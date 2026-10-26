#!/usr/bin/env bash
set -euo pipefail
umask 077
source "$(dirname "$0")/kind-common.sh"
cd "$app_root"
for tool in docker kind kubectl helm kubeconform trivy python3 rg curl; do
  command -v "$tool" >/dev/null || { printf 'Missing required tool: %s\n' "$tool" >&2; exit 1; }
done
[[ -f "$gitops_root/charts/sample-api/Chart.yaml" ]] || { printf 'Missing sibling aegis-gitops checkout\n' >&2; exit 1; }
# Verify local inputs before spending resources on a cluster.
bash scripts/verify-local.sh
bash "$gitops_root/scripts/validate-chart.sh"
git diff --exit-code -- app Dockerfile requirements-prod.txt >/dev/null || {
  printf 'Commit image source changes before building a traceable local candidate\n' >&2; exit 1;
}
mkdir -p .local candidate reports
source_sha=$(git rev-parse HEAD)
local_tag="aegis-sample:local-${source_sha:0:12}-$(date -u +%Y%m%d%H%M%S)"
docker build --provenance=false --tag "$local_tag" \
  --label "org.opencontainers.image.source=https://github.com/prasanthece42/aegis-cicd" \
  --label "org.opencontainers.image.revision=$source_sha" .
docker save --output candidate/image.tar "$local_tag"
bash scripts/scan-security.sh image candidate/image.tar
if kind get clusters | rg -qx "$cluster_name"; then
  kind export kubeconfig --name "$cluster_name" --kubeconfig "$local_kubeconfig"
else
  kind create cluster --config kind/cluster.yaml --kubeconfig "$local_kubeconfig" --wait 180s
fi
assert_local_cluster
"${kube[@]}" wait --for=condition=Ready nodes --all --timeout=180s
kind load image-archive "$app_root/candidate/image.tar" --name "$cluster_name"
qualified_tag="docker.io/library/$local_tag"
image_digest=$(docker exec "$node_name" ctr --namespace k8s.io images list \
  | awk -v image="$qualified_tag" '$1 == image { print $3 }')
[[ "$image_digest" =~ ^sha256:[0-9a-f]{64}$ ]] || { printf 'Cannot resolve loaded image manifest digest\n' >&2; exit 1; }
# Register the actual containerd manifest digest, never a source SHA/config digest alias.
local_reference="docker.io/library/aegis-sample@$image_digest"
docker exec "$node_name" ctr --namespace k8s.io images tag --force "$qualified_tag" "$local_reference"
python3 - "$source_sha" "$image_digest" "$local_reference" <<'PYTHON'
import json
import sys
from pathlib import Path

sha, digest, reference = sys.argv[1:]
Path('.local/kind-values.yaml').write_text(
    'image:\n  repository: docker.io/library/aegis-sample\n'
    f'  digest: {digest}\n  pullPolicy: Never\nsourceCommit: "{sha}"\n'
)
Path('reports/local-image-reference.json').write_text(json.dumps({
    'source_commit': sha, 'image': reference,
    'profile': 'Native local build; not the published GHCR amd64 release',
}, indent=2) + '\n')
PYTHON
"${kube[@]}" apply --filename "$gitops_root/environments/dev/namespace.yaml"
helm template sample-api "$gitops_root/charts/sample-api" --namespace "$namespace" \
  --values "$gitops_root/environments/dev/values.yaml" --values .local/kind-values.yaml \
  > reports/local-rendered.yaml
"${kube[@]}" apply --dry-run=server --filename reports/local-rendered.yaml
"${helm_local[@]}" upgrade --install sample-api "$gitops_root/charts/sample-api" \
  --namespace "$namespace" --values "$gitops_root/environments/dev/values.yaml" \
  --values .local/kind-values.yaml --wait --rollback-on-failure --timeout 180s
bash scripts/verify-local-k8s.sh
