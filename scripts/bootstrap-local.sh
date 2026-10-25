#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
venv_dir="${AEGIS_VENV_DIR:-${TMPDIR:-/tmp}/aegis-cicd-venv}"
python3.12 -m venv "$venv_dir"
"$venv_dir/bin/python" -m pip install --require-hashes -r requirements.txt
printf 'Ready. Run: %s/bin/uvicorn app.main:app --reload\n' "$venv_dir"
