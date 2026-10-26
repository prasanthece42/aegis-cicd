#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/kind-common.sh"
assert_local_cluster
printf 'Open https://127.0.0.1:%s (local Argo CD self-signed certificate)\n' "${AEGIS_ARGO_PORT:-8443}"
exec "${kube[@]}" --namespace argocd port-forward service/argocd-server \
  "${AEGIS_ARGO_PORT:-8443}:443" --address 127.0.0.1
