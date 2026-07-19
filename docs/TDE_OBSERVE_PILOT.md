# TDE Production Pilot — Phase 1 (Observe)

## Pilot selection

`djconnect-pi` is the first selected DJConnect consumer because it is an active
Python/pip repository with an existing GitHub Actions validation pipeline and
a retained Cobertura coverage artifact. It is a small, practical first shape
for the public Python/Radon analysis path and the pip dependency ecosystem
already established by Generation 2. This is one deliberately bounded pilot,
not a platform-wide rollout.

## Observe-mode contract

The `TDE observe` workflow installs the published, exact-pinned
`technical-debt-engine-runtime==0.2.0` distribution and invokes only its public
`tde` CLI. It does not check out TDE source, import TDE Python modules, run this
repository's tests, alter policies, or change any existing workflow.

The workflow runs the installed `standard` profile and then creates a separate
repository qualification with the consumer definition in
`.github/tde/repository-definition.json`. It publishes the CLI JSON output,
immutable assessment evidence, qualification evidence, runtime version, and a
short execution summary in the `tde-observe-evidence` artifact. There is no
baseline before the first observation, so this phase intentionally produces no
differential evidence.

TDE exit codes are recorded in the artifact and workflow summary but are not
propagated to the job. The observe job always succeeds and is not configured as
a required check, warning gate, soft fail, or merge blocker.

## Initial operational observations

The preflight used the public PyPI distribution, not a source checkout. At the
time of this pilot branch, `0.2.0` is the newest published version. Its bundled
`standard` profile executed `code_size` and `complexity` successfully against
this repository. The published release does not register `coverage`; an
explicit `coverage` request returned `NOT_SUPPORTED`. This is recorded as an
observed release limitation, not hidden by a consumer-side workaround.

The first GitHub Actions run is the source for CI duration, stability,
reproducibility, false-positive, and operational findings. Those results must
be added here only after they are observed from the retained
`tde-observe-evidence` artifact. No average, failure rate, or false-positive
claim is made before that evidence exists.
