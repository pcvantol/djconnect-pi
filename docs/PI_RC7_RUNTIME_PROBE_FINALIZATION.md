# Native runtime probe source Finalization

Source PR135 was normally squash-merged on29October2026 as
`d5d9b1c569e4764b41c57dc26b663ae600a2834b`, from independently reviewed head
`3f92de39afa801b056a1b17b8edee1dacd4d4469`. Reviewed and merged trees match:
`98861857ce95d3ed1bff26a75cd04da664825908`.

## Independent review and checks

The same existing read-only reviewer examined all four changed files and exact
Git blobs: the local helper, its tests, preparation document and TESTS.md.
Bounded source GO, no actionable findings. Receipt SHA256
`743cb9ee30824289f76739d7e8b65b417dfb82a17215e596f7890e3b9be065be`
is retained in the owning evidence dossier. No tests, source writes, networking,
device actions or merge were performed by that reviewer.

Exact-head checks completed27SUCCESS/4conditionalSKIPPED. Actual canonical
Owner Authorization status was SUCCESS, description
`Not required for LOW_RISK or NORMAL_RISK`. No override, substituted status,
self-review or historical Owner Authorization was used.

Main Validate40865383412 and original canonical reconciliation40865699831
completed SUCCESS. The unchanged canonical source-status validator accepts the
actual protected source status. Original artifact12894280138 contains2116raw
report bytes, SHA256
`a744d55a28839a21b9b8832ebd47d94fdc24870eede9662a5927a6ccd68883b9`.
Its original provider ZIP is1034bytes, SHA256
`07b26b9cb6d95e101243768870acac6c94fba587f2a34a8cb2551edeac6a9ade`,
matching GitHub's artifact digest. Both the raw report and ZIP, full original
run/jobs metadata, artifact index and commit status are retained under
`pi-rc7-functional-vm-20261029/original-d5d9b1c569e4764b41c57dc26b663ae600a2834b`
in the external own evidence directory. This preserves new evidence only; it
does not recreate missing provider ZIPs from older qualification runs.

## Delivered source and validation scope

The native helper runs one isolated subprocess with a15second timeout, no stdin,
no collected output and only PATH/LC_ALL. It checks exact Python3.14.9, enabled
GIL, PySide6/native Qt6.12.0 and expected venv/base/executable joins. The optional
running-process helper reads bounded process stat metadata and executable
path/device/inode twice, with a starttime fence. It reads neither arguments nor
environment, and rejects observed PID reuse or exec changes.

All43targeted tests pass in the existing isolated DebianARM64 VM. One actual
native venv check and a temporary QA Pythonprocess check pass; the process is
rejected after exit. Ruff0.16.0 and diff checks pass. The earlier3583full source
tests and300targeted/150QML published-package views retain their separate scopes;
they are not rerun or recounted for this helper.

## Explicit remaining gates

These helpers remain disconnected from every deployment/smoke workflow. They
create no released schema, target admission, SMOKE_PASS or operational authority.
The caller must authenticate systemd MainPID and trusted base/release provenance.
An executable match does not prove the running process's venv, loaded modules,
configuration or future lifetime. Full package/API/configuration and watchdog
verification remain separate requirements for a later qualified adapter.

The published rc.7 app remains source30c0f8278619a6a5e0ab24726e4c138d167e22c8,
publication40715314835. All84app runtime files, dependency lock/version, installer,
rc.6 contracts/workflows and physical devices are unchanged. Do not republish or
overwrite those existing rc.7 assets. Protected Core rc.7 contract, matching
reviewed Pi adapter, exact operative binding and fresh physical readiness remain
required before installation. No pairing, HA/provider/model action, timer change,
root repair, other-lane source write or full Apple-parity acceptance follows.

This separate documentary Finalization requires its own independent exact review,
normal protected merge and original qualification before being considered closed.
