# Configuration guide

| File | Purpose and important decisions |
| --- | --- |
| app/__init__.py | Marks the application as a Python package. |
| app/main.py | Creates FastAPI, defines the typed health response, and registers GET /health. |
| tests/test_health.py | Checks exact health JSON/content type, unknown routes, and rejected POST requests through ASGI. |
| pyproject.toml | Declares Python 3.12, Pytest discovery/import path, and Ruff rules including import ordering and bug checks. |
| requirements-prod.in | Direct, exact FastAPI and Uvicorn pins. |
| requirements-prod.txt | Fully resolved runtime packages and allowed artifact hashes. |
| requirements.in | Adds HTTPX, Pytest, and Ruff to the runtime lock. |
| requirements.txt | Fully resolved local and CI packages with hashes. |
| Dockerfile | Builder installs runtime dependencies; runtime copies only the environment and app. Numeric USER avoids root; exec-form CMD allows termination signals to reach Uvicorn. HEALTHCHECK validates HTTP and JSON using Python's standard library. |
| .dockerignore | Allowlist prevents source-control files, credentials, tests, or virtual environments entering the build context. |
| .gitignore | Excludes local caches, environments, and secret env files from Git. |
| .github/workflows/ci.yml | Defines triggers, read-only permissions, CI concurrency, caching, ordered gates, and container smoke checks. |
| scripts/bootstrap-local.sh | Creates a colon-free Python 3.12 virtual environment and installs locked dependencies. |
| scripts/verify-local.sh | Runs the same lint, format, and test commands as CI. |
| scripts/verify-container.sh | Starts, verifies, logs, and removes a disposable hardened container. Requires an image argument. |
| README.md | Entry point, structure, stack, commands, and numbered documentation index. |
| ARCHITECTURE.md | Shows implemented flow separately from future GitOps delivery. |
| DOCS/01 through DOCS/08 | Plan, operations, configuration reference, evidence, and teaching material. |

A Docker HEALTHCHECK only records health; Docker does not automatically restart an
unhealthy process. Kubernetes probes will be configured in their own phase.
