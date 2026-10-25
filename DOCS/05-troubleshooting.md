# Troubleshooting

| Symptom | Check and action |
| --- | --- |
| Python venv rejects PATH separator | Use the setup script's temporary default or AEGIS_VENV_DIR outside the colon-containing workspace. |
| python3.12 missing | Install Python 3.12 and ensure that executable is on PATH. Python 3.13 is not this project's supported version. |
| PyPI DNS/download failure | Check network access, proxy, and sandbox permissions; retry bootstrap. Do not remove hash checks. |
| ModuleNotFoundError | Re-run bootstrap; invoke the documented virtual environment's Python or Uvicorn. |
| Ruff fails | Read the path/line diagnostic. Use the virtual environment's Ruff formatter when formatting is the issue; rerun verification. |
| Pytest fails | Read the assertion and reproduce with the virtual environment's python -m pytest -vv. |
| anyio BlockingPortal warning | Current Starlette TestClient uses a deprecated alias. Tests still pass; update compatible upstream dependencies when fixed rather than hiding warnings. |
| Docker daemon permission denied | Start Docker Desktop, inspect docker context and docker version; sandbox access may require elevated execution. |
| Docker base image pull fails | Check Docker Hub connectivity, configured credentials, and the exact base-image tag. |
| Container unhealthy | The smoke script prints logs. Confirm Uvicorn listens on 0.0.0.0:8000 and /health returns the documented contract. |
| Local port 8000 occupied | Run Uvicorn on another --port. The container smoke script allocates its own host port. |
| GitHub workflow absent | Confirm .github/workflows/ci.yml is at the remote repository root and Actions is enabled. |
| Container job skipped | Fix the earlier lint, formatting, or test failure first. |

Local verification is evidence for this host only. The GitHub Linux amd64 build and
container smoke test have also passed; see the Phase 1 report for the run link. Nothing deploys in Phase 1.
