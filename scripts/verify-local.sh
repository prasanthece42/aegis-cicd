#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
venv_dir="${AEGIS_VENV_DIR:-${TMPDIR:-/tmp}/aegis-cicd-venv}"
"$venv_dir/bin/ruff" check .
"$venv_dir/bin/ruff" format --check .
"$venv_dir/bin/python" -m pytest
