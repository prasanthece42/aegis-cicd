#!/usr/bin/env bash
# Live demonstration: commits/pushes a local-profile replica change, tests drift, then reverts it.
set -euo pipefail
source "$(dirname "$0")/kind-common.sh"
cd "$app_root"
assert_local_cluster
[[ -z "$(git -C "$gitops_root" status --porcelain)" ]] || { printf 'GitOps worktree must be clean\n' >&2; exit 1; }
[[ "$(git -C "$gitops_root" branch --show-current)" == main ]] || { printf 'GitOps checkout must be on main\n' >&2; exit 1; }
initial_revision=$(git -C "$gitops_root" rev-parse HEAD)
bash scripts/verify-local-argocd.sh "$initial_revision" 1
cp reports/argocd-verification.json reports/argocd-before.json
python3 - "$gitops_root/environments/local/values.yaml" <<'PYTHON'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()
if text.count('replicaCount: 1\n') != 1:
    raise ValueError('Expected the one-replica local baseline')
path.write_text(text.replace('replicaCount: 1\n', 'replicaCount: 2\n'))
PYTHON
git -C "$gitops_root" add environments/local/values.yaml
git -C "$gitops_root" commit -m 'Demonstrate Git-driven local DEV scaling to two replicas'
change_revision=$(git -C "$gitops_root" rev-parse HEAD)
git -C "$gitops_root" push origin main
# No manual Argo sync or refresh: poll until its normal Git polling drives the update.
bash scripts/verify-local-argocd.sh "$change_revision" 2
cp reports/argocd-verification.json reports/argocd-after-git.json
"${kube[@]}" --namespace "$namespace" scale deployment/sample-api --replicas=3
"${kube[@]}" --namespace "$namespace" get deployment sample-api --output json > reports/argocd-drift-injected.json
bash scripts/verify-local-argocd.sh "$change_revision" 2
cp reports/argocd-verification.json reports/argocd-after-self-heal.json
git -C "$gitops_root" revert --no-edit "$change_revision"
revert_revision=$(git -C "$gitops_root" rev-parse HEAD)
git -C "$gitops_root" push origin main
bash scripts/verify-local-argocd.sh "$revert_revision" 1
cp reports/argocd-verification.json reports/argocd-after-revert.json
python3 - <<'PYTHON'
import json
from pathlib import Path

reports = Path('reports')
states = {
    label: json.loads((reports / filename).read_text())
    for label, filename in {
        'initial': 'argocd-before.json',
        'git_change': 'argocd-after-git.json',
        'self_heal': 'argocd-after-self-heal.json',
        'git_revert': 'argocd-after-revert.json',
    }.items()
}
injected = json.loads((reports / 'argocd-drift-injected.json').read_text())
if injected['spec']['replicas'] != 3:
    raise ValueError('Did not capture the injected live drift')
if states['git_change']['git_revision'] != states['self_heal']['git_revision']:
    raise ValueError('Self-healing must occur without a Git change')
states['injected_live_replicas'] = injected['spec']['replicas']
(reports / 'gitops-flow.json').write_text(json.dumps(states, indent=2) + '\n')
print('PASS: Git scaling 1 -> 2; self-heal live 3 -> Git 2; Git revert -> 1')
PYTHON
