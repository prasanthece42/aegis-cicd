# Setup guide

1. Install Python 3.12, Git, Docker Desktop, and curl. Start Docker Desktop.
2. Open this repository as the project root; use the README commands to bootstrap,
   run checks, start Uvicorn, and verify Docker.
3. Open `http://127.0.0.1:8000/docs` for the generated API documentation.

The scripts invoke the virtual environment's executables directly; activation is
unnecessary. For persistent local dependencies, set `AEGIS_VENV_DIR` to a colon-free
absolute directory you own before running bootstrap and verification. Do not put it
under the current `AICI:CD` workspace. The temporary default can be deleted by the OS.

## Bootstrap the application repository on GitHub

This directory is the application repository root. The workflow must be at its top
level, not buried inside a parent repository. Create an empty GitHub repository
named `aegis-cicd` in your account, then run from here:

```bash
git add .
git commit -m "Build Phase 1 API and CI foundation"
# Replace YOUR_ACCOUNT before running:
git remote add origin https://github.com/YOUR_ACCOUNT/aegis-cicd.git
git push -u origin main
```

This project is now pushed to the private repository `prasanthece42/aegis-cicd`,
and its first GitHub CI run passed. The commands above document bootstrap for a new
copy; do not repeat repository creation for the existing remote. Configure branch
protection to require both jobs. Pull requests run the
same checks without deployment secrets or registry credentials.

## Bootstrap the GitOps repository later

When Phase 3/4 is approved, create a separate sibling directory and GitHub repository
named `aegis-gitops`. Initialize it on main and add charts, environments, and declarative
Argo CD Applications there. Connect Argo CD to that remote. These are future steps;
no empty GitOps scaffold or deployment integration is included in Phase 1.

## Update dependency locks

Using uv (the developer lock-generation tool):

```bash
uv pip compile requirements-prod.in --python-version 3.12 --generate-hashes -o requirements-prod.txt
uv pip compile requirements.in --python-version 3.12 --generate-hashes -o requirements.txt
bash scripts/bootstrap-local.sh
bash scripts/verify-local.sh
```

Commit input and output files together. Installation uses pip with `--require-hashes`;
CI and Docker do not need uv. Rebuild the image after dependency changes.
