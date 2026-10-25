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
| GitHub Release / GHCR | PASS | [Run 40246584982](https://github.com/prasanthece42/aegis-cicd/actions/runs/40246584982), source commit 9927c761640fa29af3f0190717052f1983ac83eb |
| Registry digest pull / HTTP | PASS | Pulled image matches candidate and responds correctly on Linux amd64 |
| Retained release evidence | PASS | Downloaded reports, verified checksums and CycloneDX SBOM |

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

## Verified GitHub release

The user approved publication to `ghcr.io/prasanthece42/aegis-cicd`. Source commit
`9927c761640fa29af3f0190717052f1983ac83eb` was pushed, and [Release 40246584982](https://github.com/prasanthece42/aegis-cicd/actions/runs/40246584982)
completed successfully on October 25, 2026 at 20:53 America/Halifax.

| Job | Result | Duration |
| --- | --- | --- |
| Lint, tests, dependency scan | PASS | 41 seconds |
| Build, smoke-test, image scan | PASS | 51 seconds |
| Publish and verify digest | PASS | 30 seconds |

Verified image reference:

```text
ghcr.io/prasanthece42/aegis-cicd@sha256:7444f4a7ff7dd99f094543251fe80a16ec1603c346286c0252e0d7b81ac7f421
```

Platform: `linux/amd64`. Unique tag:
`ghcr.io/prasanthece42/aegis-cicd:sha-9927c761640fa29af3f0190717052f1983ac83eb-40246584982-1`.

GitHub reports contain the same observed severity totals as the local table above,
including zero CRITICAL findings. The runner verified source and scan identity,
authenticated with GITHUB_TOKEN, pushed, pulled by digest, checked the image identity,
and ran the HTTP/UID smoke test. The workflow retained its SBOM and release.json.

A durable copy of the small release receipt is committed at
[releases/40246584982.json](releases/40246584982.json). Full reports remain in the
Actions artifacts; their SHA256 hashes are recorded in the receipt and were checked
independently after download. These are unsigned records, not signed attestations.

Additional commands executed:

```bash
git push origin main
gh run watch 40246584982 --repo prasanthece42/aegis-cicd --exit-status --interval 15
gh run download 40246584982 --repo prasanthece42/aegis-cicd --name dependency-report-40246584982-1 --dir /tmp/aegis-phase2-40246584982
gh run download 40246584982 --repo prasanthece42/aegis-cicd --name image-reports-40246584982-1 --dir /tmp/aegis-phase2-40246584982
gh run download 40246584982 --repo prasanthece42/aegis-cicd --name release-evidence-40246584982-1 --dir /tmp/aegis-phase2-release-40246584982
```

The final evidence-only documentation commit uses `[skip ci]` to record this completed
run without publishing another copy solely for a documentation update. The source
commit tested and published is explicitly recorded above.

No execution blocker remains. Lower-severity findings, unsigned provenance, artifact
retention limits, and unconfigured branch protection are documented limitations.
A separate PR-triggered run and an intentionally failing remote scan were not run;
permission isolation and failure propagation were reviewed in workflow code, with
the vulnerable-fixture gate tested locally. Next recommended phase is Kind and Helm,
after explicit user approval. No Phase 3 work has started.
