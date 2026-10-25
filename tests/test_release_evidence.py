"""Ensure wrong-source and wrong-image releases cannot pass identity verification."""

from copy import deepcopy

import pytest

from scripts.release_evidence import resolve_reference, validate_candidate, validate_pulled

SHA = "a" * 40
SOURCE = "https://github.com/example/aegis-cicd"
IMAGE_ID = "sha256:" + "b" * 64
CANDIDATE = {
    "Id": IMAGE_ID,
    "Config": {
        "Labels": {
            "org.opencontainers.image.revision": SHA,
            "org.opencontainers.image.source": SOURCE,
        }
    },
}
SCAN = {"Metadata": {"ImageID": IMAGE_ID}}


def test_matching_candidate_and_scan_pass():
    validate_candidate(CANDIDATE, CANDIDATE, SHA, SOURCE, SCAN, IMAGE_ID)


@pytest.mark.parametrize(
    "field,value",
    [
        ("org.opencontainers.image.revision", "c" * 40),
        ("org.opencontainers.image.source", "https://github.com/other/repository"),
    ],
)
def test_wrong_source_is_rejected(field, value):
    actual = deepcopy(CANDIDATE)
    actual["Config"]["Labels"][field] = value
    with pytest.raises(ValueError):
        validate_candidate(CANDIDATE, actual, SHA, SOURCE, SCAN, IMAGE_ID)


def test_scan_of_different_image_is_rejected():
    with pytest.raises(ValueError, match="scan"):
        validate_candidate(
            CANDIDATE,
            CANDIDATE,
            SHA,
            SOURCE,
            {"Metadata": {"ImageID": "sha256:" + "c" * 64}},
            IMAGE_ID,
        )


def test_pulled_image_must_match_candidate():
    with pytest.raises(ValueError, match="differs"):
        validate_pulled(CANDIDATE, {"Id": "sha256:" + "c" * 64})


def test_registry_digest_is_scoped_to_repository():
    reference = "ghcr.io/example/aegis-cicd@sha256:" + "d" * 64
    assert resolve_reference([reference], "ghcr.io/example/aegis-cicd") == reference
    with pytest.raises(ValueError):
        resolve_reference([reference], "ghcr.io/other/aegis-cicd")


def test_mutable_tag_is_not_a_digest():
    with pytest.raises(ValueError):
        resolve_reference(["ghcr.io/example/aegis-cicd:latest"], "ghcr.io/example/aegis-cicd")


def test_manifest_id_may_differ_from_scanner_config_id():
    candidate = deepcopy(CANDIDATE)
    candidate["Id"] = "sha256:" + "e" * 64
    validate_candidate(candidate, candidate, SHA, SOURCE, SCAN, IMAGE_ID)


def test_loaded_image_must_match_candidate_metadata():
    actual = deepcopy(CANDIDATE)
    actual["Id"] = "sha256:" + "e" * 64
    with pytest.raises(ValueError, match="Loaded image"):
        validate_candidate(CANDIDATE, actual, SHA, SOURCE, SCAN, IMAGE_ID)
