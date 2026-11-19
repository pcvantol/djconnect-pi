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
Source121/Final122 qualified the recovery components only. Core subsequently
closed admission under a distinct schema4 producer contract. The explicit
consumer described below supersedes the earlier V3 admission proposal; V3
consumer/manifest prose is never sufficient recovery authority.

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
before any watchdog or installer mutation. It synchronizes the potentially new
parent directory entry, claim file data/metadata, claim entry and ledger entry
with four checked fsync calls before hold/install. Every synchronization failure
propagates before effects; no retry, claim deletion or rearm occurs. The helper
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
source, all80 files, restored watchdog and preserved configuration. The dedicated
separate read-only recovery smoke accepts only the exact new typed recovery
receipt and its successful first-attempt workflow. Original failed evidence is never promoted.
Aggregation includes recoveries in physical intent ordering but keeps exact
consumer/manifest joins; no cross-consumer carry-forward or overall PASS.

## Qualification

202 added cases;528 directed locked-tool PASS3.75s. FULL2763 integrated PASS/no
skips45.53s; Ruff0.16 src/tests and changed deployment tools PASS; diff PASS.
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

## Independent review P1: crash-durable claim

Exact6d7233d review found missing durable claim writes. That candidate is blocked,
not given GO and never executed on a device. Exclusive mkdir alone did not ensure
the claim or containing directory entries survived a crash. The corrected claim
fsyncs parent.parent, flushed/fchmod0600 claim file, ledger and parent, in that
order before returning to hold/install. Linux requires explicit directory fsync
in addition to the file: https://man7.org/linux/man-pages/man2/fsync.2.html.
Ten new cases cover existing/new parent and success/all four sync failures. All
ten fail against the original unmodified claim AST; the corrected cases PASS.
No functional/security assertions were relaxed. Helper bytes are re-pinned at
all three joins. Earlier192/518/2753 results remain historical component proof;
final202/528/2763 totals above replace rather than add them. This is source/test
evidence, not a simulated crash/powerloss/hardware durability acceptance result.
Exact new independent review is required; the old OwnerAuth/CI is not reused.

## Explicit closed producer adoption

Core source265f151293735cddcf2e496e6c822f16c7cd2064 and distinct Final
c8549876df54e22b71ed26fcded4ec822b3d166d supply the byte-pinned
pi-rc6-wall4-recovery-v1 contract and two schemas, vendored separately. Source and
Final raw canonical receipts were independently checked; Final normative bytes
match source. An initial source-run HTTP404 is retained as availability evidence;
the actual original downloaded source raw receipt was checked from its owner's
retained copy, not reconstructed. The old16 producer files/inventory stay intact.

New authority uses only schema4 / platform_release_recovery_operational_manifest
at fixed PLATFORM_4_0_RC6_PI_WALL4_RECOVERY_MANIFEST.json and the dedicated closed
configuration pair PI_RC6_WALL4_RECOVERY_CORE_SHA plus
PI_RC6_WALL4_RECOVERY_MANIFEST_SHA256. No old/partial/mixed pair or path fallback.
Exactly one original wall-4inch artifact and target; original publication and
later protected matching consumer are independently qualified. JSON duplicate
keys, nonfinite values including exponent overflow, invalid timezone-aware
timestamps and unknown fields fail closed. The helper remains exact11ce41115c7a.

Recover and distinct smoke-rc6-wall4-recovery.yml use their own trusted entrypoint,
exact main checkout/actor/workflow/attempt1 and the shared physical mutation
serialization key. Latest physical intent includes normal deploy, normal smoke,
recovery and recovery smoke, including newer queued attempts and later updates.
Ordinary V3 CLI, smoke joins and aggregate reject recovery authority. Recovery
smoke never calls aggregate or emits overall DEPLOYMENT_OPERATIONAL; Pi10's old
success remains separate.

A new fixed hash-pinned read-only observer joins the whole private configuration
and current boot before/after recovery and again during separate recovery smoke.
Its fixed paths are the original /opt/djconnect/config/client.json, device profile
and kernel boot identity. The root code only reads; it never writes configuration,
services, installer, ledger or credentials. Its wrapper is staged at a fresh fixed
Pi-owned install-pattern location. Exact sudo -n -l -- command/boot authorization
must succeed before a single observer execution through the pre-existing narrow
rule; no sudoers/root-grant expansion or fallback. Only opaque digest plus boot
enter authenticated operational artifacts, never public status/docs. Separate
smoke also verifies the watchdog timer enabled/active and no loaded hold condition.

