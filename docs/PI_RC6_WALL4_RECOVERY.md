# Bounded rc.6 wall-4inch recovery

## Actual failure and authorization

The original wall-4inch deployment39669504016 is FAILED / DEPLOYMENT_INCONCLUSIVE.
Its immutable historical evidence is retained: a dispatched installer could have
continued after relay loss. Subsequent actual installer and watchdog logs show
that the existing watchdog rebooted while the installer had intentionally stopped
the client. The published rc.6 release is selected, API active, client disabled
and inactive. This is not a completed installation.

Peter explicitly selected qualification and execution of this bounded recovery
in this same chat. Source approval, separate Finalization and a new qualified Core
operative binding remain mandatory. The original rc.6 binding is not reused.
Existing contractV2 semanticjoin5 and manifestV3 consumer.source_sha permit the
original publication source and new qualified consumer to differ; no new wire
field or producer schema is introduced here.

Pi10 deployment39669510052 and separate smoke39670779250 already passed with the
published rc.6 source. Its success remains separate: do not reinstall Pi10 and do
not carry its old consumer/manifest evidence into a new overall PASS.

## Closed execution

The dedicated recover-rc6-wall4.yml allows only wall-4inch / pi-zero-2w-arm64.
It retains the same physical mutation concurrency key and normal canonical
preflight, source/current authority, strict SSH identity/key/configuration and
attempt1 checks. The exact old failed run and bounded artifact receipt must
remain available, unmodified and match. The newest physical deploy or recovery
intent wins, including queued or inconclusive attempts; no replay or fallback.

Publication source is0dde0abe22a0859f170a7c1d3eab41f1ade44d37. The original profile
archive d67869ffca53c4936059bdbbdbdf6be63b36eafac269fa2f3f9b090922cd0d64,
installer712474d158524903542588ba513801b7953df625c0c8fc26710706a6655e37cc
and80-file wheel0f238c4e978ad7b84684e5934761d5391fb1040016371b5b9204039f6ea7a18a
remain unchanged. No republishing or runtime-source change is part of recovery.
The helper is hash-pinned independently by controller, remote staging and smoke
receipt validation; edited helper bytes cannot be staged.

Root preflight binds the exact physical device, boot, release symlink, all80
installed files, original staging/markers, whole private configuration digest,
unit bytes/policies, absent competing installer/shutdown and current failed-state
services. Fresh boot is joined across the checked SSH channel and privileged
preflight. No endpoint, path or command is supplied by a caller.

A persistent root-private exclusive claim under /var/lib burns this one recovery
before any watchdog or installer mutation, even on timeout/failure. The helper
stops the existing watchdog service/timer and adds only its own runtime service
drop-in with ExecCondition=/usr/bin/false. It verifies PID1 actually loaded this
condition and that no success/failure/shutdown hooks apply. A runtime unit mask
would be shadowed by the existing /etc unit and is deliberately not used.
The installer may re-enable the timer; the loaded condition still suppresses its
watchdog command. Original published installer/artifact are sealed in root-private
/run staging, then invoked once, without dependency/OS repair or config override.

Only proven stable new API/client PIDs, exact80 files, unchanged configuration
and boot allow removal of this exact own runtime drop-in and restoration of the
original enabled watchdog timer. Foreign files, replaced inode/content or unit
policy changes prevent removal. Failure never claims cancellation or success,
never auto-rearms the root claim and never blindly removes the guard; actual
state review is required. Runtime guard is ephemeral across a reboot, so a lost
connection must not be treated as proof that a hold remains active.

A new RECOVERED_PENDING_SMOKE receipt binds original and new run, helper bytes,
source, all80 files, restored watchdog and preserved configuration. The existing
separate read-only smoke accepts only this exact typed recovery receipt and its
successful first-attempt workflow. Original failed evidence is never promoted.
Aggregation includes recoveries in physical intent ordering but keeps exact
consumer/manifest joins; no cross-consumer carry-forward or overall PASS.

## Qualification

192 added cases;518 directed locked-tool PASS4.28s. FULL2753 integrated PASS/no
skips47.08s; Ruff0.16 src/tests and changed deployment tools PASS; diff PASS.
Two changed YAML files parsed and their actual Bash run blocks pass bash -n.
Tests include real local SSH pipes with intercepted effects, actual shell syntax
of the staged wrapper, one-claim race, boot/context/identity/authority withdrawal,
original receipt/archive rejection, root guard ownership, private staging and
whole-config checks, lost acknowledgements and late/replayed recovery ordering.
No root/systemd/device/HA/provider/model action occurs in these tests. All80 runtime
files remain identical to the published source. No new Qt, ARM, installed, touch,
Spotify or audible acceptance is claimed for this tooling-only change.

Diagnostics are retained separately under taskvisualizations/pi-rc6-recovery-consumer.
The first new real-pipe fixture used an invented wheel filename and was correctly
rejected by the unchanged closed remote payload; corrected to the actual wheel
name. Initial lint import/with style findings and a sandbox pytest cache-write
warning are retained. Earlier root fixture diagnostics and runtime-mask draft
were never device executions. Python lacks PyYAML; existing Ruby Psych parsed
YAML without installing dependencies. Earlier test runs are intermediate, not
added to these final totals. Deployment is still pending exact independent review,
protected source/Finalization and new protected Core operative binding.
