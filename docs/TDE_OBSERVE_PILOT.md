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

The first successful CI observation is [run 29684373080](https://github.com/pcvantol/djconnect-pi/actions/runs/29684373080).
It completed the `TDE observe (non-blocking)` job in 13 seconds. Its retained
summary records a three-second observe step; the assessment took 983 ms and
the separate qualification took 1,136 ms. With one successful sample, that
sample is the only available average; a stable multi-run average has not yet
been observed.

The published artifact contains two immutable assessment-evidence records, one
repository-qualification record, the CLI JSON outputs, runtime version, and
workflow summary. The assessment executed `code_size` and `complexity`; its
policy decision was `FAIL`, while runtime qualification was `QUALIFIED`.
Repository qualification was `FAILED` because it preserves the policy decision.
Both public CLI exit codes were `2`, were retained in the artifact, and did not
change the successful workflow outcome.

The first attempt exposed an operational incompatibility: Ubuntu's package
manager supplied `cloc 1.98`, while the public runtime requires `cloc 2.10+`.
The workflow now provisions the checksum-verified upstream `cloc 2.10` release;
the successful run above confirms that correction. No false positives have
been classified in this one-run observation. The concrete missing capability is
the published `0.2.0` profile's absence of coverage and dependency-health
execution; no consumer-side substitute has been added.
