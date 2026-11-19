# Python 3.14.9 / Qt 6.12 Source Finalization

Source PR106 was normally squash-merged at2026-10-26T22:07:29Z as
`f30be8208a29ea4b3923e7c0bcb429c84782fefa`, from reviewed head
`ded1f938029b11dc7a432de64054c05e05570fb4`, base
`78594211b602579908e104c3d071dcd3690bbe27`. Reviewed and merged trees are equal:
`e0abd5fd208d51f192f06dc5b8cbeaf03466e253`.

## Independent source review and correction

Peter explicitly selected Python3.14/latestQt for both physical Pis and later
instructed normal merge and Finalization. When Core parked the requested review
for its Help priority, Peter approved one separate read-only reviewer. That
reviewer examined all29 changed files at22236d7 and found a blocking P1: the
automatic updater still created a system-Python venv and could leave services
stopped after failing the new wheel minimum. That head was not merged.

The corrected exact ded1f938 received bounded independent Source GO, findings
empty. All32 changed-file/blob/SHA entries were verified;24 predecessor files
were byte-identical, five changed predecessor paths and three updater-related
paths newly in the review scope were examined. Receipt SHA256
`67e17db5b7ec630a494a255ee0576d9a382e544d5e7a368a995d073f4ab0f341`
is retained in the own evidence dossier. The reviewer ran no tests or effects.

The updater now selects/probes the fixed app Python, validates compatible resume
state without executing/removing incompatible environments, prepares before
stopping services, refuses the active release target and makes one normal
restart attempt after a started switch exits. This is not atomic systemd/config
rollback or proof of asynchronously restarted service health. Immutable installed
rc.6 updaters are not retroactively fixed; first migration still requires the
separately qualified installer route.

Exact candidate checks were27SUCCESS/4conditionalSKIPPED. Fresh original
HIGH_RISK Owner Authorization40409466075 explicitly binds PR106/ded1f938/PASS.
No administrator override, self-review, substituted status or historical
Owner Authorization was used for this head.

## Original protected qualification

Main Validate40409971656 and original canonical reconciliation40410282354
completed SUCCESS. Actual downloaded artifact12693505463 is4378bytes, SHA256
`7f75a21c023acc19819af3e11d631395a7922117dafbc716509fdb9fda03c3d6`.
It binds PR106/ded1f938/mainf30be820, HIGH_RISK, findings empty and
POST_MERGE_RELEASE_EVIDENCE_QUALIFIED. Tests, coverage, CI, build, lint,
static analysis, governance and provenance are PASS. The unchanged local
canonical validator independently accepted the actual source status.

Setuptools PR133 was already merged by pcvantol at2026-10-26T08:46:01Z as
`78594211b602579908e104c3d071dcd3690bbe27`, head
`6d1c990a9bdca626822ae0b267a5c4e84e331faa`, parent
`b0dc7fa15fa02732825aed28994c98fdb312ccf4`. It changes only the isolated build
backend84.0.0 to84.1.0. Its actual original qualification40294935743/artifact
12637099154 is1878bytes, SHA256
`f9580a009ecc0590e664cf13a0c883d1db910cf0a596787c70ceb5134c33a9c7`.
It binds the actual PR/head/main with all applicable checks PASS and no findings.

Our reviewer independently checked that protected one-file delta after the merge,
with no actionable findings. Post-merge review receipt SHA256
`3187aedbaf67150d7f83c91ab7a6f275b1ad5854ee25fe513527447b50b4dbdb`
is retained. Original head6d1 was unavailable in the local object database;
PR-head provenance comes from the original canonical artifact, not a local
head/tree comparison. No premerge review or second merge by this lane is claimed.
PR106 normally incorporated actual main785 before correction/requalification.

## Evidence and remaining operational gates

The final owning integrated VM suite is3583PASS/no skips70.69s, with113focused
PASS and36 new updater regressions. Two controlled tests fail on the exact old
updater and pass after correction. All service/pip/download effects are mocked;
selected Python probes use synthetic version metadata. Earlier3547 and150 actual
QML views, and predecessor866+25 component renderings, retain their exact prior
scope and are not counted as new final-source runs. QML bytes are unchanged.
The earlier Python3.11 and later native-crash diagnostics remain failed; no
universal PySide crash cause or hardware fix is asserted.

Python3.14.9/setuptools84.1.0 review wheel SHA256
`49b5f3fdcff810a7bf4c7350f4b0f16d52fa0d3e4971b5815616dee77d984c16`
matches all84 committed runtime files. It is not a published operational asset.
Raw receipts, failed diagnostics, exact-source packets, logs and package proofs
are retained under the external own pi-python314-qt612-migration-20261025 taskroot.

The source is qualified for a distinct rc.7. This document still requires its own
independent exact review, normal protected merge and original qualification.
Immutable publication, matching new Core-owned rc.7 operational binding, actual
per-device installation/smoke and product acceptance remain separate gates.
Neither physical running app was upgraded by this merge work; no new pairing,
HA/provider/model/device action, audio capability or full Apple-parity claim.
The sole existing Pi worktree was used, primary checkout and unrelated WIP kept;
fresh actual-root host verification was MATCH before the source merge.
