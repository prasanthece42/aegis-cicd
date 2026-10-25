# Phase 2 security policy

## Blocking policy

Trivy v0.76.1 scans the full resolved Python development dependency set (which
includes runtime packages) and the actual candidate image archive (OS and Python
packages). Full JSON reports contain every severity. A separate `trivy convert`
view exits 1 if any CRITICAL vulnerability is present, including unfixed findings.
HIGH, MEDIUM, LOW, and UNKNOWN findings are retained for review but do not block
this phase. This policy does not certify a vulnerability-free production release.

Download failures, stale-database update failures, malformed reports, or missing
application package inventory fail the job. We do not use continue-on-error,
ignore-unfixed, or CVE exceptions. Fix code/dependencies/base images and rerun.
Future policy exceptions must be explicit, reviewed, justified, and time-limited.

The initial Bookworm image failed with five CRITICAL findings. Switching to an
official Python 3.12.14 Debian Trixie image pinned by OCI index digest removed those
findings without suppression. Refresh that digest intentionally and rescan: pinning
prevents unnoticed changes, but does not automatically apply security patches.

## Trust boundaries and credentials

- Pull requests execute CI on GitHub-hosted runners with contents:read only.
- A push to main starts Release, which calls the same CI workflow. There is no
  pull_request_target or workflow_run path to privileged execution.
- Only Release's publish job receives packages:write. The validation jobs have no
  registry credential. Login occurs after validation and image identity checks.
- GHCR authentication uses the job's short-lived GITHUB_TOKEN, not a stored PAT.
  The login action logs out in its post-job cleanup.
- The validated candidate is passed using run/attempt-scoped Actions artifacts.
  It is not rebuilt for publication. Source labels and the scan's image config
  digest must match the loaded candidate.
- Workflow action references are pinned to verified commit SHAs; the official
  Trivy setup action also pins its nested action and installation-script references.
- Production branch protection still needs to be configured by the repository
  administrator. Direct writes to main are trusted by this design.

## Immutability and concurrency

Release tags are `sha-<full-commit>-<run-id>-<attempt>`; there is no latest tag.
Serialized releases and unique tags prevent normal runs overwriting one another.
GHCR tags remain mutable to a sufficiently privileged actor. Consumers must use
`ghcr.io/prasanthece42/aegis-cicd@sha256:<digest>` from release.json. A digest names
fixed content while that content is retained in the registry.

## Evidence and provenance limits

Retained evidence includes dependency/image JSON, a CycloneDX SBOM, source commit,
workflow URL, registry digest, image config digest, and SHA256 hashes of reports.
The workflow pulls by digest and runs an HTTP smoke test before creating release.json.
Partial reports may be retained after a failed job; only a successful workflow and
its verified release.json represent a completed release.

This is unsigned workflow evidence, not a signed provenance attestation or SLSA claim.
Docker archive transfer is used for a single-platform image; BuildKit attestations
are not preserved as a supported provenance mechanism in this path. GitHub's managed
attestations for private repositories require Enterprise Cloud. We do not change
repository visibility or publish private build details to a transparency log.

Reports expire after 14 days, candidate archives after 1 day, and release evidence
after 30 days. Download evidence for longer retention. No registry deletion policy
is automated yet. No GitOps authentication exists in Phase 2; use a short-lived,
narrowly installed GitHub App when the cross-repository integration is approved.

References: [Trivy Python coverage](https://trivy.dev/docs/latest/coverage/language/python/),
[Trivy image scanning](https://trivy.dev/docs/latest/target/container_image/),
[GHCR authentication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry),
[GitHub attestation availability](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations).
