# Phase 5 — Enterprise release management plan

Scope: verified release selection, GitOps release proposals, environment promotion,
review controls, drift observation, and a real failed-release rollback in the local
Kind lab. AWS resources remain disabled.

## Findings and approved decisions

GitHub returned HTTP 403 for branch protection on the private GitOps repository:
this plan requires GitHub Pro or public visibility. Production stays disabled until
an enforceable approval path exists. The user explicitly approved making both repositories public. Full Git histories
passed Gitleaks v8.30.1 with redacted output and no detected leaks; local keys and
kubeconfig remain ignored. Both visibility changes were then verified through GitHub.

Current published images are amd64 only, while Kind is arm64. First extend release
validation to test and scan both platforms and publish one immutable OCI index. An
exact OCI delivery bundle can transfer private registry content into the local cache
without creating a persistent registry PAT. It must preserve registry digests.

Cross-repository automation must use short-lived workflow or GitHub App tokens.
No broad account token may be copied into repository secrets or the cluster.

## Acceptance checklist

- [ ] Both image architectures are built, tested, scanned, and published by digest.
- [ ] An OCI bundle's imported digest and actual runtime match release evidence.
- [ ] A validated release produces a GitOps proposal without a persistent PAT.
- [ ] DEV, STAGING, PROD reuse the same digest with explicit promotion sequencing.
- [ ] Production approval is enforced; missing/stale/self approvals fail closed.
- [ ] Argo policies differ by environment and production revisions are controlled.
- [ ] Drift is observed and corrected through Argo reconciliation.
- [ ] A real failed local release is diagnosed and restored by a Git change.
- [ ] Local/GitHub results and unfulfilled external prerequisites are recorded accurately.

No visibility change, paid upgrade, or production activation is inferred from elapsed
time or a missing answer. Continue independent implementation and validation first.

Use protected main/DEV, staging, and prod branches in aegis-gitops. Production
requires a fresh human review, including administrators. A GitOps-owned workflow
reads public application release receipts and opens its own PR using GITHUB_TOKEN.
It explicitly dispatches validation because bot-token PR creation does not trigger
normal PR workflows. Promotion requires prior environment health recorded by an
allowlisted workstation operator at the exact Git revision/digest. Argo never receives
a GitHub write token; local observation uses the workstation's existing authentication.
