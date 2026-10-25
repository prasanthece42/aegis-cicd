# Phase 1 verification report

Date: October 25, 2026 (America/Halifax).

## Architecture and files

Application source → Ruff/Pytest → Docker build → running-container HTTP verification.
The application is a separate Git repository on main, pushed to the private
GitHub repository `prasanthece42/aegis-cicd`. See the README project tree and configuration guide for the complete
file inventory and each file's purpose. Numbered DOCS guides, root ARCHITECTURE.md,
and root Dockerfile follow the user-selected reference repository's format.

## Commands executed

Workspace inspection used pwd, ls, rg --files, git status, command -v,
python3.12 --version, and docker version. The initial parent directory was not a Git
repository. Docker initially required sandbox elevation; daemon access then passed.

Dependency versions were queried from PyPI and action SHAs verified against the
GitHub API. uv resolved direct pins into fully hashed locks:

```bash
uv pip compile requirements-prod.in --python-version 3.12 --generate-hashes --output-file requirements-prod.txt --cache-dir /tmp/aegis-uv-cache --quiet
uv pip compile requirements.in --python-version 3.12 --generate-hashes --output-file requirements.txt --cache-dir /tmp/aegis-uv-cache --quiet
bash scripts/bootstrap-local.sh
bash scripts/verify-local.sh
bash -n scripts/bootstrap-local.sh scripts/verify-local.sh scripts/verify-container.sh
/tmp/aegis-actionlint -shellcheck= .github/workflows/ci.yml
docker build --tag aegis-sample:phase1 .
bash scripts/verify-container.sh aegis-sample:phase1
docker image inspect aegis-sample:phase1 --format '{{.Id}} {{.Os}}/{{.Architecture}} user={{.Config.User}}'
git init -b main
```

A Python subprocess harness also started the virtual environment's Uvicorn on a
free loopback port, requested /health with urllib.request, asserted status/body,
and terminated the process. The verification container was removed after testing.
The locally downloaded actionlint executable is outside the repository.

## Results

| Check | Status | Evidence |
| --- | --- | --- |
| Locked package installation | PASS | pip --require-hashes installed runtime and dev dependencies |
| Ruff lint | PASS | All checks passed |
| Ruff formatting | PASS | All checked files formatted |
| Pytest | PASS | 3 passed; 1 upstream deprecation warning |
| Local Uvicorn HTTP | PASS | Actual /health request returned 200 and expected JSON |
| Bash syntax | PASS | bash -n returned zero |
| Workflow validation | PASS | actionlint v1.7.12 returned zero |
| ShellCheck static analysis | NOT RUN | Not installed; disabled in actionlint invocation; Bash syntax checked separately |
| Docker build | PASS | Built real linux/arm64 image |
| Container health and HTTP | PASS | Docker healthy, host HTTP contract verified |
| Non-root/hardened runtime | PASS | UID 10001; read-only filesystem; all capabilities dropped |
| GitHub-hosted CI | PASS | [Run 40244734844](https://github.com/prasanthece42/aegis-cicd/actions/runs/40244734844), source commit 4ef9c1626fef70e6b33a5d3a5b597de052a8e888 |
| Linux amd64 execution | PASS | GitHub ubuntu-24.04 runner built and smoke-tested the image |
| Vulnerability scans / registry / Kubernetes | NOT RUN | Outside approved Phase 1 scope |

Local image ID (not a published registry digest):
`sha256:73742011e102cf23579e355e8fbf1829a5b3120428a6302f38c78e627607d07d`.

## Resolved environment failures and outstanding limitations

The initial PyPI request failed DNS inside the restricted sandbox; authorized network
access resolved it. Standard venv creation rejected the colon in AICI:CD; setup now
uses a configurable temporary directory outside the workspace. No local blocker remains.

Starlette TestClient emits an anyio BlockingPortal deprecation warning. All assertions
pass; the warning remains visible. The temporary virtual environment may be cleaned
by the OS; rerun bootstrap if needed.

## Security and next step

No deployment credentials or secrets are needed. CI uses contents:read and SHA-pinned
actions, installs hash-verified dependencies, and builds only after checks. The runtime
runs as non-root and the build context is allowlisted. Package and image vulnerability
scanning, base-image digest pinning, GHCR publishing, provenance, and immutable release
digests are deferred to Phase 2. A SHA image tag alone is not immutable storage.

GitHub CI passed: Lint and tests completed in 16 seconds; Build and smoke-test
container completed in 26 seconds. GitHub emitted a non-failing Node.js 20 deprecation
annotation for the pinned checkout/setup-python actions, which ran under Node.js 24.
Update their verified SHA pins to Node.js 24-native versions in a maintenance change.

After explicit approval, implement Phase 2 security policy, Trivy scans, GHCR
publishing, and release evidence. No Phase 2 code or cloud resources were added.

## GitHub execution commands

After the user approved the exact private destination:

```bash
git add .
git commit -m 'Build Phase 1 API and CI foundation'
gh repo create prasanthece42/aegis-cicd --private --source . --remote origin --push
gh run list --repo prasanthece42/aegis-cicd --limit 3 --json databaseId,headSha,status,conclusion,url
gh run watch 40244734844 --repo prasanthece42/aegis-cicd --exit-status --interval 10
```
