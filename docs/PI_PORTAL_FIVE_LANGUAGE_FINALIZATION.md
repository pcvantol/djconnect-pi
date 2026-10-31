# Five-language portal persistence — source Finalization

Source PR139 was normally squash-merged on31October2026 as
`3787c6672bc6f63179a59c93f40a8ac55f3531b5`, from independently reviewed head
`8ef5879dc538e7a700fa0899f51e8aafd72f8133`. Reviewed and merged trees are equal:
`d4df748ea523fe008e73002cdc35943156297274`.

The portal already offered English, Dutch, German, French and Spanish, but the
settings handler persisted only English and Dutch. The handler now uses the
existing central SUPPORTED_LANGUAGES list. No new copy, protocol field, locale
alias, permission, authentication, Profile or pairing behavior is introduced.

## Review and original qualification

The same existing independent read-only reviewer examined the entire four-file
diff and exact Git blobs, with bounded source GO and no actionable findings.
Receipt SHA256 is
`9e64557b0a13ba4b2145504cdd3afd1c8078c4c8c11fa7ec3fab3877d4d548fc`.
The reviewer performed no writes, tests, network, device, config or merge actions.
Exact-head CI completed27SUCCESS/4conditionalSKIPPED. Actual canonical Owner
Authorization was SUCCESS, description `Not required for LOW_RISK or NORMAL_RISK`;
no override, self-review or historical authorization was substituted.

Original main Validate41204046013 and canonical reconciliation41204276486 both
completed SUCCESS. The unchanged source-status validator accepts the actual
protected status. Artifact13043782035 contains2106raw report bytes, SHA256
`36b4e0364866c5701fa9e9e786615a3acc88ef0b5afceea781355832ed2b35fe`.
The original provider ZIP is1032bytes, SHA256
`2107b6020ee2e6908df96c5fc80d4afcceb39772ae09d028ef744b27a95e4664`,
matching GitHub's artifact digest. Raw report, provider ZIP, full original
run/jobs/artifact metadata and coverage ZIP are retained in the external own
`pi-portal-five-languages-20261031/original-3787c6672bc6f63179a59c93f40a8ac55f3531b5`
evidence directory. No older missing artifact has been reconstructed or relabelled.

## Validation and limitations

The controlled old-handler HTTP roundtrip reproduced6FAIL/2PASS: German/French/
Spanish, including case/whitespace variants, retained the previous Dutch choice;
English/Dutch passed. After the fix, all35ClientAPI tests pass, including12new
realHTTP cases for persistence/readback, unsupported input, unchanged synthetic
identity/token/pairing/Profile and one settings notification. Tests ran in the
existing DebianARM64 Python3.14.9/Qt6.12 VM with only loopback networking. Local
Ruff0.17.3 and diff checks passed; canonical CI lint is separate. No full local
suite, QML or browser click run is claimed for this API-only change.

Initial test collection lacked PYTHONPATH and produced no product result; the
corrected source path then reproduced the genuine regression. Both logs remain.
CUA reported no browser and native Safari/inventory timed out. This was not
bypassed or counted as UI acceptance. Only the own temporary loopback webforward
was opened on the existing VM SSHcontrol connection and then cancelled.

The live VM remains normally paired, Dutch and on the unchanged publishedrc7
package. Its installed client_api bytes were independently compared with that
published wheel after source work. No live language setting or physical Pi was
changed. This fix needs a distinct future qualified app release; do not overwrite
existing rc.7 assets or infer installed acceptance from protected main. Existing
rc.7 deployment still needs the Core-owned contract, matching reviewed adapter,
exact operative binding, watchdog safety and fresh per-target readiness/smoke.

This separate documentary Finalization requires its own independent exact review,
normal protected merge and original qualification before being considered closed.
