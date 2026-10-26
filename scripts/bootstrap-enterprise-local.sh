#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/kind-common.sh"
cd "$app_root"
assert_local_cluster
# All sources are now public HTTPS; no account/registry token is given to Argo.
"${kube[@]}" apply --filename "$gitops_root/argocd/projects"
"${kube[@]}" apply --filename "$gitops_root/argocd/applications"
printf 'Argo definitions applied: DEV automated; STAGING and PROD await approved manual sync\n'
