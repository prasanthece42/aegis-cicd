"""Publish one multi-platform identity only after each child has passed validation."""

import hashlib
import json
import os
import re
import tarfile
from datetime import UTC, datetime
from pathlib import Path


def validate_platforms(index, receipts, source_sha, source_repo):
    expected = {"linux/amd64", "linux/arm64"}
    if set(receipts) != expected:
        raise ValueError("Both platform receipts are required")
    manifests = {
        m["platform"]["os"] + "/" + m["platform"]["architecture"]: m["digest"]
        for m in index["manifests"]
    }
    if set(manifests) != expected or len(index["manifests"]) != 2:
        raise ValueError("Unexpected index platforms")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", index["digest"]):
        raise ValueError("Invalid index digest")
    for platform, receipt in receipts.items():
        if receipt["source_commit"] != source_sha or receipt["source_repository"] != source_repo:
            raise ValueError("Mismatched release source")
        if receipt["platform"] != platform or receipt["digest_pull_smoke_test"] != "passed":
            raise ValueError("Untested platform")
        expected_image = "ghcr.io/" + source_repo.lower() + "@" + manifests[platform]
        if receipt["image"] != expected_image:
            raise ValueError("Published manifest differs from tested platform")


def verify_oci_archive(path, digest):
    with tarfile.open(path) as archive:
        content = archive.extractfile("blobs/sha256/" + digest.split(":")[1]).read()
    if "sha256:" + hashlib.sha256(content).hexdigest() != digest:
        raise ValueError("OCI archive did not preserve the registry index")


def main():
    receipts = {}
    for path in Path("platform-evidence").glob("*/release.json"):
        receipt = json.loads(path.read_text())
        if receipt["platform"] in receipts:
            raise ValueError("Duplicate platform receipt")
        receipts[receipt["platform"]] = receipt
    index = json.loads(Path("reports/index.json").read_text())
    sha, repo = os.environ["SOURCE_SHA"], os.environ["SOURCE_REPOSITORY"]
    validate_platforms(index, receipts, sha, repo)
    verify_oci_archive("reports/image.oci.tar", index["digest"])
    with open("reports/image.oci.tar", "rb") as bundle:
        bundle_hash = hashlib.file_digest(bundle, "sha256").hexdigest()
    image = "ghcr.io/" + repo.lower() + "@" + index["digest"]
    tag = f"release-{os.environ['RUN_ID']}-{os.environ['RUN_ATTEMPT']}"
    evidence = {
        "schema_version": 2,
        "release_tag": tag,
        "verified_at": datetime.now(UTC).isoformat(),
        "image": image,
        "source_repository": repo,
        "source_commit": sha,
        "workflow_run": os.environ["RUN_URL"],
        "run_id": int(os.environ["RUN_ID"]),
        "run_attempt": int(os.environ["RUN_ATTEMPT"]),
        "platforms": receipts,
        "bundle_sha256": bundle_hash,
        "provenance": "Unsigned workflow evidence; source and run verified through GitHub API",
    }
    Path("reports/release.json").write_text(json.dumps(evidence, indent=2) + "\n")
    Path("reports/release-notes.md").write_text(
        f"Validated amd64 and arm64 release\n\nImage: `{image}`\n\n"
        f"Source: `{sha}`\n\nOCI bundle SHA256: `{bundle_hash}`\n"
    )
    print("PASS: both tested manifests and exact registry OCI index verified")


if __name__ == "__main__":
    main()
