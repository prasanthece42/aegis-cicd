import pytest

from scripts.oci_manifest import normalize
from scripts.release_evidence import resolve_reference


def test_oci_conversion_preserves_config_and_layer_digest_sizes():
    manifest = {
        "schemaVersion": 2,
        "config": {
            "digest": "sha256:abc",
            "size": 42,
            "mediaType": "application/vnd.docker.container.image.v1+json",
        },
        "layers": [
            {
                "digest": "sha256:def",
                "size": 55,
                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            }
        ],
    }
    output = normalize(manifest)
    assert output["config"]["digest"] == manifest["config"]["digest"]
    assert output["config"]["size"] == manifest["config"]["size"]
    assert output["layers"][0]["digest"] == manifest["layers"][0]["digest"]
    assert output["layers"][0]["size"] == manifest["layers"][0]["size"]
    assert output["mediaType"] == "application/vnd.oci.image.manifest.v1+json"


def test_known_published_digest_selected_over_old_transport_digest():
    name = "ghcr.io/prasanthece42/aegis-cicd"
    old, new = "sha256:" + "a" * 64, "sha256:" + "b" * 64
    assert resolve_reference([name + "@" + old, name + "@" + new], name, new) == name + "@" + new
    with pytest.raises(ValueError):
        resolve_reference([name + "@" + old], name, new)
