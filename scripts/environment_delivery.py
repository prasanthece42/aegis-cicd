"""Local Argo synchronization and operator health observations for promotion gates."""

import argparse
import json
import socket
import subprocess
import tempfile
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "prasanthece42/aegis-gitops"
BRANCH = {"dev": "main", "staging": "staging", "prod": "prod"}
APP = {
    "dev": "sample-api-local",
    "staging": "sample-api-staging-local",
    "prod": "sample-api-prod-local",
}
KUBE = ["kubectl", "--kubeconfig", str(ROOT / ".local/kubeconfig"), "--context", "kind-aegis-dev"]


def api(endpoint, payload=None):
    cmd = ["gh", "api", endpoint]
    if payload is not None:
        cmd += ["--method", "POST", "--input", "-"]
    output = subprocess.check_output(cmd, input=json.dumps(payload) if payload else None, text=True)
    return json.loads(output) if output.strip() else None


def get(kind, name, namespace):
    return json.loads(
        subprocess.check_output(
            KUBE + ["-n", namespace, "get", kind, name, "-o", "json"], text=True
        )
    )


def head(environment):
    return api(f"repos/{REPO}/git/ref/heads/{BRANCH[environment]}")["object"]["sha"]


def sync(environment):
    # Protected target branches enforce approval; sync their exact current HEAD.
    revision = head(environment)
    checks = api(f"repos/{REPO}/commits/{revision}/pulls")
    if environment == "prod":
        protection = api(f"repos/{REPO}/branches/prod/protection")
        if (
            not protection.get("enforce_admins", {}).get("enabled")
            or protection.get("required_pull_request_reviews", {}).get(
                "required_approving_review_count", 0
            )
            < 1
        ):
            raise ValueError("PROD branch protections are not enforced")
        merged = [p for p in checks if p.get("merged_at") and p["base"]["ref"] == "prod"]
        if not merged:
            raise ValueError("PROD has no approved merged release PR at this revision")
        pr = merged[0]
        reviews = []
        page = 1
        while True:
            batch = api(f"repos/{REPO}/pulls/{pr['number']}/reviews?per_page=100&page={page}")
            reviews += batch
            if len(batch) < 100:
                break
            page += 1
        allowed = [
            r
            for r in reviews
            if r["state"] == "APPROVED"
            and r["commit_id"] == pr["head"]["sha"]
            and r["user"]["login"] == "prasanthece42"
            and r["user"]["login"] != pr["user"]["login"]
            and r["user"]["type"] != "Bot"
        ]
        if not allowed:
            raise ValueError("PROD needs an independent current-head human approval")
    patch = {"operation": {"sync": {"revision": revision, "prune": True}}}
    subprocess.run(
        KUBE
        + [
            "-n",
            "argocd",
            "patch",
            "application",
            APP[environment],
            "--type",
            "merge",
            "-p",
            json.dumps(patch),
        ],
        check=True,
    )
    observe(environment, wait=True)


def http_health(environment):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryFile() as log:
        proc = subprocess.Popen(
            KUBE
            + [
                "-n",
                "aegis-" + environment,
                "port-forward",
                "service/sample-api",
                f"{port}:80",
                "--address",
                "127.0.0.1",
            ],
            stdout=log,
            stderr=log,
        )
        try:
            for _ in range(40):
                if proc.poll() is not None:
                    log.seek(0)
                    raise RuntimeError(log.read().decode())
                try:
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:{port}/health", timeout=2
                    ) as response:
                        if response.status != 200 or json.load(response) != {"status": "ok"}:
                            raise ValueError("Unexpected HTTP health response")
                    return
                except OSError:
                    time.sleep(0.25)
            raise RuntimeError("HTTP port-forward timeout")
        finally:
            proc.terminate()
            proc.wait(timeout=10)


def observe(environment, wait=False, expect_failure=False):
    revision = head(environment)
    deadline = time.monotonic() + (240 if wait else 1)
    last = None
    while True:
        app = get("application", APP[environment], "argocd")
        status = app.get("status", {})
        state = (
            status.get("sync", {}).get("status"),
            status.get("health", {}).get("status"),
            status.get("sync", {}).get("revision"),
        )
        if state != last:
            print(environment, state, flush=True)
            last = state
        healthy = state == ("Synced", "Healthy", revision)
        if app["spec"]["source"]["targetRevision"] != BRANCH[environment]:
            raise ValueError("Wrong Argo source branch")
        if healthy or time.monotonic() >= deadline or expect_failure:
            break
        time.sleep(5)
    deployment = get("deployment", "sample-api", "aegis-" + environment)
    image = deployment["spec"]["template"]["spec"]["containers"][0]["image"]
    if healthy:
        desired = deployment["spec"]["replicas"]
        healthy = deployment.get("status", {}).get("availableReplicas", 0) == desired
        healthy &= (
            deployment.get("status", {}).get("observedGeneration", 0)
            >= deployment["metadata"]["generation"]
        )
    if healthy:
        http_health(environment)
    state_value = "success" if healthy else "failure"
    api(
        f"repos/{REPO}/statuses/{revision}",
        {
            "state": state_value,
            "context": f"aegis/{environment}-health",
            "description": ("Healthy " if healthy else "Unhealthy ") + image,
            "target_url": f"https://github.com/{REPO}/commit/{revision}",
        },
    )
    record = {
        "environment": environment,
        "revision": revision,
        "image": image,
        "state": state_value,
        "argocd": list(state),
        "observed_at": datetime.now(UTC).isoformat(),
    }
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / f"{environment}-health.json").write_text(json.dumps(record, indent=2) + "\n")
    if expect_failure and healthy:
        raise ValueError("Expected failure, but environment is healthy")
    if not healthy and not expect_failure:
        raise ValueError("Environment failed health validation")
    print("PASS: recorded operator observation", record, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["sync", "observe"])
    parser.add_argument("environment", choices=BRANCH)
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--expect-failure", action="store_true")
    args = parser.parse_args()
    if args.command == "sync":
        sync(args.environment)
    else:
        observe(args.environment, args.wait, args.expect_failure)
