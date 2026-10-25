# Phase 1 implementation plan

Scope: deliver a real sample workload and a repeatable CI gate. Stop before registry publishing.

1. Inspect the workspace and tools; isolate this new application repository.
2. Define the `/health` HTTP contract and exercise it with Pytest.
3. Configure Ruff and resolve dependencies into hashed, pinned lock files.
4. Build a minimal runtime image with a numeric non-root user and health check.
5. Run lint and tests before the CI image job; build and smoke-test without credentials.
6. Verify locally, record evidence, and explain failures and next steps.

Architecture decision: follow the reference repository's root Dockerfile, ARCHITECTURE.md,
and numbered DOCS guides. Keep pyproject.toml for Python tooling. A separate aegis-gitops
repository will be introduced in a later approved phase; no deployment files are needed yet.
