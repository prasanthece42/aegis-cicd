#!/usr/bin/env bash
# Sourced by workstation-only scripts. All Kubernetes commands use explicit context flags.
app_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
gitops_root="${AEGIS_GITOPS_DIR:-$app_root/../aegis-gitops}"
local_kubeconfig="$app_root/.local/kubeconfig"
cluster_name=aegis-dev
namespace=aegis-dev
node_name=aegis-dev-control-plane
export KIND_EXPERIMENTAL_PROVIDER=docker
kube=(kubectl --kubeconfig "$local_kubeconfig" --context kind-aegis-dev)
helm_local=(helm --kubeconfig "$local_kubeconfig" --kube-context kind-aegis-dev)

assert_local_cluster() {
  local server cluster_label
  server=$("${kube[@]}" config view --minify --output 'jsonpath={.clusters[0].cluster.server}')
  [[ "$server" == https://127.0.0.1:* ]] || { printf 'Refusing non-loopback Kubernetes API\n' >&2; return 1; }
  cluster_label=$(docker inspect --format '{{index .Config.Labels "io.x-k8s.kind.cluster"}}' "$node_name")
  [[ "$cluster_label" == "$cluster_name" ]] || { printf 'Kind node identity mismatch\n' >&2; return 1; }
}
