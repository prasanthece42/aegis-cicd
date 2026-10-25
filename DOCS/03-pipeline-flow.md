# Pipeline flow

A pull request, push to main, or manual dispatch starts `.github/workflows/ci.yml`.

1. **Lint and tests:** checkout without persisted credentials; install Python 3.12;
   restore the pip download cache keyed by requirements.txt; install the hashed lock;
   run Ruff lint, Ruff formatting verification, then Pytest.
2. **Container:** `needs: checks` means any failed quality gate skips this job.
   Build from the Dockerfile using `aegis-sample:<github.sha>` and run the smoke script.
3. **Smoke check:** start a disposable container with a read-only filesystem, no Linux
   capabilities, and no privilege escalation; poll Docker's health status, verify
   UID 10001, and call the dynamically allocated loopback host port. Always clean up.

Jobs have timeouts. Concurrency cancels superseded CI runs on the same branch/ref;
this is CI cancellation, not a release locking strategy. No registry push exists yet.
For pull requests, github.sha is GitHub's merge-test commit. On main it is the pushed commit.

## Security boundaries

The GITHUB_TOKEN has only contents:read. Actions are pinned to verified commit SHAs.
There is no pull_request_target trigger, secret access, deployment credential, or
self-hosted runner. Untrusted PR code runs only on GitHub-hosted runners. Cross-repo
authentication is deferred; later use short-lived GitHub App installation tokens.

Hashed package pins verify downloaded artifacts, not absence of vulnerabilities.
The base image uses an explicit Python version tag; tags can move. Base image digest
pinning, Trivy gates, GHCR publishing, provenance, and digest verification are Phase 2
work. Do not treat this Phase 1 result as a security-scanned production release.

## Failure behavior

A nonzero exit stops the step and fails the job. No image is built after a failed
check job. A failed Docker build or unhealthy container fails the container job.
Logs from the disposable container are printed before removal, including on failure.
Fix the underlying issue and push again. There is no deployment to roll back in Phase 1.
