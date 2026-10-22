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

## Nested descriptor compatibility with selected Core draft

Core draft PR1290/headfe3a235b8b811d893d3362b20d33245084da245d provides a
concrete V3/schema6 proposal. Its three normative API blobs were independently
matched to the owner's exact SHA256 and git blob IDs for compatibility only.
They are not installed under Tools/pi_contract and are not dispatch authority.
The extracted historical-descriptor rule in tests is a draft compatibility
fixture, not a released producer schema. It is semantically identical to that
rule in the corrected selected Core draft; it is not a byte-copy of a whole
normative file.

latest_descriptor() returns only the closed historical descriptor. It excludes
local evidence_bytes and retains the original classification and nested V1
record. constant_descriptor() replaces a flat-only extraction assumption with a
bounded recursive decoder: at most8 levels,256 nodes,64 required keys per object;
only exact closed objects or primitive constants; no references or optional,
duplicate or unknown schema controls. matches_latest_descriptor() uses recursive
type-strict equality, preserving bool/int distinctions. These methods perform
no network or device operation and grant no execution authority. Production V3
workflow/authority integration remains pending a released producer and its
actual source/Final pins; the live V2 routes are untouched.

72 more cases;245 focused including both earlier failure validators PASS;
FULL3262 integrated PASS/no skips47.33s; Ruff0.16/diff PASS. The earlier3190 full
run remains component evidence. Separate synthetic external compatibility audit
on the actual selected draft:1positive49negative, exact descriptor and nested
V1 equality, explicit V3path and old V2path rejection; no operative example was
exported. These49 checks are not49 new product tests or producer qualification.
Initial new-test import formatting diagnostics were corrected without assertion
changes; both focused runs passed. Runtime80/helper/observer/workflows remain
unchanged, with no device intent, installation, smoke or screen-restoration claim.

The first private draft preview contained a V2 manifest_path. Its original bytes
and an explicit failing V3path assertion are retained as intermediate diagnostics;
Core corrected the path before headfe3a235. That first preview was never adopted
as a product contract, operative binding or device authority.

## Existing V2 parser integration

The released V2 previous_spec now uses the bounded recursive decoder. Its flat
result remains type-strictly identical to the original V2 constants; producer
pins, path, request schemas, helper, observer and workflows remain V2. No V3
authority is imported. The original exact_json function moved to the neutral
pi_json_equivalence module with identical AST and is still exported by the
authority module. This removes an import cycle found by an in-memory preview of
the planned integration; that preview was not a released product failure.

Four additional regression cases cover original descriptor equality, exact
function identity/AST and fresh-process imports in both orders. 409 focused
cases passed before the final import-only lint correction; the exact final
source passed the full3266 integrated tests/no skips47.32s. Ruff0.16/diff PASS.
The intermediate full3266/46.19s and import re-export lint diagnostics are retained.
No assertion, schema, device or replay gate changed. Current precommit host
verification reports retention DRIFT; this is independent of local source tests
and blocks protected delivery/effects until the owner resolves it.

After the exact Core-owner retention receipt, a fresh actual-root verify returned
MATCH in pi-parser-after-owner-retention-hostverify.log. The earlier DRIFT log
and metadata remain preserved. Pi changed no other-lane file. This is current
host readiness, not source, operative or device-recovery approval.
