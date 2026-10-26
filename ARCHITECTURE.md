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

## Current implementation — Phase 3 local deployment

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
keeps operations on the named local Kind cluster. Helm currently applies from the
workstation; no CI job deploys resources and Argo CD has not been installed.

## Target architecture — Phase 4 and later, not implemented

```mermaid
flowchart LR
    Source[Application repository] --> CI[Checks and security scans]
    CI --> Registry[GHCR image by digest]
    Registry --> Update[GitOps change through GitHub App]
    Update --> GitOps[Separate GitOps repository]
    GitOps --> Argo[Argo CD reconciliation]
    Argo --> K8s[Helm on Kind: DEV / STAGING / PROD]
```

Use two repositories: `aegis-cicd` for application source and workflows, and
`aegis-gitops` for charts, environment values, and Argo CD Applications. The second repository is now implemented as a sibling checkout. CI must never directly deploy application
resources with kubectl. Argo CD will own reconciliation. Phase 2 publishes unique commit/run tags and records digest references.
Later deployment configuration must consume those digests.

DEV will sync automatically; production desired-state changes will require reviewed
GitOps pull requests and protected branches. Reverting a GitOps commit will request
rollback through Argo CD. Git history links configuration changes to image digests.
Cross-repository updates should use a narrowly installed GitHub App with short-lived
tokens, not a long-lived personal access token.
