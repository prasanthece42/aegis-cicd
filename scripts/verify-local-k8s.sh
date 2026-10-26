#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/kind-common.sh"
cd "$app_root"
assert_local_cluster
mkdir -p reports
"${kube[@]}" --namespace "$namespace" rollout status deployment/sample-api --timeout=180s
"${kube[@]}" --namespace "$namespace" get deployment sample-api --output json > reports/k8s-deployment.json
"${kube[@]}" --namespace "$namespace" get pods --selector app.kubernetes.io/instance=sample-api --output json > reports/k8s-pods.json
"${kube[@]}" --namespace "$namespace" exec deployment/sample-api -- id -u | python3 -c 'import sys; assert sys.stdin.read().strip() == "10001"'
python3 - <<'PYTHON'
import json
from pathlib import Path

deployment = json.loads(Path('reports/k8s-deployment.json').read_text())
expected = json.loads(Path('reports/local-image-reference.json').read_text())
pod_spec = deployment['spec']['template']['spec']
container = pod_spec['containers'][0]
assert container['image'] == expected['image'], 'Deployment image digest differs'
assert deployment['status'].get('availableReplicas') == deployment['spec']['replicas']
assert pod_spec['securityContext']['runAsNonRoot'] is True
assert pod_spec['automountServiceAccountToken'] is False
assert container['securityContext']['readOnlyRootFilesystem'] is True
assert container['securityContext']['allowPrivilegeEscalation'] is False
assert container['securityContext']['capabilities']['drop'] == ['ALL']
assert container['resources']['requests'] and container['resources']['limits']
for probe in ['startupProbe', 'readinessProbe', 'livenessProbe']:
    assert container[probe]['httpGet']['path'] == '/health'
print('PASS: live deployment digest, replicas, security, resources, and probes')
PYTHON
port="${AEGIS_LOCAL_PORT:-18080}"
forward_log=$(mktemp)
forward_pid=""
cleanup() {
  if [[ -n "$forward_pid" ]]; then
    kill "$forward_pid" 2>/dev/null || true
    wait "$forward_pid" 2>/dev/null || true
  fi
  rm -f "$forward_log"
}
trap cleanup EXIT
"${kube[@]}" --namespace "$namespace" port-forward service/sample-api "$port:80" \
  --address 127.0.0.1 > "$forward_log" 2>&1 &
forward_pid=$!
for ((attempt=1; attempt<=30; attempt++)); do
  if ! kill -0 "$forward_pid" 2>/dev/null; then
    cat "$forward_log" >&2
    exit 1
  fi
  if rg -q 'Forwarding from' "$forward_log"; then
    if curl --fail --silent --show-error "http://127.0.0.1:$port/health" \
      | python3 -c 'import json,sys; assert json.load(sys.stdin) == {"status": "ok"}'; then
      printf 'PASS: Kubernetes Service /health reachable on 127.0.0.1:%s\n' "$port"
      exit 0
    fi
  fi
  sleep 1
done
cat "$forward_log" >&2
printf 'FAIL: Kubernetes Service HTTP check timed out\n' >&2
exit 1
