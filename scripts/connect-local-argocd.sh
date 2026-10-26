#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/kind-common.sh"
cd "$app_root"
assert_local_cluster
[[ -f .local/argocd-deploy-key.json ]] || { printf 'Register the read-only deploy key first\n' >&2; exit 1; }
"${kube[@]}" --namespace argocd create secret generic aegis-gitops-repository \
  --from-literal=type=git \
  --from-literal=url=git@github.com:prasanthece42/aegis-gitops.git \
  --from-literal=project=aegis-local \
  --from-file=sshPrivateKey=.local/argocd-gitops-readonly \
  --dry-run=client --output json \
  | "${kube[@]}" label --local --filename - argocd.argoproj.io/secret-type=repository --output yaml \
  | "${kube[@]}" apply --server-side --field-manager=aegis-repository --filename -
# Upstream's pinned known-hosts ConfigMap verifies GitHub SSH host keys; no insecure bypass.
"${kube[@]}" apply --filename "$gitops_root/argocd/projects/aegis-local.yaml"
"${kube[@]}" apply --filename "$gitops_root/argocd/applications/sample-api-local.yaml"
bash scripts/verify-local-argocd.sh
