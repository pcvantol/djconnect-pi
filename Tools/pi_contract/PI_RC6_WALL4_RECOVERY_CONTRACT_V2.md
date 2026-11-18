# Pi rc.6 wall-4inch recovery contract V2 — Timer OS-shape compatibility

Version:2. Producer:DJConnect Core. Contract ID `pi-rc6-wall4-recovery-v2`.
This is a separate closed revision for the same selected wall4/Zero recovery,
not permission to repeat a failed run, reset a claim, expand privileges or widen
targets. All prior V1 producer/operative bytes and actual failure evidence stay
unchanged. Pi owns new explicit adoption and current per-instance authority.

## Concrete compatibility finding, exact bounded helper

The original helper `11ce41115c7aa5ac34e568f3ea9008915f342bc3272850b56c61eed19a760ab9` requires MainPID for every unit.
Root independently read actual retained systemctl property bytes: the three
fixed service responses include MainPID; the fixed watchdog timer has only
LoadState/ActiveState/UnitFileState. Exact-method offline replay with a fake
command edge proves old3servicePASS/TimerRECOVERY_UNIT_INVALID. The corrected
helper `c395af61f47c42633c65013d61853c66c442781832ed4225d035d9209e9f0be2` accepts exactly those three timer fields,
requires all four service fields plus a numeric MainPID, rejects unknown units,
unknown/duplicate/malformed lines and never synthesizes a timer PID. Its only
other change is a finite reviewed private diagnostic-code allowlist with generic
fallback. Complete claim/fsync/hold/installer/config/restore logic is unchanged.
All64 new test bodies/runner and actual owning176PASS0.21s evidence were read;
Root independently executed only the exact unit AST over actual retained raw
metadata, no Root main/prepare/subprocess/SSH/installer/device operation.
This proves a necessary blocking compatibility condition, NOT the independently
unproven earliest guard in the actual failed recovery and NOT physical success.

## New machine-closed version and path

Use [request V2](PI_RC6_WALL4_RECOVERY_REQUEST_V2.schema.json) and
[manifest V2](PI_RC6_WALL4_RECOVERY_MANIFEST_V2.schema.json), JSON Schema2020-12.
New manifest schema_version5, unchanged recovery kind, contractIdV2 and explicit
`release-4.0.0-rc.6-pi-wall4-recovery-v2-` manifest-ID prefix. The fixed path is
`docs/release/PLATFORM_4_0_RC6_PI_WALL4_RECOVERY_V2_MANIFEST.json`.
This producer preparation DOES NOT create that file, an APPROVED example or any
future consumer placeholder. Dedicated NEW public Pi-owned indirection is
`PI_RC6_WALL4_RECOVERY_V2_CORE_SHA` plus
`PI_RC6_WALL4_RECOVERY_V2_MANIFEST_SHA256`. OldV1 pair2945/de22 stays untouched.
No V1/V3/ordinary fallback, alternate path, mixed pair/helper/observer/consumer,
caller host/path/user/port override or auto-selection from latest is allowed.

Existing dedicated `.github/workflows/recover-rc6-wall4.yml` and separate
`.github/workflows/smoke-rc6-wall4-recovery.yml` may remain, only after qualified
consumer V2 explicitly enforces this version/path/pair. Twelve request inputs
retain actiondeployment/execution_modeexecute transport meaning; those literals
are never permission for ordinary deployment. Latest physical intent includes
all four deploy/recover/ordinary-smoke/recovery-smoke lists including queued or
newer runs. Exact main/actor/attempt1/workflow/consumer/provenance joins apply
before/after awaits and effects. Smoke contract is
`pi-rc6-wall4-recovery-readback-v2`; no old smoke or cross-consumer carry-forward.

Exactly one unchanged inventory target: rbpi-djconnect/wall-4inch/pi-zero-2w-arm64,
inventory SHA530220ee38f6ccbcc824a78331b9dd89f236a5fa6ede12ebf7899dac83ff50c0.
Publication stays0dde0abe22a0859f170a7c1d3eab41f1ade44d37/run39658681213,
v4.0.0-rc.6/INTERNAL_RELEASE/Zeroarchive d67869ffca53c4936059bdbbdbdf6be63b36eafac269fa2f3f9b090922cd0d64,
original installer/lock/80runtime bytes. Native immutable:false; exact downloaded
version/asset/content joins are required, not deletion/availability guarantees.
Consumer.source_sha must later be the actual protected matching Pi V2 separate
Final with its own source/Final qualifications. Current77fc is V1, not V2 adoption.
Do not invent its future hash or transfer earlier source review GO.

