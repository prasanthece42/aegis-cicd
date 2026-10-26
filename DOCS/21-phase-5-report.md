# Phase 5 — Release management verification report

Recorded 2026-10-26 UTC. DEV and STAGING delivery, enforced GitOps PR controls,
failure blocking, Git rollback, live drift repair and human-approved local PROD
deployment are verified. The separately approved background delivery bridge is running.

## Architecture and implementation

The source pipeline natively tests and scans linux/amd64 and linux/arm64, publishes
an immutable OCI index, verifies digest pulls and retains an exact OCI bundle plus
release receipt. A verified local import supplies Kind without a registry PAT.
The GitOps-owned workflow proposes the selected release using its short-lived
GITHUB_TOKEN. Checked PR merges drive DEV; fresh prior-environment health permits
STAGING and then PROD proposals. STAGING/PROD require explicit Argo sync.

Both repositories were made public after explicit user approval and full-history
Gitleaks v8.30.1 scans with no detected leaks. Local credentials stay ignored. A final directory scan also found the ignored local
kubeconfig and public Python base-image GPG_KEY values in generated reports. All four
findings were verified untracked/ignored; exact publication files and both Git histories
then passed with no detected leaks before publication continued. The
former Argo SSH deploy key was revoked; public HTTPS reconciliation is healthy.
GHCR remains private; the release receipt and OCI delivery bundle are public.

Application main now requires its actual lint/test/dependency-scan and amd64 container
checks through PRs, including administrators, with strict current checks and no
force-push/deletion. Its single-maintainer PRs do not require another reviewer.
GitOps main/staging/prod require chart and promotion-policy checks, current branches,
PRs, resolved conversations and linear history, including administrators. Force-push
and deletion are blocked. CODEOWNERS protects sensitive paths. PROD requires a fresh
independent human review at the current PR head. The policy rejects missing, stale,
self and bot reviews; production is not auto-approved by any workflow.

## Actual release and environment results

