# Phase 1 learning notes

We built a small, real HTTP service and an automated quality gate. The service is
our delivery workload: it lets us prove that changes pass checks and still run
inside the image that later phases will publish and deploy.

In an enterprise, developers open pull requests and reviewers require CI checks
before merging. Lint catches mechanical issues early. Tests check behavior. Building
an image catches packaging errors. Starting the image catches problems such as an
incorrect command, missing dependency, wrong user permissions, or closed port.
These checks answer different questions; a passing unit test alone cannot prove
that a container starts.

The dependency inputs name direct packages. The generated locks name the full
resolved dependency graph and allowed artifact hashes. The builder installs those
packages; the runtime image excludes Pytest and Ruff. Running as a non-root user
limits what a compromised process can modify. Neither hashes nor non-root execution
replace vulnerability scanning, which is the next phase.

GitHub Actions schedules isolated jobs. `needs: checks` establishes a dependency:
Docker work starts only if quality checks pass. `contents: read` lets checkout read
source without granting repository write access. A commit SHA identifies the code
being tested; a registry digest will later identify exact image bytes.

## Interview practice

| Question | Answer |
| --- | --- |
| What is CI? | Automatically integrating and checking each change so problems surface before release. |
| Why build after tests? | A failed quality gate should block creating a candidate image and avoid wasted build work. |
| Why test the container too? | Source tests cannot detect every packaging or runtime configuration error. |
| Why a multi-stage Dockerfile? | Keep dependency installation work separate from the final runtime and control what gets copied. |
| Why avoid root? | Reduce the privileges available if the application is compromised. |
| Is a SHA tag immutable? | It names a commit by convention, but a registry tag can be reassigned; deploy by digest later. |
| What if a stage fails? | That job fails; dependent jobs skip. Inspect its first failing step, reproduce locally, fix, and rerun. |
| CI versus CD? | CI validates changes; CD delivers validated artifacts. Phase 1 implements CI only. |
| Why separate source and GitOps repositories? | Application changes and deployment desired state have different permissions and review lifecycles. |
