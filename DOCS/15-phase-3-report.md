# Phase 3 verification report

Date: October 25, 2026 (America/Halifax).

## Architecture and files

Application inputs are built/scanned natively, loaded into local Kind, and deployed
from the separate sibling aegis-gitops Helm chart. Only DEV runs. The explicit
.local/kubeconfig and kind-aegis-dev context isolate every operation from the existing
AWS context. Continuous reconciliation and Argo CD are not implemented yet.

Added application files: kind/cluster.yaml; kind-common.sh, bootstrap-local-k8s.sh,
verify-local-k8s.sh, verify-kind-recovery.sh, and teardown-local-k8s.sh under scripts;
DOCS/13 through DOCS/15 and a small deployment receipt. Updated CI to check Bash
syntax, .gitignore to exclude .local credentials/overrides, README, architecture,
and the configuration index.

The separate [aegis-gitops repository](https://github.com/prasanthece42/aegis-gitops)
is private and published; chart implementation commit `3a627f3` contains charts/sample-api with schema and
Deployment/Service/ServiceAccount templates, dev/staging/prod namespaces and values,
a static-validation GitHub workflow, validation script, README, and numbered guides.

## Acceptance checklist and results

| Check | Status | Evidence |
| --- | --- | --- |
| Python tests / Ruff | PASS | 12 tests; lint and formatting pass; existing upstream warning remains |
| Helm lint | PASS | All three environments; only optional chart-icon recommendation |
| Template/schema validation | PASS | 4 resources per environment, 12 valid total; zero invalid/errors/skipped |
| Invalid chart input tests | PASS | Empty digest, non-digest value, and zero replicas rejected |
| Workflow syntax | PASS | actionlint; ShellCheck unavailable |
| Local image security gate | PASS | Zero CRITICAL; remaining severities: {'LOW': 70, 'HIGH': 51, 'MEDIUM': 100, 'UNKNOWN': 4} |
| Kind creation | PASS | Kubernetes 1.35.8 node Ready; API bound to loopback |
| Server-side DEV validation | PASS | Deployment, Service, ServiceAccount accepted in restricted namespace |
| Helm install / rollout | PASS | sample-api chart 0.1.0; one desired/available replica |
| Live digest, security, probes, resources | PASS | Read live Deployment and verified required settings |
| Runtime UID | PASS | kubectl exec returned 10001 |
| HTTP through Service | PASS | Loopback port-forward to Service returned exact health JSON |
| Pod replacement | PASS | Deleted owned DEV pod; new UID/name, same image, Ready and HTTP healthy |
| Restricted Pod Security | PASS | Privileged Pod dry-run rejected by restricted:v1.35; no Pod created |
| AWS context preservation | PASS | Existing default context remains unchanged; application commands used explicit local context |
| STAGING / PROD installation | NOT RUN | Rendered only; outside local DEV scope |
| Private GHCR pull into Kind | NOT RUN | Local native image used; no GHCR registry credential created |
| Argo CD / Git reconciliation | NOT RUN | Phase 4 not authorized |
| GitOps GitHub CI | PASS | [Chart run 40249510939](https://github.com/prasanthece42/aegis-gitops/actions/runs/40249510939) |
| Application GitHub release | PASS | [Release run 40249322983](https://github.com/prasanthece42/aegis-cicd/actions/runs/40249322983); scans, GHCR publication, digest pull and smoke test |

Observed local image:

```text
docker.io/library/aegis-sample@sha256:ca29d52da6d8bcf428b685b98941025deec79d90060772e909449a8795234f00
```

Application source commit: `32952da316d443f514e6bc4aaa0b6f6fd693c520`. This is a distinct native
linux/arm64 build from committed app inputs, not the Phase 2 GHCR linux/amd64 image.
The generated override uses the actual manifest digest from Kind's containerd store
and imagePullPolicy Never. Tracked GitOps values retain the verified Phase 2 digest.

The replacement pod changed from `sample-api-5cd69bbffd-kcr9d` to `sample-api-5cd69bbffd-2pqs9`.
This demonstrates ReplicaSet replacement, not Git drift correction or high availability.
A single replica can be briefly unavailable during deletion.

## Commands executed

Official Kind 0.33.0, kubectl 1.35.8, and kubeconform 0.8.0 binaries were downloaded
to /tmp/aegis-phase3-bin and verified against official release checksums. Existing
Helm 4.2.4 and Trivy 0.76.1 were used.

```bash
export PATH="/tmp/aegis-phase3-bin:/tmp/aegis-phase2-bin:$PATH"
export TRIVY_CACHE_DIR=/tmp/aegis-trivy-cache
bash scripts/bootstrap-local-k8s.sh
bash scripts/verify-kind-recovery.sh
# From the GitOps checkout:
bash scripts/validate-chart.sh
```

Bootstrap ran app checks, Helm/schema checks, native Docker build/export, Trivy,
kind create cluster, kind load image-archive, explicit-context namespace apply,
server-side dry-run, Helm upgrade --install --wait --rollback-on-failure, rollout,
UID checks, and real HTTP verification. The namespace policy negative test used
kubectl apply --dry-run=server and checked the PodSecurity rejection message.

Read-only inspections confirmed the node version, Deployment/Pod/Service state,
Helm release status, and unchanged default Kubernetes context. Verification cleans
up its temporary port-forward; the DEV cluster remains running for inspection.
No teardown has been executed.

## Security and limitations

The namespace enforces Restricted Pod Security. The chart fixes non-root UID/GID,
RuntimeDefault seccomp, read-only root filesystem, dropped capabilities, disabled
privilege escalation and token mounting. Resource requests/limits and probe settings
are present. Namespace separation alone does not provide network isolation; no
NetworkPolicy or production availability claim is made.

Kubeconfig and local artifacts are gitignored. Registry tokens and cloud credentials
were not added. Direct GHCR pulls need architecture-compatible images and secure
registry access in a later integration step. All lower-severity scan findings remain
visible under the Phase 2 policy. Helm is being applied manually from the workstation;
CI does not deploy application resources. Argo CD will own reconciliation in Phase 4.

See [deployment receipt](deployments/phase-3-local.json) and
[learning/run guide](14-kubernetes-helm-guide.md). After Phase 3 publication and review,
the next recommended phase is local Argo CD, requiring explicit user approval.

## GitHub verification and publication

Application source commit `80df9c4e17f70466f69122506f6cb141260f2d20` passed the actual
[application release run 40249322983](https://github.com/prasanthece42/aegis-cicd/actions/runs/40249322983).
Jobs passed in 31s (checks/dependency scan), 46s (image build/test/scan), and 39s
(publication and digest verification). The release evidence was downloaded and its
checksums verified; [release receipt](releases/40249322983.json) records the new
published amd64 digest. This new release does not alter the running native local
image or automatically change the tracked GitOps environment digest.

After exact-destination approval, the private GitOps repository was created and
pushed. Source commit `be7ff7df5bd24770b2d55ede1c64cc9f46eff844` passed
[chart run 40249510939](https://github.com/prasanthece42/aegis-gitops/actions/runs/40249510939).
This executed static validation only, with no deployment credentials or cluster access.

```bash
git push origin main
gh repo create prasanthece42/aegis-gitops --private --source . --remote origin --push
gh run watch 40249322983 --repo prasanthece42/aegis-cicd --exit-status --interval 15
gh run watch 40249510939 --repo prasanthece42/aegis-gitops --exit-status --interval 10
gh run download 40249322983 --repo prasanthece42/aegis-cicd --name release-evidence-40249322983-1 --dir /tmp/aegis-phase3-release-40249322983
```

The last documentation-only updates use [skip ci] to record completed evidence
without rerunning publication solely for documentation. Both source commits tested
on GitHub are named above. No blocker remains for Phase 3. Phase 4 has not started.
