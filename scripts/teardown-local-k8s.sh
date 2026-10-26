#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/kind-common.sh"
assert_local_cluster
kind delete cluster --name "$cluster_name" --kubeconfig "$local_kubeconfig"
printf 'Deleted the dedicated local aegis-dev Kind cluster\n'
