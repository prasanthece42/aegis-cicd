# Phase 4 verification report

Date: October 25, 2026 (America/Halifax).

## Architecture and scope

The private GitOps repository main branch is now continuously read by Argo CD inside
the local Kind cluster. Argo renders the existing Helm chart with DEV plus the
tracked local native-image profile and reconciles the aegis-dev workload. CI validates
source/configuration and does not deploy application resources.

Added pinned Argo installation config; install/register/connect/verify/port-forward
scripts; a live Git-driven test script; a guard on manual Helm bootstrap; numbered
plan/guide/report and receipt. GitOps adds a local values profile, scoped/default-deny
projects, Application, controller config, a local-profile chart validation, and guide.

## Results

| Check | Status | Evidence |
| --- | --- | --- |
| Pinned Argo installation | PASS | v3.5.6 manifest SHA256 verified; core controllers rolled out |
| Read-only repository authentication | PASS | Registered scoped deploy key; private Git revision fetched and rendered |
| CRD server-side validation | PASS | Application and project accepted by actual API |
| Initial adoption | PASS | Synced/Healthy at 8c5ef9f, one replica |
| Git-driven deployment | PASS | Commit 25dcd8c changed replicas 1 -> 2; automatically reconciled |
| Live drift and self-healing | PASS | Observed OutOfSync with 3 replicas, then Synced/Healthy at Git's 2 without a new Git revision |
| Git revert | PASS | Commit 6400f50 automatically restored one replica |
| HTTP/security after each stage | PASS | Real Service health, UID 10001, probes, resources, digest and security settings |
| Project isolation | PASS | Forbidden destination test returned InvalidSpecError with auto-sync disabled; test app removed |
| Manual Helm guard | PASS | Bootstrap refused to overwrite Argo-owned application |
| Argo server health | PASS | HTTPS /healthz returned 200/ok through temporary loopback forward |
| Browser admin login | NOT RUN | Admin password not read or printed |
| Local app tests / lint | PASS | 12 tests; existing Starlette/anyio warning remains |
| GitOps chart checks | PASS | Four profiles, 16 valid native resources, invalid input cases rejected |
| GitHub setup/change/revert CI | PASS | GitOps runs 40250659921, 40250732778, 40250770351 |
| Application GitHub CI | PASS | [Release 40251242073](https://github.com/prasanthece42/aegis-cicd/actions/runs/40251242073): source commit 64c86de |
| Private GHCR pull / production deployment | NOT RUN | Outside this local native-image integration |

The final application is Synced and Healthy with one replica. Its image remains:
`docker.io/library/aegis-sample@sha256:ca29d52da6d8bcf428b685b98941025deec79d90060772e909449a8795234f00`.
The receipt [phase-4-gitops.json](deployments/phase-4-gitops.json) records revisions,
observed states, ownership annotation, server health, and policy rejection.

Git change: `25dcd8c5a4543b4034791b3f300263b53f18f4c1`.
Git revert: `6400f50157d53f52eb5b59e18d308395a6d2294d`.
No manual Argo sync/refresh or Helm upgrade was used between the demonstration stages.

## Commands executed

```bash
export PATH="/tmp/aegis-phase3-bin:$PATH"
bash scripts/install-local-argocd.sh
bash scripts/register-argocd-repository.sh
bash scripts/connect-local-argocd.sh
bash scripts/verify-gitops-flow.sh
bash scripts/verify-local.sh
bash -n scripts/*.sh
```

Local checks also performed actual CRD server-side dry-runs, a loopback HTTPS
/healthz request, a temporary no-auto-sync forbidden-destination Application test,
a manual-Helm refusal test, and read-only inspection of Argo/deployment state.
The default AWS context remained unchanged; all application operations used the
isolated Kind kubeconfig/context. All temporary test Applications/forwards were removed.

## Resolved issues and limitations

The default Python 3.13 HTTPS trust store initially failed certificate verification
before installation. The installer now downloads through curl's working system trust
and still verifies the pinned manifest hash; TLS verification was not disabled.
Argo Dex restarted once during startup and was Ready at final inspection; all Argo
components were Ready. No failed rollout or reconciliation remained.

The deploy key is persistent and read-only, scoped to this repository. Its private
half is stored only in ignored local storage and the local repository Secret. Its
revocation procedure is documented. No account token/PAT or admin password was
copied into Git or printed. The upstream controller has cluster-level RBAC; AppProject
restrictions are application-level boundaries, not namespace-only controller RBAC.

This proves local DEV Git-driven reconciliation. Registry authentication, amd64/arm64
release integration, CI-to-GitOps image updates, production approvals, HA/SSO, and a
failed-image release rollback are not claimed. The replica revert demonstrates
configuration rollback. Stop after Phase 4; Phase 5 requires explicit approval.

## Final GitHub and runtime verification

[Application release 40251242073](https://github.com/prasanthece42/aegis-cicd/actions/runs/40251242073)
passed on source commit `64c86de7490e1b0dac7d8b24510ac481347924b4`. Checks/dependency scan
completed in 33 seconds, image validation in 58 seconds, and publication/digest
verification in 34 seconds. Its [release receipt](releases/40251242073.json) was
downloaded and all report checksums independently verified.

GitOps setup/change/revert runs passed:
[40250659921](https://github.com/prasanthece42/aegis-gitops/actions/runs/40250659921),
[40250732778](https://github.com/prasanthece42/aegis-gitops/actions/runs/40250732778),
and [40250770351](https://github.com/prasanthece42/aegis-gitops/actions/runs/40250770351).
The final evidence-only GitOps documentation commit `284e2ec274daadd612b64398ed5d375fed5d5ddc`
was also observed Synced/Healthy by Argo at one replica, with UID/security/HTTP checks passing.

```bash
git push origin main
gh run watch 40251242073 --repo prasanthece42/aegis-cicd --exit-status --interval 15
gh run download 40251242073 --repo prasanthece42/aegis-cicd --name release-evidence-40251242073-1 --dir /tmp/aegis-phase4-release-40251242073
```

The final report-only commit uses [skip ci] to record already completed validation;
no source-code change is hidden by that marker. Both repositories are pushed and
clean. There is no outstanding Phase 4 blocker. The local cluster and Argo remain
running for inspection; temporary port-forwards are closed. Phase 5 has not started.
