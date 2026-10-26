#!/usr/bin/env bash
set -euo pipefail
umask 077
source "$(dirname "$0")/kind-common.sh"
cd "$app_root"
assert_local_cluster
mkdir -p .local reports
python3 - <<'PYTHON'
import hashlib
import json
import subprocess
from pathlib import Path

pin = json.loads(Path('config/argocd-version.json').read_text())
url = f"https://raw.githubusercontent.com/argoproj/argo-cd/{pin['commit']}/manifests/install.yaml"
data = subprocess.check_output(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '60', url])
if hashlib.sha256(data).hexdigest() != pin['manifest_sha256']:
    raise ValueError('Argo CD installation manifest checksum mismatch')
Path('.local/argocd-install.yaml').write_bytes(data)
print('PASS: pinned Argo CD manifest', pin['version'])
PYTHON
"${kube[@]}" create namespace argocd --dry-run=client --output yaml \
  | "${kube[@]}" apply --filename -
"${kube[@]}" --namespace argocd apply --server-side --field-manager=aegis-argocd-install \
  --filename .local/argocd-install.yaml
"${kube[@]}" wait --for=condition=Established crd/applications.argoproj.io crd/appprojects.argoproj.io --timeout=90s
"${kube[@]}" apply --server-side --field-manager=aegis-argocd-config \
  --filename "$gitops_root/argocd/config/argocd-cm.yaml"
"${kube[@]}" apply --filename "$gitops_root/argocd/projects/default-deny.yaml"
for deployment in argocd-repo-server argocd-server argocd-redis; do
  "${kube[@]}" --namespace argocd rollout status "deployment/$deployment" --timeout=300s
done
"${kube[@]}" --namespace argocd rollout status statefulset/argocd-application-controller --timeout=300s
printf 'PASS: Argo CD installed on isolated Kind; repository connection is a separate step\n'
