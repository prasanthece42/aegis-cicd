"""Bind the scanned candidate, registry digest, and retained release evidence."""

import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path

REPORTS = Path("reports")


def read_json(path):
    return json.loads(Path(path).read_text())


def image_config_digest(archive_path):
    """Docker stores may expose an index/manifest ID; Trivy reports the config ID."""
    with tarfile.open(archive_path) as archive:
        manifests = json.load(archive.extractfile("manifest.json"))
        if len(manifests) != 1:
            raise ValueError("Expected a single candidate image")
        config = archive.extractfile(manifests[0]["Config"]).read()
    return "sha256:" + hashlib.sha256(config).hexdigest()


def validate_candidate(candidate, actual, source_sha, source_url, scan, config_digest):
    """Reject wrong-source images and scan reports for different image bytes."""
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("Invalid source commit")
    labels = actual["Config"].get("Labels") or {}
    if labels.get("org.opencontainers.image.revision") != source_sha:
        raise ValueError("Candidate revision does not match workflow commit")
    if labels.get("org.opencontainers.image.source") != source_url:
        raise ValueError("Candidate source repository does not match")
    if actual["Id"] != candidate["Id"]:
        raise ValueError("Loaded image does not match candidate metadata")
    if scan.get("Metadata", {}).get("ImageID") != config_digest:
        raise ValueError("Image scan does not describe the candidate image")


def resolve_reference(repo_digests, image_name):
    for reference in repo_digests:
        if re.fullmatch(re.escape(image_name) + r"@sha256:[0-9a-f]{64}", reference):
            return reference
    raise ValueError("Registry returned no valid digest for the expected image repository")


def validate_pulled(candidate, pulled):
    if candidate["Id"] != pulled["Id"]:
        raise ValueError("Digest-pulled image differs from the scanned candidate")


def main(command):
    candidate = read_json("candidate/image-inspect.json")[0]
    if command == "check-candidate":
        actual = json.loads(
            subprocess.check_output(
                ["docker", "image", "inspect", "aegis-sample:" + os.environ["SOURCE_SHA"]],
                text=True,
            )
        )[0]
        source_url = "https://github.com/" + os.environ["SOURCE_REPOSITORY"]
        validate_candidate(
            candidate,
            actual,
            os.environ["SOURCE_SHA"],
            source_url,
            read_json(REPORTS / "image.json"),
            image_config_digest("candidate/image.tar"),
        )
    elif command == "resolve-digest":
        pushed = read_json(REPORTS / "pushed-image.json")[0]
        validate_pulled(candidate, pushed)
        reference = resolve_reference(pushed.get("RepoDigests", []), os.environ["IMAGE_NAME"])
        (REPORTS / "image-reference.txt").write_text(reference + "\n")
        print(reference)
    elif command == "check-pulled":
        validate_pulled(candidate, read_json(REPORTS / "pulled-image.json")[0])
    elif command == "write":
        validate_pulled(candidate, read_json(REPORTS / "pulled-image.json")[0])
        evidence_files = ["dependencies.json", "image.json", "sbom.cdx.json"]
        evidence = {
            "schema_version": 1,
            "verified_at": datetime.now(UTC).isoformat(),
            "image": (REPORTS / "image-reference.txt").read_text().strip(),
            "tag": os.environ["IMAGE_TAG"],
            "image_config_digest": image_config_digest("candidate/image.tar"),
            "source_repository": os.environ["SOURCE_REPOSITORY"],
            "source_commit": os.environ["SOURCE_SHA"],
            "workflow_run": os.environ["RUN_URL"],
            "run_attempt": os.environ["RUN_ATTEMPT"],
            "platform": candidate["Os"] + "/" + candidate["Architecture"],
            "scanner": "Trivy 0.76.1",
            "policy": "Block every CRITICAL vulnerability, including unfixed findings",
            "digest_pull_smoke_test": "passed",
            "provenance": "Unsigned workflow evidence; not a signed attestation",
            "evidence_sha256": {
                name: hashlib.sha256((REPORTS / name).read_bytes()).hexdigest()
                for name in evidence_files
            },
        }
        (REPORTS / "release.json").write_text(json.dumps(evidence, indent=2) + "\n")
    else:
        raise ValueError("Unknown command: " + command)
    print("PASS:", command)


if __name__ == "__main__":
    main(sys.argv[1])
