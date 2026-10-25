# Phase 2 verification report

Date: October 25, 2026 (America/Halifax).

## Implementation

Added release.yml, scan-security.sh, release_evidence.py, nine image/source/digest
verification tests, and numbered Phase 2 guides. Updated CI to support PR checks and
trusted workflow_call validation. Updated action SHAs to current releases, including
Node.js 24-native actions. The Docker base now pins Python 3.12.14-slim-trixie by digest.

The publishing job receives the validated archive without rebuilding, uses the
short-lived GITHUB_TOKEN, publishes a unique commit/run/attempt tag, resolves the
GHCR digest, pulls it, checks image identity, and runs the HTTP smoke test. Reports,
SBOM, and unsigned release metadata are retained as Actions artifacts.

## Local results

| Check | Result | Evidence |
| --- | --- | --- |
| Ruff lint / formatting | PASS | verify-local.sh |
| Pytest | PASS | 12 passed; existing Starlette/anyio warning remains visible |
| Workflow validation | PASS | actionlint v1.7.12; ShellCheck unavailable |
| Bash syntax | PASS | bash -n scripts/*.sh |
| Dependency gate | PASS | 23 packages; zero CRITICAL; 3 HIGH, 2 MEDIUM, 1 LOW |
| Initial Bookworm image | FAIL (remediated) | 5 CRITICAL findings blocked the old base |
| Trixie image gate | PASS | 103 inventory entries; zero CRITICAL; 51 HIGH, 100 MEDIUM, 70 LOW, 4 UNKNOWN |
| Trixie container HTTP / UID | PASS | Real arm64 container healthy and UID 10001 |
| Scan/config identity | PASS | Compared Trivy metadata with config digest computed from actual archive |
| Vulnerable fixture | PASS | Django 2.2.0 metadata detected 6 CRITICAL findings; gate returned 1; package never installed |
| GitHub Release / GHCR | NOT RUN | Automatic approval review blocked the push pending explicit approval for ghcr.io/prasanthece42/aegis-cicd |

Noncritical findings are visible and permitted by the explicit Phase 2 policy; this
is not a production security approval. Counts reflect this scan/database and platform.

## Commands executed

```bash
bash scripts/verify-local.sh
/tmp/aegis-actionlint -shellcheck= .github/workflows/ci.yml .github/workflows/release.yml
bash -n scripts/*.sh
# Trivy v0.76.1 downloaded from official release and checksum-verified locally:
PATH="/tmp/aegis-phase2-bin:$PATH" TRIVY_CACHE_DIR=/tmp/aegis-trivy-cache bash scripts/scan-security.sh dependencies
docker build --tag aegis-sample:phase2-local .
docker save --output candidate/image.tar aegis-sample:phase2-local
PATH="/tmp/aegis-phase2-bin:$PATH" TRIVY_CACHE_DIR=/tmp/aegis-trivy-cache bash scripts/scan-security.sh image candidate/image.tar
bash scripts/verify-container.sh aegis-sample:phase2-local
```

A temporary requirements.txt containing django==2.2.0 was scanned outside the
repository; `trivy convert --severity CRITICAL --exit-code 1` rejected its JSON report.
The application lock files were never modified for the negative test. An initial
identity check exposed manifest/config ID differences on Docker Desktop; verification
now hashes the archive's config blob and tests that distinction explicitly.

## Scope and remaining work

No GitOps update, Kind, Helm, Argo CD, deployment, or AWS provisioning was added.
Private managed artifact attestations are not enabled; evidence is explicitly unsigned.
Local account package listing returned HTTP 403 because its OAuth token lacks
read:packages; the pipeline uses GITHUB_TOKEN instead and does not broaden that token.
Phase 3 requires a separate user instruction after Phase 2 results are reviewed.

## Publication blocker

Automatic approval review rejected the push because it would trigger publication
to GHCR, a separate external destination not explicitly approved by the user.
Phase 2 changes are committed locally only. No Phase 2 workflow or GHCR publication
has executed. To complete this phase, approve pushing these changes to the existing
private GitHub repository and publishing the validated image to
`ghcr.io/prasanthece42/aegis-cicd` using the workflow token.