187 added cases;715 directed PASS4.47s. FULL2950 integrated PASS/no skips45.68s,
including existing authorized loopback fixtures. Restricted run2937PASS/13SKIP
is separate, not the full qualification. Ruff0.16 src/tests/changed tools, three
workflow YAML/actual Bash blocks and diff checks PASS. All80 runtime files,
original installer and runtime lock remain byte-identical to0dde. No new Qt/GPU,
installed/click/Spotify/audio claim. On the actual Zero2W Python3.13.5/aarch64,
helper/remote/observer compile in RAM only; no candidate execution/file write.

Diagnostics remain external: initial missing observer config path was corrected
by inspection before qualification; obsolete V3-positive fixtures were moved to
the explicit controller with assertions retained; one negative hash accidentally
equaled its original fixture and was corrected; missing deepcopy import failed
five fixture cases before correction. JSON exponent overflow was caught during
inspection and explicitly rejected, without altering the pinned root helper.
Earlier112/640/intermediate runs are not added to final715. Source/independent
review/protected separate Final and a new separately protected Core operative
binding are still required before any real recovery. The new pair is not set and
no recovery/smoke has been dispatched as part of this source qualification.


## V2 adoption after actual first recovery failure

Actual first recovery39695635601 on protected V1 consumer77fc4047 remains
FAILED/RECOVERY_INCONCLUSIVE with intent_dispatched:true and
remote_may_still_be_running:true. Original artifact12391115673 / raw SHA
ce97876b008d4417ec08100066aa38abf87dd57ae8398ae5e64de97d442744ec is preserved
byte-for-byte. No claim/ledger/guard is reset and no old run is retried.

The actual watchdog timer has three systemd properties without MainPID. The old
helper requires four for every unit; exact-method replay proves this blocking
compatibility condition, not the earliest actual failure guard. New helper
c395af61f47c42633c65013d61853c66c442781832ed4225d035d9209e9f0be2 accepts exactly
three timer fields and four service fields with numeric MainPID, rejects unknown
units/fields/duplicates/malformed lines, and limits private failure output to
reviewed static codes. Existing claim, four fsyncs, hold, installer, config and
restoration code is unchanged. Independent Core component review covers c395;
new whole-consumer review is still required.

Core V2 source5cf78c1c83936cc9ed2feb750f83cf743b643b90 plus separate Final
659bfe752dff0dcdcdbfc475be52bdf69090e085 were independently qualified via actual
canonical raw39699015746/39700346580. All three API/Git-blob exports match both
pins and are separately vendored; V1 normative bytes remain untouched.
V2 uses schema5, a new fixed PLATFORM_4_0_RC6_PI_WALL4_RECOVERY_V2_MANIFEST.json
path and only PI_RC6_WALL4_RECOVERY_V2_CORE_SHA plus
PI_RC6_WALL4_RECOVERY_V2_MANIFEST_SHA256. Old normal/V1 pairs are unchanged.
No approved V2 operative binding is created by this consumer source.

Both original deployment and actual previous recovery are independently joined
before prepare/send/smoke: exact trusted run/actor/main/attempt1, fixed artifact
ID/name/bounded ZIP/member/raw digest, actual public provenance and exact five
historical code objects at77fc. No nonexistent kind/schema/helper/input fields
are fabricated in the old raw. Helper11ce and deployment/execute transport
literals instead join through the byte-pinned historical code/schema chain.
Nested receipt equality distinguishes bools from integers. A missing original
artifact fails closed. All four physical intent lists still withdraw stale work.

Observer4ae5 remains byte-identical: boot plus opaque whole-private-config digest,
no added claim/process/root-read route. Root itself must pass current readiness
and exclusive durable claim before effects; no historical absence observation is
a current execution grant. Exact V2 recovery smoke requires the same new run,
consumer, operative pair, helper, observer, original/previous failure and current
boot/config. It never upgrades Pi10's earlier smoke or yields overall PASS.

Source tests are synthetic transport/effects and actual retained OS-shape bytes;
no new root execution, device recovery, installed smoke, touch or Spotify result.
Runtime80 files, original installer and lock remain byte-identical to published
0dde; no runtime republishing or rc.6 asset overwrite. New source and separate
Final qualification must precede a distinct protected Core V2 operative binding,
then current human/readiness/no-replay assessment, one owning intent and separate
smoke. Standing human recovery scope is22:39:09Z21Oct in this same chat; source
or new hashes do not manufacture new device authority. Automation stays PAUSED.

Final V2 source qualification:165 new cases,880 directed PASS;FULL3115 PASS/no
skips45.73s. Ruff0.16 src/tests/tools and three YAML/actual Bash blocks PASS.
