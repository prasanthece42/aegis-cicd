#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mode="${1:?Usage: bash scripts/scan-security.sh dependencies|image [IMAGE_ARCHIVE]}"
mkdir -p reports
case "$mode" in
  dependencies)
    # Isolate the lock files so cached environments/reports cannot affect detection.
    scan_dir=$(mktemp -d)
    trap 'rm -rf "$scan_dir"' EXIT
    cp requirements.txt "$scan_dir/requirements.txt"
    cp requirements-prod.txt "$scan_dir/requirements-prod.txt"
    report=reports/dependencies.json
    trivy fs --scanners vuln --list-all-pkgs --format json \
      --output "$report" --timeout 10m "$scan_dir"
    ;;
  image)
    archive="${2:?An image archive from docker save is required}"
    report=reports/image.json
    trivy image --input "$archive" --scanners vuln --list-all-pkgs \
      --format json --output "$report" --timeout 10m
    trivy convert --format cyclonedx --output reports/sbom.cdx.json "$report"
    ;;
  *) printf 'Unknown scan mode: %s\n' "$mode" >&2; exit 2 ;;
esac
# An empty or undetected package inventory must never count as a clean scan.
python3 - "$report" <<'PYTHON'
import json
import sys

with open(sys.argv[1]) as report_file:
    report = json.load(report_file)
results = report.get("Results", [])
assert any(r.get("Packages") for r in results), "Scanner detected no packages"
assert any(r.get("Class") == "lang-pkgs" and r.get("Packages") for r in results), (
    "Scanner detected no application dependency inventory"
)
print("PASS: scanner detected package inventory")
PYTHON
# Keep the complete JSON report; apply the blocking policy to a separate view.
trivy convert --scanners vuln --format table --severity CRITICAL --exit-code 1 "$report"
