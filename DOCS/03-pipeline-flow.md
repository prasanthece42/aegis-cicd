# Pipeline flow

Phase 2 extends the original Phase 1 quality gate. Pull requests and manual CI runs
execute ci.yml; pushes to main execute release.yml, which invokes ci.yml through
workflow_call with candidate export enabled. Manual Release runs are main-only.

1. Check out code without persisted credentials, install Python 3.12, restore pip
   download caching, and install the hash-verified development lock.
2. Run Ruff lint/format and Pytest; install pinned Trivy and scan locked dependencies.
3. Only after checks pass, build the candidate with source/revision/run labels,
   smoke-test it, export it, scan its actual archive, and generate an SBOM.
4. Retain scan reports even on failure. Export the candidate only after success
   and only for a trusted main caller.
5. Release's publish job downloads this run's candidate and reports, validates
   image/source/scan identity, logs into GHCR using GITHUB_TOKEN, and pushes the image.
6. Resolve a registry digest, pull by digest, compare image identity, and smoke-test.
   Write release.json only after verification succeeds.

Every shell gate fails on error; jobs have timeouts. Failed checks block the container
job; failed validation blocks publication. An image already pushed before a failed
pull/smoke test remains uniquely tagged but is not a verified release.

Release runs serialize through release-main with cancellation disabled. Unique
commit/run/attempt tags avoid overwrite even on reruns. No latest tag is published.
For PR checks, github.sha is GitHub's merge-test commit; main releases use the actual
pushed commit. Actions are SHA-pinned and only publish has packages:write.

See [security policy](10-security-policy.md) and [release guide](11-release-guide.md)
for thresholds, artifact retention, authentication, and failure recovery.
