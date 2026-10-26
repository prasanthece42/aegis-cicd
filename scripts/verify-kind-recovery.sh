#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/kind-common.sh"
cd "$app_root"
assert_local_cluster
mkdir -p reports
"${kube[@]}" --namespace "$namespace" get pods --selector app.kubernetes.io/instance=sample-api \
  --output json > reports/pod-recovery-before.json
pod=$(python3 -c 'import json; d=json.load(open("reports/pod-recovery-before.json")); assert len(d["items"]) == 1; print(d["items"][0]["metadata"]["name"])')
"${kube[@]}" --namespace "$namespace" delete pod "$pod" --wait=true --timeout=90s
"${kube[@]}" --namespace "$namespace" wait --for=condition=Ready pod \
  --selector app.kubernetes.io/instance=sample-api --timeout=180s
bash scripts/verify-local-k8s.sh
"${kube[@]}" --namespace "$namespace" get pods --selector app.kubernetes.io/instance=sample-api \
  --output json > reports/pod-recovery-after.json
python3 - <<'PYTHON'
import json
from pathlib import Path

before = json.loads(Path('reports/pod-recovery-before.json').read_text())['items'][0]
after = json.loads(Path('reports/pod-recovery-after.json').read_text())['items'][0]
assert before['metadata']['uid'] != after['metadata']['uid'], 'Pod was not replaced'
assert before['spec']['containers'][0]['image'] == after['spec']['containers'][0]['image']
Path('reports/pod-recovery.json').write_text(json.dumps({
    'result': 'passed', 'before': before['metadata']['name'],
    'after': after['metadata']['name'], 'same_image': True,
}, indent=2) + '\n')
print('PASS: ReplicaSet replaced the deleted pod with the same image and healthy HTTP')
PYTHON
