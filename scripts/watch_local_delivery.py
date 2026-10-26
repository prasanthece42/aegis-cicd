"""Local registry-cache bridge: import exact releases, propose DEV, observe health."""

import argparse
import json
import time

from scripts.environment_delivery import api, head, observe
from scripts.load_release_bundle import ROOT, load

STATE = ROOT / ".local/delivery-watch-state.json"


def cycle():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    release = api("repos/prasanthece42/aegis-cicd/releases/latest")
    tag = release["tag_name"]
    if state.get("release_tag") != tag or time.time() - state.get("loaded_at", 0) > 12 * 3600:
        load(tag)
        # Only cache content is loaded; Argo remains the application deployer.
        import subprocess

        subprocess.run(
            [
                "gh",
                "workflow",
                "run",
                "promote.yml",
                "--repo",
                "prasanthece42/aegis-gitops",
                "--ref",
                "main",
                "-f",
                "environment=dev",
                "-f",
                "release_tag=" + tag,
            ],
            check=True,
        )
        state["release_tag"] = tag
        state["loaded_at"] = time.time()
    revision = head("dev")
    if (
        state.get("healthy_revision") != revision
        or time.time() - state.get("health_at", 0) > 12 * 3600
    ):
        observe("dev", wait=True)
        state["healthy_revision"] = revision
        state["health_at"] = time.time()
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    while True:
        try:
            cycle()
        except Exception as error:
            print("Delivery bridge failed closed:", error, flush=True)
            if args.once:
                raise
        if args.once:
            return
        time.sleep(30)


if __name__ == "__main__":
    main()
