# Latest wall4 recovery failure: read-only consumer preparation

This is a prerequisite component for a new reviewed recovery route. It is not
wired to a workflow or a new producer contract and does not authorize another
recovery attempt. The physical 4-inch UI is still disabled/inactive in the latest
actual readback. Runtime version remains the published 4.0.0-rc.6/source0dde.

The actual V2 attempt39775941080 failed at consumerFinal
2e7479d0d15aa11ad3bff4c8103c18dbb1f2c32a, CoreFinal83744790 and manifestc63ca35c.
Its original artifact12423814908 contains one pi-recover-evidence.json,3058 bytes,
SHA256 eb57af222e6be4f9d7e9e40be488f3f395ae2e6e94a583e6d4ea7e9d839c6b4d.
It says RECOVERY_INCONCLUSIVE, intent_dispatched:true and
remote_may_still_be_running:true. These historical values remain unchanged.

Tools/pi_wall4_latest_failure.py verifies the exact trusted failed run, actor,
main branch, attempt1, qualified consumer, five original code blobs, exact
artifact identity/layout/digest and the entire typed original receipt. Its
nested V1 failure remains byte-semantically identical to the original V1
record. The new V2 receipt has kind/schema/helper/observer fields; it has no
inputs/action/execution_mode, root diagnostic, claim-absence or failure-counter
fields. Local observations must never be invented as GHA receipt fields.
Missing/unavailable or modified evidence fails closed. None of these reads
creates current execution, cancellation, claim-reset or retry authority.

The existing V2 producer machine-pins only the earlier V1 failure39695635601.
A new free-text authority_record cannot substitute the latest failed attempt
for that closed object. Core must select/review the bounded successor contract,
then Pi must implement and qualify the matching consumer. Exact protected source,
separate Finalization and a distinct qualified operative binding/current human,
readiness, physical-intent and noReplay checks precede any further device intent.
The draft Pi schema proposal in private task evidence is not released authority.

The separate actual private root log returned only the reviewed static code
RECOVERY_WATCHDOG_STATE_CHANGED. Read-only stat found no original ledger or
runtime hold at that observation. Those observations are not a permanent state
or permission to recreate/reset a claim. Two later reads showed different boot
IDs, counter186->187 and a312.940942226s counter-mtime interval while the native
client remained disabled. Published watchdog threshold5/reboottrue/OnBoot5min is
consistent with a reboot loop. The exact failed predicate field was not recorded;
no timingrace rootcause or busy-state acceptance is claimed. Root helperc395,
observer4ae5, exclusive original durable claim/four fsyncs, hold/install/restore
and all runtime/installer/lock bytes remain unchanged.

Qualification for this component:75 additional tests;173 focused including the
original V1 validator; full3190 passed/no skips47.42s. Ruff0.16 and diff checks
pass. Formatting of the two new Python files was AST-identical after that full
run. A separate actual read-only GitHub exercise matched the original artifact
and all five protected code pins; it performed no device or dispatch action.
The original fixture bytes are unchanged. There are no new Qt/ARM/installed,
smoke/display/touch/live Profile/Spotify/audio acceptance results.

Diagnostics retained in private task evidence: the initial generator accidentally
replaced the nested historical V1 consumer while changing the outer consumer.
Code inspection corrected it before final qualification; a new independent
assertion compares the nested object with both original raw and released V1
constants. An unused test import was removed. The earlier172 focused result is
intermediate, replaced by173 final. No assertions or product gates were relaxed.
