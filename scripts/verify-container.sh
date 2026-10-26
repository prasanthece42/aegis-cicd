#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
image="${1:?Usage: bash scripts/verify-container.sh IMAGE}"
container=""
cleanup() {
  if [[ -n "$container" ]]; then
    docker logs "$container" || true
    docker rm -f "$container" >/dev/null || true
  fi
}
trap cleanup EXIT
container=$(docker run -d --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m \
  --cap-drop ALL --security-opt no-new-privileges \
  --publish 127.0.0.1::8000 "$image")
for ((attempt=1; attempt<=30; attempt++)); do
  health=$(docker inspect --format '{{.State.Health.Status}}' "$container")
  if [[ "$health" == healthy ]]; then
    [[ "$(docker exec "$container" id -u)" == 10001 ]]
    address=$(docker port "$container" 8000/tcp)
    curl --fail --silent --show-error "http://$address/health" \
      | python3 -c 'import json,sys; assert json.load(sys.stdin) == {"status": "ok"}'
    python3 - "$address" <<'PYTHON'
import json
import sys
from urllib.request import urlopen

base = "http://" + sys.argv[1]
for path, content_types in [
    ("/", {"text/html"}),
    ("/assets/app.css", {"text/css"}),
    ("/assets/app.js", {"text/javascript", "application/javascript"}),
]:
    with urlopen(base + path, timeout=5) as response:
        assert response.status == 200, path
        assert response.headers.get_content_type() in content_types, path
        assert response.read(), path
with urlopen(base + "/version", timeout=5) as response:
    version = json.load(response)
    assert isinstance(version.get("version"), str) and version["version"]
print("PASS: UI, browser assets, and version endpoint shipped in the actual container")
PYTHON
    printf 'PASS: container healthy, UID 10001, host HTTP contracts verified\n'
    exit 0
  fi
  if [[ "$health" == unhealthy ]]; then break; fi
  sleep 2
done
printf 'FAIL: container did not become healthy\n' >&2
exit 1
