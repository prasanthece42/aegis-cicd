#!/usr/bin/env bash
# Registers a persistent READ-ONLY SSH deploy key on exactly the named private repo.
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
mkdir -p .local
chmod 700 .local
key=.local/argocd-gitops-readonly
if [[ ! -f "$key" ]]; then
  ssh-keygen -q -t ed25519 -N '' -C aegis-kind-argocd-readonly -f "$key"
fi
chmod 600 "$key"
python3 - <<'PYTHON'
import json
import subprocess
from pathlib import Path

repo = 'prasanthece42/aegis-gitops'
public_key = Path('.local/argocd-gitops-readonly.pub').read_text().strip()
endpoint = f'repos/{repo}/keys'
keys = json.loads(subprocess.check_output(['gh', 'api', endpoint], text=True))
key = next((k for k in keys if k['key'].split()[:2] == public_key.split()[:2]), None)
if key is None:
    if any(k['title'] == 'aegis-kind-argocd-readonly' for k in keys):
        raise ValueError('A different deploy key already has this title; inspect before replacing')
    payload = json.dumps({'title': 'aegis-kind-argocd-readonly', 'key': public_key, 'read_only': True})
    key = json.loads(subprocess.check_output(
        ['gh', 'api', endpoint, '--method', 'POST', '--input', '-'], input=payload, text=True,
    ))
if not key['read_only']:
    raise ValueError('Repository key must be read-only')
Path('.local/argocd-deploy-key.json').write_text(json.dumps({
    'repository': repo, 'id': key['id'], 'read_only': key['read_only'],
}, indent=2) + '\n')
print(f"PASS: read-only deploy key {key['id']} registered for {repo}")
PYTHON
