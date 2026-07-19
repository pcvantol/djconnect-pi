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

## Current merged-main observations

The baseline deliberately uses only successful observations on merged `main`:
[29684757770](https://github.com/pcvantol/djconnect-pi/actions/runs/29684757770)
and [29685625820](https://github.com/pcvantol/djconnect-pi/actions/runs/29685625820).
They assessed the same merged SHA. Both workflows and non-blocking jobs
succeeded, retained the `tde-observe-evidence` artifact, and used
`technical-debt-engine-runtime==0.2.0` with the `standard` profile.

Each assessment executed `code_size` and `complexity`, returned `FAIL`, and
its repository qualification returned `FAILED`. Both public CLI commands
returned exit code `2`; those exits were retained as observations and did not
change the successful workflow outcome. The observe steps took three and two
seconds, the assessments took 896 ms and 892 ms, and the qualifications took
1,100 ms and 1,120 ms.

The published artifact contains CLI JSON outputs, runtime version, a workflow
summary, immutable assessment evidence, and repository-qualification evidence.
No false positive has been classified from the merged-main evidence.

The concrete release limitation remains that the published `0.2.0` `standard`
profile executes `code_size` and `complexity`, but no coverage or dependency
health. No consumer-side substitute has been added. The objective exit criteria
and the decision prerequisite for any WARN proposal are defined in
[TDE Observe Exit Criteria](TDE_OBSERVE_EXIT_CRITERIA.md).
