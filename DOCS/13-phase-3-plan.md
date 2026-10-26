# Phase 3 — Kubernetes and Helm implementation plan

Scope: a real local Kind DEV deployment and a separate GitOps chart repository.
No Argo CD, automatic GitOps updates, promotion, or AWS provisioning in this phase.

## Architecture decisions

- Keep application source in aegis-cicd and charts/desired state in sibling aegis-gitops.
- Kind cluster aegis-dev uses pinned Kind v0.33.0 and Kubernetes v1.35.8 node digest.
- Use .local/kubeconfig and explicit kind-aegis-dev context flags. Never use or alter
  the existing AWS context. Do not set KUBECONFIG to the colon-containing workspace path.
- Chart defaults and tracked environment values reference the verified Phase 2 GHCR
  digest. For native arm64 local execution, build and scan the same application on
  this host, load it into Kind, and generate a gitignored local digest override.
  This local digest is distinct from the published amd64 release; no GHCR pull is claimed.
- Helm installs DEV manually from the workstation for this phase. CI only validates
  templates. Argo CD becomes the application reconciler when Phase 4 is approved.

## Implementation sequence

1. Inspect local tools, Docker, cluster contexts, and source/GitOps boundaries.
2. Write the Helm chart, restrictive schema, and per-environment namespaces/values.
3. Lint and render all environments; validate Kubernetes schemas and negative inputs.
4. Build/scan a native image and create the isolated Kind cluster.
5. Load the image and deploy DEV with a generated digest reference using Helm.
6. Verify rollout, replicas, probes, UID, Service HTTP access, and recovery after pod deletion.
7. Document commands, checks, architecture, learning notes, and any registry/remote blockers.

Acceptance evidence will be recorded in DOCS/15-phase-3-report.md. Stop after Phase 3.
