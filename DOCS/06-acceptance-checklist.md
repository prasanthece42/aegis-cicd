# Phase 1 acceptance checklist

Verified on October 25, 2026. See the report for commands and limitations.

- [x] New application repository isolated from existing workspace projects.
- [x] Implementation plan and architecture documented before validation.
- [x] Python 3.12 application starts through a real Uvicorn server.
- [x] GET /health returns HTTP 200 and exact JSON {"status":"ok"}.
- [x] Three Pytest HTTP contract tests pass.
- [x] Ruff lint and formatting checks pass.
- [x] Fully pinned dependency locks install with hash verification.
- [x] Multi-stage Docker image builds on local linux/arm64.
- [x] Real container becomes healthy and responds over published HTTP.
- [x] Runtime UID 10001 verified with read-only filesystem and capabilities dropped.
- [x] GitHub Actions workflow accepted by actionlint v1.7.12.
- [x] CI builds only after lint and tests; SHA-pinned actions and read-only token.
- [x] Local instructions, failure behavior, file guide, and learning notes available.
- [ ] GitHub-hosted CI execution — NOT RUN: no remote configured or code pushed.

Phase 1 local implementation is complete. GitHub execution remains an external
verification step. Phase 2 is not implemented and requires explicit approval.
