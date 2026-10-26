"""Import exact registry content into Kind; never substitute a locally rebuilt digest."""

import argparse
import hashlib
import io
import json
import re
import subprocess
import tarfile
from pathlib import Path

SOURCE = "prasanthece42/aegis-cicd"
ROOT = Path(__file__).resolve().parents[1]


def gh(endpoint, payload=None):
    cmd = ["gh", "api", endpoint]
    if payload is not None:
        cmd += ["--method", "POST", "--input", "-"]
    return json.loads(
        subprocess.check_output(cmd, input=json.dumps(payload) if payload else None, text=True)
    )


def load(tag):
    if not re.fullmatch(r"release-[0-9]+-[0-9]+", tag):
        raise ValueError("Expected a validated release tag")
    kube = [
        "kubectl",
        "--kubeconfig",
        str(ROOT / ".local/kubeconfig"),
        "--context",
        "kind-aegis-dev",
    ]
    server = subprocess.check_output(
        kube + ["config", "view", "--minify", "-o", "jsonpath={.clusters[0].cluster.server}"],
        text=True,
    )
    if not server.startswith("https://127.0.0.1:"):
        raise ValueError("Refusing nonlocal cluster")
    target = ROOT / ".local/releases" / tag
    target.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "gh",
            "release",
            "download",
            tag,
            "--repo",
            SOURCE,
            "--pattern",
            "release.json",
            "--pattern",
            "image.oci.tar",
            "--dir",
            str(target),
            "--clobber",
        ],
        check=True,
    )
    receipt = json.loads((target / "release.json").read_text())
    if (
        receipt["schema_version"] != 2
        or receipt["release_tag"] != tag
        or receipt["source_repository"] != SOURCE
    ):
        raise ValueError("Unexpected release receipt")
    if not re.fullmatch(re.escape("ghcr.io/" + SOURCE) + r"@sha256:[0-9a-f]{64}", receipt["image"]):
        raise ValueError("Invalid registry reference")
    run = gh(f"repos/{SOURCE}/actions/runs/{receipt['run_id']}")
    if (
        run["conclusion"] != "success"
        or run["head_sha"] != receipt["source_commit"]
        or run["head_branch"] != "main"
    ):
        raise ValueError("Source workflow did not complete successfully")
    with open(target / "image.oci.tar", "rb") as bundle:
        if hashlib.file_digest(bundle, "sha256").hexdigest() != receipt["bundle_sha256"]:
            raise ValueError("Bundle checksum mismatch")
    # Normalize only the OCI transport wrapper name; registry manifest/blob bytes stay exact.
    imported = target / "kind-import.oci.tar"
    with (
        tarfile.open(target / "image.oci.tar") as source,
        tarfile.open(imported, "w") as destination,
    ):
        for member in source:
            if member.isdir():
                destination.addfile(member)
                continue
            if not member.isfile():
                raise ValueError("Unexpected non-file OCI archive entry")
            stream = source.extractfile(member)
            if member.name == "index.json":
                wrapper = json.load(stream)
                found = False
                for descriptor in wrapper["manifests"]:
                    if descriptor["digest"] == receipt["image"].split("@")[1]:
                        descriptor.setdefault("annotations", {})["io.containerd.image.name"] = (
                            "ghcr.io/" + SOURCE + ":" + tag
                        )
                        descriptor["annotations"]["org.opencontainers.image.ref.name"] = tag
                        found = True
                if not found:
                    raise ValueError("OCI wrapper does not reference the published index")
                data = json.dumps(wrapper).encode()
                member.size = len(data)
                stream = io.BytesIO(data)
            destination.addfile(member, stream)
    subprocess.run(
        ["kind", "load", "image-archive", str(imported), "--name", "aegis-dev"],
        check=True,
    )
    rows = subprocess.check_output(
        [
            "docker",
            "exec",
            "aegis-dev-control-plane",
            "ctr",
            "--namespace",
            "k8s.io",
            "images",
            "list",
        ],
        text=True,
    ).splitlines()
    digest = receipt["image"].split("@")[1]
    matching = [
        line.split()[0] for line in rows if len(line.split()) > 2 and line.split()[2] == digest
    ]
    if not matching:
        raise ValueError("Imported OCI index differs from registry digest")
    subprocess.run(
        [
            "docker",
            "exec",
            "aegis-dev-control-plane",
            "ctr",
            "--namespace",
            "k8s.io",
            "images",
            "tag",
            "--force",
            matching[0],
            receipt["image"],
        ],
        check=True,
    )
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "local-image-reference.json").write_text(
        json.dumps(
            {
                "source_commit": receipt["source_commit"],
                "image": receipt["image"],
                "profile": "Exact published OCI index imported with both platforms",
            },
            indent=2,
        )
        + "\n"
    )
    gh(
        f"repos/{SOURCE}/statuses/{receipt['source_commit']}",
        {
            "state": "success",
            "context": "aegis/kind-cache-health",
            "description": "Healthy " + receipt["image"],
            "target_url": receipt["workflow_run"],
        },
    )
    print("PASS: verified registry index cached for Kind:", receipt["image"])
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("release_tag")
    args = parser.parse_args()
    load(args.release_tag)
