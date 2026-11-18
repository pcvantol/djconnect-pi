# Pi dependency consolidation Finalization

## Protected source

PR138 was squash-merged as `c8496924508c44e24142cc24194d1a42e27936f2`
from independently reviewed head `2829212f608808c1e4ecaf6facf14a6d2606d4d7`.
The reviewed and protected trees match. Seven workflows update full-SHA pins
for setup-python and CodeQL; permissions, triggers and governance remain intact.

PR137 was squash-merged as `0e8fc9860766992a796dcd2c6bcf27c994ed92c8`
from independently reviewed head `11b46a281f56ffb4ed53576ffe9dc9535b7d73b9`.
Setuptools build isolation moves to84.2.1; coverage moves to7.17.0 in both
pyproject.toml and the canonical requirements.lock. The initial review found
the unchanged7.16.2 lock inconsistent with the declared dev dependency. The
one-line correction received independent exact-head closure. The runtime/test
setuptools lock remains83.0.0, distinct from the isolated build backend.

Both exact heads completed27SUCCESS/4conditionalSKIPPED. PR138 received fresh
HIGH_RISK Owner Authorization41359264758 for its exact head. PR137's canonical
Owner Authorization reports not required for LOW_RISK or NORMAL_RISK. The
initial missing authorization is not counted as success.

Independent merged-composition readback confirms PR137 applies exactly its
reviewed two-file delta atop PR138, leaving all other paths unchanged. The
combined protected tree is `b48d80e786ebebe93f7c6e69d41ffe1c0f402bb4`.

## Original qualification

PR138 main Validate41359419681 and original reconciliation41359668976 pass.
The raw2478byte report SHA256 is
`2ff39fba876f31749b9bcb081921fa2df3c3e85e36186344fab93b684d5c3c04`;
its original1053byte provider ZIP SHA256 is
`598b6363354762c90361613e83db136ddb26c3688d332ba906b6a9922d5dad98`.
A separate older TDE observe run41359419123 was cancelled; it is not a PASS.

Combined main Validate41359573033 and original reconciliation41359777743 pass.
The raw1932byte report SHA256 is
`17a4ab597a025f9b0426ed88f8e91b4851bb26f78ac7ae0ff9189c903d36fae1`;
its original985byte provider ZIP SHA256 is
`a31bd33dff5eac1107131b04bdd4996782870b5e0b19b9d1cc1adbb6d33aee6c`.
The unchanged canonical validator accepts both actual protected statuses.
Provider digests, raw report extraction, full original run/jobs metadata and
coverage ZIP joins are independently checked and retained under
`pi-dependency-consolidation-20261102/original-<merge SHA>` in the external
own evidence directory. The original combined main log confirms coverage7.17.0
and2809Python tests passed with17skips; dedicated consumer checks retain their
separate scope. No new local full-suite or QML run is claimed.

## Delivery boundary

This is source/development-tooling delivery. Application runtime source bytes,
app version and official published rc.7 assets are unchanged. There is no new
publication, VM package replacement, physical Pi installation, HA-dev mutation,
pairing, provider action or physical/GPU acceptance. The protected rc.7 Core
contract, matching consumer, exact operative binding and fresh target readiness
remain required for physical deployment. This separate documentary Final still
requires its own independent review, protected merge and original qualification.
