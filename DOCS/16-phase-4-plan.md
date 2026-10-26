# Phase 4 — Argo CD implementation plan

Scope: install pinned Argo CD on local Kind, connect the private GitOps repository,
and demonstrate automatic Git-driven deployment and self-healing in DEV.
No AWS provisioning, promotion pipelines, production deployment, or automated
cross-repository image updates are part of this phase.

## Architecture

GitOps main -> Argo CD repository server -> Helm rendering -> application controller
-> restricted DEV namespace. GitHub Actions validates templates; it never deploys.

Use the existing native image digest through a tracked environments/local profile.
Tracked dev/staging/prod registry values remain separate. Use a read-only SSH deploy
key for only prasanthece42/aegis-gitops; private key lives in ignored .local and an
Argo repository Secret. The read-only deploy key is a persistent local-development
credential and must be revoked when the local integration is retired. No account PAT
or GitHub OAuth token is copied into the cluster. A GitHub App is a later option for
short-lived repository credentials.

Argo's project restricts source repository, local cluster, target namespace, and
resource kinds. Use annotation tracking to preserve Helm's instance labels. After
handoff, the manual Helm bootstrap must refuse to mutate the Argo-owned application.

## Sequence and acceptance checklist

- [x] Validate declarative project/Application and the local-profile Helm render.
- [x] Install checksum-pinned Argo CD with the isolated kubeconfig/context.
- [x] Register the scoped read-only repository credential securely.
- [x] Application reports Synced and Healthy from the private Git repository.
- [x] Commit a replica change, push it, and observe automatic reconciliation.
- [x] Change the live replica count and observe self-healing to Git desired state.
- [x] Revert the Git change and verify the original desired state and HTTP health.
- [x] Verify Argo server loopback access and guard against manual Helm overwrite.
- [ ] Run application/chart checks on GitHub and record evidence/limitations.

Stop after Phase 4. Argo CD becoming the reconciler does not automatically connect
new CI image publication to GitOps updates; that release integration is still later work.