Chosen release [40259693000](https://github.com/prasanthece42/aegis-cicd/actions/runs/40259693000)
succeeded for both architectures. Source SHA: 51702a46d18ecdec39ba9f94ecbc47a28228d815.

```text
ghcr.io/prasanthece42/aegis-cicd@sha256:e02908653b52ef077cbcde43874edb49449f1bc47af5a7e469e17f0bc8fee8ef
```

| Verification | Actual result |
| --- | --- |
| Application quality | Ruff, formatting and 20 tests passed |
| Promotion policy | Ruff, formatting and 13 tests passed |
| Standalone application CI | [40262986427](https://github.com/prasanthece42/aegis-cicd/actions/runs/40262986427) succeeded |
| Latest helper release checks | [40261868130](https://github.com/prasanthece42/aegis-cicd/actions/runs/40261868130) succeeded; chosen runtime remains the release above |
| Chart validation | DEV/STAGING/PROD and historical local profile: 16 resources, schemas and negative cases passed |
| Exact OCI delivery | Bundle hash, root index and imported Kind digest verified; actual Service HTTP passed |
| DEV PR #1 | Merged; Synced/Healthy at 1bfedb2ff3a1a279aae2eb7106b4d0a8796a59dd |
| STAGING PR #2 | Merged; two replicas Synced/Healthy at ac40770c03aa6b7708d37fb30e5de23adb132544, same image |
| PROD PR #3 | Independently approved at unchanged head after explicit user authorization; all checks passed, merged at 38a294e48dcc77f1331abb7693900b7acbc4721f |
| PROD deployment | Argo Synced/Healthy, three replicas, real Service HTTP passed; same release digest as the DEV/STAGING promotion |
| PROD local sync negative test | Before approval/merge, refused because no approved merged release PR existed |
| DEV failure PR #4 | Merged at 84343c38bcbc9437cb234bbf7c92f855aff3a45a; new pod actually OOMKilled at 8Mi limit |
| Failed DEV promotion | [40262549462](https://github.com/prasanthece42/aegis-gitops/actions/runs/40262549462) correctly failed its prior-health gate |
| Rollback PR #5 | Git revert merged at 48a6e601604213eb66caba60b3f0309ec17e5b23; DEV recovered Synced/Healthy with unchanged image |
| Documentation PR #6 | Both required checks passed; merged, DEV still Synced/Healthy at f8607dd173136bd87fb797e7c4d1cb546815f5bf |
| Live drift | Temporary DEV replicas 1 → 3; Argo restored Git desired count 1, ready 1 |

The old ready replica answered /health during the failed rollout. That is a measured
observation, not a continuous zero-downtime guarantee. This drill tested a real memory
configuration failure and Git rollback, not a broken production image.

The durable [JSON evidence record](deployments/phase-5-release-management.json) retains
exact environment health revisions, timestamps, digest, failure, recovery and drift.
Full transient command output remains in ignored reports/ and GitHub workflow logs.

## Failures diagnosed and corrected

Native arm64 runners replaced an emulated arm64 container health timeout. OCI format
conversion first failed digest preservation, then changed container configuration and
removed health metadata; identity checks caught both. Publication now normalizes only
manifest descriptor media types while preserving config/layer blobs and verifies the
new published digest. The OCI transport wrapper uses a unique fully qualified image
name so containerd resolves the imported index correctly without changing its blobs.
Manual Argo sync now carries syncOptions, including namespace creation, and retry
settings from the Application. STAGING was retested successfully after that fix.

GitHub additionally held bot PR workflows for execution approval. The known validation
diffs were checked before approving CI execution; no production PR review was submitted.
Explicit validation dispatch also checks the exact bot PR head. Neither mechanism
replaces the required human production review.

## Changed code and operational commands

Source: ci.yml and release.yml, OCI manifest/index/evidence helpers, exact bundle
loader, environment sync/observer, optional local bridge and branch protection setup.
GitOps: promotion.py, policy tests and hashed dependencies, validation/proposal workflows,
CODEOWNERS, branch-specific Argo projects/Applications, values and release pointers.
The [release guide](20-release-management-guide.md) maps each file to its purpose and
includes commands, troubleshooting, rollback and interview questions.

```bash
bash scripts/verify-local.sh
python3.12 scripts/load_release_bundle.py release-40259693000-1
python3.12 scripts/environment_delivery.py observe dev --wait
python3.12 scripts/environment_delivery.py sync staging
# In the GitOps checkout:
/tmp/aegis-gitops-venv/bin/pytest
bash scripts/validate-chart.sh
```

All Kubernetes operations use the isolated kubeconfig and explicit kind-aegis-dev
context. GitHub Actions has no cluster credentials. The existing AWS context was not
used and no AWS resources were provisioned.

## Authorized production deployment and ongoing operation

The user explicitly approved submitting their human review for
[Production PR #3](https://github.com/prasanthece42/aegis-gitops/pull/3), merging after
checks and deploying local PROD. The exact approved head remained
b35ce64a305fb73d8f756822222e34cad71f2757. Review was submitted by prasanthece42 at
2026-10-26T14:01:26Z, independently of the bot author. Review-event validation
40335801833 passed. The original pre-approval policy failure was also rerun and passed
before GitHub allowed a normal protected merge; no --admin or policy bypass was used.
Argo then deployed revision 38a294e48dcc77f1331abb7693900b7acbc4721f with three healthy
replicas and the same exact validated OCI digest. The Service HTTP observation passed.

The final source documentation CI initially hit a Trivy database mirror 404; retrying
the failed job passed with the full security gate enforced (40272827305, attempt 2).
No scan was skipped and no vulnerability policy was weakened.

Automatic approval review initially rejected unattended background side effects.
The user subsequently explicitly approved the background bridge. It was started in a
detached process session and checked alive; ignored .local/delivery-watch.pid, log and
state files record local operation. It polls every 30 seconds, imports verified releases,
proposes DEV PRs through Actions and observes DEV health. It never approves or syncs
PROD. The initial shell/nohup process did not persist; detached process startup replaced
it. It runs while the workstation is awake; it is not an installed boot service.
Stop the recorded process using the guide. Future releases may advance DEV independently;
STAGING/PROD remain explicit promotions of a selected tested digest.

Health is a 24-hour operator-attributed observation, not signed runtime attestation.
Release receipts are unsigned. The lab uses three local namespaces, not independent
production clusters. Production SSO/RBAC hardening, hosted observers and cloud registry
credentials remain outside this phase. No Phase 6 work has started.
