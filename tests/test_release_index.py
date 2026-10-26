"""Reject untested/mismatched platform manifests before release publication."""

from copy import deepcopy

import pytest

from scripts.release_index import validate_platforms

SHA = "a" * 40
REPO = "prasanthece42/aegis-cicd"
INDEX = {
    "digest": "sha256:" + "c" * 64,
    "manifests": [
        {"platform": {"os": "linux", "architecture": arch}, "digest": "sha256:" + char * 64}
        for arch, char in [("amd64", "d"), ("arm64", "e")]
    ],
}
RECEIPTS = {
    "linux/" + arch: {
        "source_commit": SHA,
        "source_repository": REPO,
        "platform": "linux/" + arch,
        "digest_pull_smoke_test": "passed",
        "image": "ghcr.io/" + REPO + "@sha256:" + char * 64,
    }
    for arch, char in [("amd64", "d"), ("arm64", "e")]
}


def test_both_validated_platforms_pass():
    validate_platforms(INDEX, RECEIPTS, SHA, REPO)


def test_missing_platform_fails():
    with pytest.raises(ValueError, match="Both"):
        validate_platforms(INDEX, {"linux/amd64": RECEIPTS["linux/amd64"]}, SHA, REPO)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_commit", "b" * 40),
        ("source_repository", "other/repo"),
        ("digest_pull_smoke_test", "failed"),
        ("image", "ghcr.io/other/repo@sha256:" + "f" * 64),
    ],
)
def test_mismatched_or_untested_child_fails(field, value):
    receipts = deepcopy(RECEIPTS)
    receipts["linux/arm64"][field] = value
    with pytest.raises(ValueError):
        validate_platforms(INDEX, receipts, SHA, REPO)