## Both actual failed attempts, no history rewriting

Original deployment39669504016/Core0b9/manifest8740/publication0dde stays the
separate original failure binding. New closed previous_recovery_attempt object
binds ACTUAL first recovery39695635601, failed workflow_dispatch/main77fc/
pcvantol/attempt1, Core2945/de22, helper11ce and the exact original raw receipt.
Root freshly downloaded artifact12391115673/namepi-wall4-recovery-evidence,
filepi-recover-evidence.json SHA `ce97876b008d4417ec08100066aa38abf87dd57ae8398ae5e64de97d442744ec`.
Consumer must independently match actual trusted GitHub run metadata/workflow,
artifact identity/size/digest and these exact raw bytes/public joins. A missing
or unavailable original artifact fails closed; no reconstruction/rerun/status
repair or substituted result. Historical remote_may_still_be_running:true stays
true in that receipt, and is NOT a current-state claim. No inference of cancelled,
unchanged boot/PID, successful hold/install or completion from this failure.

The original raw has NO kind/schema_version/helper/observer fields and NO
inputs object/action/execution_mode fields. Never fabricate or require those
nonexistent fields. Join raw public values to current closed previous object,
join exact helper11ce to GitHub blob Tools/pi_rc6_recovery_root.py at77fc, and
the two fixed transport literals to the exact trusted77fc workflow/consumer/
pinned-request-schema chain. Other
request/provenance fields are actual raw public joins. Old fields remain exact.

## Current safety, unchanged narrow observation and durable claim

The same original root-owned ledger is never removed, reset, renamed or rearmed.
claim_policy `UNCHANGED_LEDGER_EXCLUSIVE_DURABLE_CREATE_BEFORE_EFFECTS` requires
fixedc395 to independently pass current original readiness, identity, strict
ed25519 channel, full model/profile/architecture, boot/config and no competing
installer/shutdown checks. Its unchanged atomic exclusive ledger/claim creation,
claim+parent fsyncs occur BEFORE any watchdog hold or installer command. An
existing claim fails closed even across changed run/consumer/manifest/helper.
No historical claim-absence point read can substitute for that current exclusive
claim. No invented controller claim_absent boolean or broad root/sudo grant.

The fixed read-only observer remains `4ae5b8fa3297785a362dfb2e36354cffb4168ab2d0572ef169288d559239e36c` byte-identical,
only boot plus opaque whole-private-config digest. V2 schema pins it explicitly;
NO added claim/process/config-body read route or permission. Current boot/config
before/after helper and matching separate smoke must join; root helper itself
performs existing no_competing_installer and exclusive claim gates. Any unknown
state leaves inconclusive and no implicit retry. Preserve configuration/pairing,
Profile, prior release and all failure/claim/guard evidence. Restore only own
loaded/verified bounded watchdog guard after actual healthy exact installed
bytes, original config semantics and current boot are proven. No credential,
sudoers, root grant, pairing reset, Pi10 reinstall or new model/provider action.

Success is only RECOVERED_PENDING_SMOKE. Separate V2 smoke must match SAME
recovery run/current consumer/producer pair/helper/observer/original+previous
attempt/artifact/instance/boot/config with exact80files/API/client/watchdog
readback. Matching SMOKE_PASS qualifies this instance only, never overall
DEPLOYMENT_OPERATIONAL or physical/touch/audio/native/live/user acceptance.

## Required protected sequence

First protect/actually qualify this additive CoreV2 producer source and distinct
Final, unchanged233-file HA-dev readback/independent review and own cleanup.
Then Pi explicit V2 adoption+negativeV1/V3/mixedpair/helper/previous-receipt cases,
exact independent review, applicable OwnerAuth/normal protected source and
separate Final/raw qualification. ONLY THEN separate CoreV2 operative binding
with actual matching consumer and actual current human scope, its own source/
Final/raw/readback. Pi independently evaluates remaining human/current physical
readiness/no-replay gates; code/hash/timer/new pair is not new device authority.
No placeholder, silent pin replacement, auto-retry or claim cleanup. Core product
bytes unchanged; no redundant HA restart/reinstall for equal code. Hard Core
stop22October06:00UTC/08:00Amsterdam is unchanged, not a Pi/device extension.
