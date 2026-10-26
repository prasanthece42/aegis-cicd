# Aegis CI/CD architecture

## Phase 1 foundation

```mermaid
flowchart TB
    Developer[Developer] --> Repo[Application Git repository]
    Repo --> Checks[GitHub Actions: Ruff and Pytest]
    Checks --> Image[Build commit-tagged Docker image]
    Image --> Smoke[Run image and verify health over HTTP]
    Local[Local Python 3.12] --> API[FastAPI GET /health]
    Smoke --> API
```

The API returns HTTP 200 and `{"status":"ok"}`. It has no database or external
services; the health check confirms process responsiveness. A future dependency
readiness check should be distinct from liveness so an outage does not cause restart loops.

Lint and tests run before container work. The image contains runtime dependencies
and application code; tests and developer tools stay outside it. A two-stage build
copies a virtual environment into a slim runtime running as UID/GID 10001.

## Phase 2 release pipeline

```mermaid
flowchart LR
    Main[Main push] --> CI[Lint, tests, dependency gate]
    CI --> Candidate[Build, smoke-test, image gate]
    Candidate --> Artifact[Run-scoped candidate archive]
    Artifact --> GHCR[Unique SHA tag in GHCR]
    GHCR --> Verify[Pull by digest and smoke-test]
    Verify --> Evidence[Reports, SBOM, release.json]
```

PRs run CI without publication. Main runs Release, which calls CI and publishes
only after success. Only the publication job receives packages:write. It uses
GITHUB_TOKEN; no registry PAT is stored. The Docker base is digest-pinned Trixie.
The full policy and retained unsigned evidence are documented in DOCS/10 and DOCS/11.

## Phase 3 local bootstrap

```mermaid
flowchart LR
    App[Committed app inputs] --> Scan[Native Docker build and Trivy gate]
    Scan --> Kind[Load image into Kind]
    GitOps[Separate aegis-gitops chart and DEV values] --> Helm[Workstation Helm install]
    Kind --> Deployment[Restricted DEV namespace and Deployment]
    Helm --> Deployment
    Deployment --> Service[ClusterIP Service and verified /health]
```

Only DEV is installed. STAGING/PROD are schema-validated desired-state examples.
The local arm64 image has its own actual manifest digest; tracked environment values
reference the published Phase 2 amd64 GHCR digest. An isolated kubeconfig/context
keeps operations on the named local Kind cluster. This Phase 3 bootstrap applied Helm from the workstation. Phase 4 below
replaces ongoing manual deployment with Argo CD; CI never deploys application resources.

## Historical Phase 4 reconciliation

```mermaid
flowchart LR
    Git[Private aegis-gitops main] --> Repo[Argo repository server renders Helm]
    Repo --> Controller[Application controller]
    Controller --> DEV[Kind aegis-dev workload]
    DEV --> Drift[Compare with Git; self-heal live drift]
    Drift --> Controller
```

Argo uses a read-only repository deploy key, a scoped local project, and an automated
Application. The chart is rendered with DEV and tracked local native-image values.
Real Git scaling, live drift repair, and Git revert were verified. Manual workstation
Helm bootstrap is guarded after handoff. The original Helm release history is historical.

## Current Phase 5 release management

```mermaid
flowchart LR
    Source[Application main] --> CI[Native amd64 + arm64 checks and scans]
    CI --> Release[GHCR OCI index and public receipt/bundle]
    Release --> Cache[Verified exact-image Kind cache]
    Cache --> PR[GitOps DEV PR using repo GITHUB_TOKEN]
    PR --> DEV[Required checks; merge; Argo automatic DEV]
    DEV --> Stage[Healthy DEV; STAGING PR and manual Argo sync]
    Stage --> Prod[Healthy STAGING; human-reviewed PROD PR and manual sync]
```

Both repositories are public following explicit approval and history credential scans.
Argo reads public HTTPS without a repository credential; the former SSH deploy key was
revoked. GHCR remains private. A workstation bridge verifies public release evidence,
imports an exact digest-preserving OCI bundle into the local Kind cache, and dispatches
the GitOps-owned proposal workflow. Background operation is pending explicit approval.

GitOps main, staging and prod are protected, including administrators. Required chart
and trusted-main promotion policy checks enforce source release validation, exact digest
reuse and fresh prior-environment health. Production requires an independent allowlisted
human approval at the current PR head. DEV reconciles automatically; STAGING/PROD
require explicit Argo sync. DEV and STAGING are verified; PROD PR #3 remains unapproved
and undeployed. All namespaces are in local Kind, with no AWS provisioning.

Health statuses are allowlisted operator observations with a 24-hour expiry, not signed
runtime attestations. Source release evidence is unsigned. CI has no cluster credentials.
See [the release guide](DOCS/20-release-management-guide.md) for code, commands and limits.
