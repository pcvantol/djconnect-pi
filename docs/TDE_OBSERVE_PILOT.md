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
`technical-debt-engine-runtime==1.1.1` distribution and invokes only its public
`tde` CLI. It does not check out TDE source, import TDE Python modules, alter
policies, or change the workflow's non-blocking behavior. The workflow first
generates the existing canonical coverage input by running the Pi test suite.

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

## Dependency-health reproducibility

`requirements.lock` is the canonical Python 3.11 dependency input for the Pi
runtime, tests and build. Its exact runtime, transitive, test and build-tool
pins are installed before the project is installed with `--no-deps`. The
release bundle includes the same file, and both the shell installer and
in-app updater consume it before installing the application wheel with
`--no-deps`.

With public runtime `1.1.1`, this provides the dependency-health adapter a
concrete `dependency_health.outdated_dependencies` measurement instead of the
former unavailable result caused by open direct constraints. This is evidence
collection only; OBSERVE behavior remains unchanged.

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

The RC3 qualification run is the first selected-consumer observation of the
public four-capability Runtime. It remains non-blocking, and any unavailable
coverage or dependency evidence is retained as canonical evidence rather than
replaced consumer-side. The objective exit criteria and the decision prerequisite for any WARN proposal are defined in
[TDE Observe Exit Criteria](TDE_OBSERVE_EXIT_CRITERIA.md).

## Public 1.0 release qualification

The hand-dispatched merged-main run
[30284607891](https://github.com/pcvantol/djconnect-pi/actions/runs/30284607891)
validated the publicly published, exact-pinned
`technical-debt-engine-runtime==1.0.0rc3` distribution. The immutable final
1.0 release bundle was later certified from TDE commit
`51497958cfcdcd2d273e97499234006bff3ba969` and published as the final public
release on 27 July 2026.

The non-blocking workflow and job succeeded in 15 seconds and retained
`tde-observe-evidence`. The standard profile executed `code_size`,
`complexity`, `coverage`, and `dependency_health`. The assessment decision was
`FAIL` and the repository qualification was `FAILED`; both CLI commands
returned exit code `2`, were retained as observation, and did not change the
successful workflow result. The observe step took three seconds.

The prior RC3 run confirms public-CLI consumer execution for all four 1.0
capabilities. This workflow update moves the same consumer contract to the
immutable final release; it remains non-blocking and does not promote WARN,
soft-fail, required checks, or a wider rollout.
