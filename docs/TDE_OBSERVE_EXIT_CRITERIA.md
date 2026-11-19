# DJConnect Pi TDE Observe Pilot — Exit Criteria

## Status and authority

This is the canonical, repository-local G2-D decision record for the
`djconnect-pi` TDE Observe pilot. It defines the evidence required to *propose*
a promotion from **OBSERVE** to **WARN**. It does not make that promotion.

The existing `TDE observe` workflow remains non-blocking. This record does not
authorize a change to the workflow, its runtime, profile, analyzers, policy,
schema, capabilities, or check configuration.

## Current factual observations

Only successful runs on merged `main` are used for this pilot baseline. Pull
request observations and local/preflight results are not counted.

| Run | Trigger | Workflow / job | Observe step | Assessment | Qualification | Runtime / profile | Capabilities | Assessment / repository qualification | TDE exits | Artifact |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| [29684757770](https://github.com/pcvantol/djconnect-pi/actions/runs/29684757770) | push to `main` | success / success | 3 s | 896 ms | 1,100 ms | `0.2.0` / `standard` | `code_size`, `complexity` | `FAIL` / `FAILED` | `2` / `2` | present and inspected |
| [29685625820](https://github.com/pcvantol/djconnect-pi/actions/runs/29685625820) | manual dispatch on `main` | success / success | 2 s | 892 ms | 1,120 ms | `0.2.0` / `standard` | `code_size`, `complexity` | `FAIL` / `FAILED` | `2` / `2` | present and inspected |

The two observations use the same merged SHA,
`65e1d054b104480edd92d3ab8f6afd431c369286`. Their runtime, profile,
capabilities, assessment decision, repository-qualification status, and TDE
exit codes match. The assessment evidence and qualification evidence have the
same substantive policy results. The observed timing differences are 4 ms for
assessment and 20 ms for qualification; the observe-step duration differs by
one second.

No false positive has been classified. `FAIL` is a policy outcome, not a false
positive classification. The observed non-zero exits are retained as evidence;
the job succeeds because OBSERVE deliberately records rather than propagates
them.

## Known release and profile limitation

The exact published runtime is `technical-debt-engine-runtime==0.2.0`. Its
current `standard` profile executes `code_size` and `complexity` for this
pilot. It does **not** execute coverage or dependency health. No consumer-side
substitute is present or permitted by this pilot.

Before any WARN promotion, product governance must explicitly decide whether a
warning limited to `code_size` and `complexity`, without coverage or dependency
health, is acceptable for this consumer. This record neither makes nor implies
that decision.

## Proposed Observe exit criteria

All criteria below must be met without an unresolved interruption. They are
future requirements, not claims about the current two-run baseline.

### 1. Stable successful-main sequence

- Collect at least **10 consecutive successful** `TDE observe` runs on merged
  `main`.
- The sequence must span at least **14 calendar days**, measured from the
  first qualifying successful-main run to the tenth or later qualifying run.
- A manual `workflow_dispatch` run on `main` may count when it assesses the
  then-current merged `main` SHA. A pull-request run, rerun of an older SHA, or
  a local invocation may not count.

### 2. Required artifact completeness

Every qualifying run must retain a downloadable, non-expired
`tde-observe-evidence` artifact containing:

- `tde-observe/assessment.json`, `qualification.json`, `summary.md`, and
  `runtime-version.txt`;
- immutable assessment evidence under `.tde/evidence/`;
- immutable repository-qualification evidence under `.tde/qualifications/`;
- a parseable summary that records runtime, profile, capabilities, assessment
  decision, qualification status, both TDE exit codes, duration, and artifact
  name.

Missing, unreadable, malformed, or internally inconsistent evidence is not a
qualifying run.

### 3. Runtime, profile, and capability consistency

Each qualifying run must use exactly the currently observed execution shape:

- runtime `technical-debt-engine-runtime==0.2.0` (CLI/runtime version `0.2.0`);
- assessment profile `standard`, profile version `1.0.0`, and profile hash
  `sha256:2e1f6f00b807ac2c6bb9227ab0f992102e5a0398cc564cfbbd27307607a118c8`;
- capabilities exactly `code_size` and `complexity`, both `VALID` and
  `QUALIFIED` at capability level;
- analyzer bindings `cloc 2.10` and `radon 6.0.1`.

No runtime, profile, capability, analyzer, policy, or schema variation is
allowed within the sequence. Any such variation starts a new observation
sequence after it is independently documented and reviewed; it is not silently
compared with the current baseline.

### 4. Operational timing envelope

The current baseline is an observe step of 2–3 seconds, assessment of
892–896 ms, and qualification of 1,100–1,120 ms. For the proposed sequence,
each qualifying run must remain within these operational ceilings:

- observe step: **10 seconds** or less;
- assessment: **2,000 ms** or less;
- qualification: **2,000 ms** or less;
- complete `TDE observe (non-blocking)` job: **30 seconds** or less.

These are pilot stability limits, not a performance commitment for a future
runtime or profile.

### 5. Policy outcomes, exits, and false positives

For this observed baseline, assessment `FAIL`, repository qualification
`FAILED`, and assessment/qualification exit codes `2`/`2` are expected policy
evidence. They do not by themselves break the sequence, provided the workflow
and job succeed, the artifact is complete, and the policy results remain
substantively unchanged.

A false positive is a specific policy result that is demonstrated to be wrong
for the assessed merged source, rather than merely inconvenient. Its record
must identify the rule, affected evidence, reproduction, source-grounded
reason, and an explicit maintainer-and-governance disposition. An unclassified
`FAIL`, including the current result, is not a false positive and must not be
suppressed or relabelled.

### 6. Stability-sequence interruptions

The sequence is interrupted by any of the following:

- a workflow or observe job that does not conclude `success`, including a
  cancellation or timeout;
- missing or incomplete required evidence;
- a runtime, profile, capability, analyzer, policy, or schema variation;
- a timing ceiling breach;
- a changed assessment decision, repository-qualification status, or TDE exit
  code; the cause must be documented before a new sequence begins;
- an unresolved false-positive claim or artifact-integrity concern.

After an interruption, a new ten-run, fourteen-day sequence begins only after
the cause and any required governance decision are recorded.

## Promotion decision rule: OBSERVE to WARN

A WARN promotion may be proposed only when all exit criteria are met and the
following explicit decision is recorded by the responsible product and
engineering governance:

1. the complete stable-main evidence set is accepted;
2. every false-positive disposition is accepted, with no unresolved claim;
3. governance explicitly accepts or declines a warning whose published
   `standard` profile omits coverage and dependency health; and
4. governance explicitly accepts the semantics of surfacing the currently
   observed `FAIL`/`FAILED` outcomes as WARN rather than treating them as a
   merge blocker.

Until that decision exists, the required action is to remain in OBSERVE.

## Explicitly excluded promotions

This pilot authorizes neither a soft-fail nor a required check. Satisfying the
Observe exit criteria can support only a separate proposal for **WARN**. A
soft-fail or required-check proposal needs its own later decision record,
evidence period, and authorization; neither follows automatically from a WARN
decision.
