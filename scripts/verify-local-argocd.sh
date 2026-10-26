#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/kind-common.sh"
cd "$app_root"
assert_local_cluster
mkdir -p reports
python3 - "$local_kubeconfig" "${1:-}" "${2:-}" <<'PYTHON'
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

config, expected_revision, expected_replicas = sys.argv[1:]
kube = ['kubectl', '--kubeconfig', config, '--context', 'kind-aegis-dev']
deadline = time.monotonic() + 300
previous = None
while time.monotonic() < deadline:
    app = json.loads(subprocess.check_output(kube + [
        '-n', 'argocd', 'get', 'application', 'sample-api-local', '-o', 'json',
    ], text=True))
    deployment = json.loads(subprocess.check_output(kube + [
        '-n', 'aegis-dev', 'get', 'deployment', 'sample-api', '-o', 'json',
    ], text=True))
    status = app.get('status', {})
    sync = status.get('sync', {})
    health = status.get('health', {}).get('status')
    replicas = deployment['spec']['replicas']
    state = (sync.get('status'), health, sync.get('revision'), replicas)
    if state != previous:
        print('Argo status:', state, flush=True)
        previous = state
    observed = deployment.get('status', {})
    revision_ok = not expected_revision or sync.get('revision') == expected_revision
    replicas_ok = not expected_replicas or replicas == int(expected_replicas)
    healthy = observed.get('availableReplicas', 0) == replicas
    healthy &= observed.get('observedGeneration', 0) >= deployment['metadata']['generation']
    errors = [c for c in status.get('conditions', []) if c['type'].endswith('Error')]
    if sync.get('status') == 'Synced' and health == 'Healthy' and revision_ok and replicas_ok and healthy and not errors:
        if app['spec']['source']['repoURL'] != 'git@github.com:prasanthece42/aegis-gitops.git':
            raise ValueError('Unexpected Argo source repository')
        record = {
            'verified_at': datetime.now(UTC).isoformat(),
            'application': app['metadata']['name'], 'sync': sync['status'], 'health': health,
            'git_revision': sync['revision'], 'replicas': replicas,
            'image': deployment['spec']['template']['spec']['containers'][0]['image'],
        }
        Path('reports/argocd-verification.json').write_text(json.dumps(record, indent=2) + '\n')
        print('PASS: Argo CD Synced/Healthy at expected revision and replica count', flush=True)
        break
    time.sleep(5)
else:
    print('Argo conditions:', status.get('conditions', []), file=sys.stderr)
    raise SystemExit('FAIL: Argo reconciliation timed out')
PYTHON
bash scripts/verify-local-k8s.sh
