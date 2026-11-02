# rc.7 scheduling hold component: bounded qualification

This is a non-integrated **hold-only** component, not the matching V4 consumer
or an installation permission. Protected Core Source1417/d8525117 and separate
Final1418/6a1403a9 were independently read and accepted by the unchanged canonical
status validator. All three normative V3/V4 hashes match the owning handoff.

`Tools/pi_rc7_guard.py` captures eight existing units, reserves a durable exclusive
manifest/instance namespace before guard writes, and installs four persistent
root-owned service conditions. Actual loaded policy, lifecycle hooks, boot,
fragment bytes and guard inode/content are checked. Timers are stopped under
the loaded service conditions; already running oneshots must be drained with
zero PIDs and an empty descendant cgroup. A controlled SIGTERM terminal state
requires the same observed invocation and exact termination cause. Initial
failed/absent/foreign states reject. No failure is reset in production code.

Independent review found two P1 concerns in the initial prototype: stop-post
effects despite condition skipping, and partial persistent guard removal during
restore. Lifecycle hooks are now rejected/cleared; production removal is absent.
`restore()` always rejects without invoking a callback or changing scheduling.
The same reviewer grants bounded hold-only source GO, not a release or consumer GO.

Final qualification:123 targeted cases PASS in the existing DebianARM64 VM.
Actual Linux PID1/systemd257 qualification uses eight disposable benign fixture
units: missing-unit and stop-post rejection before claim, actual invocation/cgroup
drain, real condition exit1 rather than CLI exit0 inference, hostile unit copy/
daemon-reload/timer re-enable with no fixture effect, and same-grant replay
rejection. Original disabled/inactive scheduling is captured, **not restored**.
Fixture disposal is a separate owning harness, never shipping restore behavior.
No real VM app, HA, provider or physical Pi action is part of these tests.

All failed/intermediate harnesses, raw actual systemd shape probes, review
findings and final logs are retained under external own evidence
`pi-rc7-consumer-20261102`. Empty ExecCondition arrays may be omitted by systemctl;
only known empty command-array fields are normalized. A timer reference retains
actual skip details that PID1 can otherwise garbage-collect. Output limits are
checked after subprocess capture; no streaming-output memory bound is claimed.
Ruff0.17.3 --no-cache and diff checks pass. No new full-suite/QML claim is made.

The required persistent all-unit release-commit/final-state contract remains
open in [the existing producer handoff](https://github.com/pcvantol/djconnect-pi/pull/136#issuecomment-6573838284).
Original scheduler restoration, complete native/provenance/backup/installer/smoke
wiring, protected matching-consumer Source/Final and fresh exact operative
binding remain required. No V4 manifest is synthesized, rc.6 grant reused,
workflow dispatched, published rc.7 asset replaced or physical Pi accessed.
