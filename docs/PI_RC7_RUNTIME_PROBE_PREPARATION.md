# rc.7 native runtime probe preparation

`Tools/pi_runtime_probe.py` is a local, non-integrated helper for the future
rc.7 smoke adapter. It does not change the current rc.6 contract, schemas,
workflow, operational binding, installer or published rc.7 runtime bytes.

The caller must first establish trusted release/base ownership and provenance.
The helper checks that the selected venv interpreter resolves to that supplied
base's `bin/python3.14`, then runs one isolated `-I -B` native subprocess with
only PATH/LC_ALL, no stdin and no collected stdout/stderr. A15second timeout or
nonzero exit fails without retry. Actual native predicates require exactly
Python3.14.9, GIL enabled/build not free-threaded, venv/base/executable prefix
joins, PySide6 6.12.0 and native Qt6.12.0. No service, installer, config or
pairing action exists in this helper. It is not filesystem provenance proof.

The optional running-process helper separately reads a caller-authenticated PID:
bounded stat metadata plus executable path/device/inode, with a second check and
starttime fence to reject PID reuse or an observed exec change. It never reads
cmdline or environ. The parent still must authenticate systemd MainPID and the
managed root-owned base, and verify release/module bytes/API/config/watchdog.
An executable match alone does not prove the running process uses the checked
venv, modules or configuration, nor that it stays alive after the read. No `SMOKE_PASS` or deployment permission follows from this helper alone.
Contract field names and the watchdog procedure await protected Core delivery.

Qualification:22 targeted cases pass in the existing DebianARM64 VM, including
exact predicate negatives, wrong-base rejection before execution, bounded one
process, signal/nonzero/timeout behavior and static failure messages. A separate
actual native probe of the existing isolated VM3.14.9/Qt6.12 environment passes.
It does not inspect or upgrade either physical Pi. Published runtime84files and
active VM app/config remain unchanged. Full3583source tests and150published
package QML views retain their earlier scope and are not rerun for this helper.

The process extension has21additional cases (43total), including PID reuse,
exec/inode/path changes, deleted/missing image, comm parentheses, malformed/oversize
stat data and an explicit no-cmdline/no-environ assertion. Actual native proof
checks a temporary QA Python process, not either active VM service or physical Pi.
