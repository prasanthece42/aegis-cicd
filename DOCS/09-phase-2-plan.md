# Phase 2 implementation plan and acceptance checklist

Scope: security gates, GHCR publication, immutable references, and release evidence.
No GitOps updates, deployment, environments, or AWS resources in this phase.

1. Update verified action SHA pins and pin the Python base image by digest.
2. Add dependency and container vulnerability scanning with Trivy v0.76.1.
3. Reuse the CI workflow for trusted releases; transfer the validated candidate
   through a run-scoped Actions artifact rather than rebuilding after scanning.
4. Publish only on main with the short-lived GITHUB_TOKEN and packages:write in
   the publishing job alone. Use unique sha/commit/run/attempt tags; serialize releases.
5. Resolve the registry digest, pull by that reference, compare image config IDs,
   and smoke-test the pulled image.
6. Retain full vulnerability reports, CycloneDX SBOM, and unsigned release metadata.
7. Run local gates, verify a deliberately vulnerable fixture is rejected, and test
   the actual GitHub release. Record blockers and evidence before stopping.

Acceptance status is recorded in DOCS/12-phase-2-report.md after validation.

- [x] Dependency and image scans execute with nonempty package inventories.
- [x] All CRITICAL vulnerabilities fail the gate, including unfixed findings.
- [ ] Scanner/download errors fail closed; scan reports are retained on failure.
- [x] Candidate smoke test passes before publication.
- [x] PR jobs have no packages:write and cannot publish.
- [x] SHA-pinned actions and digest-pinned base image validate.
- [ ] Registry push succeeds for the validated candidate.
- [ ] Digest-pulled image matches the candidate config and passes HTTP checks.
- [ ] Release JSON and SBOM retained with workflow/source traceability.
- [ ] Local and GitHub results documented without claiming signed attestations.

Local checks pass. Registry publication and GitHub execution remain blocked pending
explicit user approval for `ghcr.io/prasanthece42/aegis-cicd`. See DOCS/12.
