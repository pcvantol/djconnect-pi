# Python 3.14 / Qt 6.12 migration

Status: protected rc.7 Source PR106/f30be820 is originally qualified. Runtime
publication, operational approval and physical activation remain pending.
See PI_PYTHON314_QT612_SOURCE_FINALIZATION.md for exact independent review,
source/merge/qualification pins and the distinct documentary Final scope.
Peter explicitly selected Python 3.14 and latest Qt, including both physical Pis.

## Selected baseline

- Standard GIL-enabled CPython 3.14.9; application support >=3.14.9,<3.15.
- Qt/PySide6 6.12.0 with matching split package pins in requirements.lock.
- pip 26.2.2 and certifi 2026.10.19 security baseline.
- ARM64 and glibc >=2.39, checked before application/service changes.
- OS Python stays unchanged for apt, bootstrap and operating-system tooling.

The installer authenticates and executes the same bounded helper buffer.
The helper downloads the fixed Astral python-build-standalone 20261021 ARM64
CPython 3.14.9 asset, SHA256
`6f77731d85a14ed848dd4041478cd3ed511523caa3d896b84b436a7edf13cf62`.
It checks size, digest, archive members and symlink confinement, probes the native
interpreter and atomically installs it below /opt/djconnect-python. Cached files
must match the original root-owned manifest. No URL/hash/destination override is
accepted by the normal entry point. OS Python is not replaced.

## Transaction and rollback

Use a distinct rc.7 app release directory. An active matching release is rejected
before preparing or deleting its files. New dependencies are prepared with the
old client still running; download/dependency failure does not stop that client.
Only successful preparation reaches the existing service-stop/activation phase.
The shell installer rejects marked incompatible environments before stopping the
UI. The automatic updater also rejects unmarked/incompatible partial environments
and bin conflicts without deleting or executing them. The old release, runtime and
configuration remain available for a separately reviewed rollback. No automatic
watchdog pause, retry after an uncertain root result, pairing or Profile reset.

## Delivery still required

Exact source review/Owner Authorization and checks, protected source, separate
Finalization, immutable distinct rc.7 publication, and matching Core-owned rc.7
operational bindings precede physical app activation. Current vendored rc.6
contracts and historical rc.6 recovery tooling are intentionally unchanged and
cannot authorize this candidate. Per-target smoke must inspect the actual
interpreter, Qt version, app source, service health and preserved configuration.

## Physical preparation observed 2026-10-25

The exact 4-inch device D83ADD41F167 ran the verified interpreter in a new
user-owned home directory. Its app/API PIDs were unchanged; its existing
paired:false remained false. That is separate interpreter preparation, not rc.7
activation. Pi10 88A29EC0EDA6 was unreachable at its known address and hostname;
identity must be freshly verified once it returns. No credentials are copied.

## Evidence boundaries

The old Python 3.11 Qt crash remains failed historical evidence. Raising the
baseline follows the new explicit user instruction; it does not close or explain
that upstream failure. New Python 3.14 source/VM qualification must stand alone.
A later Python3.14 full run exposed an archive-worker completion/shutdown race.
A short reentrant gate now serializes the final native emission against shutdown,
without holding across HTTP. Its controlled old-code race reproduction is
separate from the broader native crash rootcause. See TESTS.md for preserved
failed and final runs.

Root provisioner QA uses a fresh /opt QA prefix in the isolated VM, with the
original verified archive and transport substituted locally. It has no physical
service, HA, Profile, provider or model effects. Live UI, GPU and physical device
acceptance are separate from unit tests and interpreter extraction.


## Independent updater review correction

The first independent whole-29-file review of22236d7 returned NO_GO/P1: the
ordinary updater still created a venv via system python3 and stopped services
before downloads/dependency installation. That does not satisfy the new minimum
on Trixie Python3.13. The corrected source selects the same fixed application
Python as the installer, probes3.14.9+/GIL in isolated mode before service effects,
checks resumed environment identity/metadata without executing it, and runs
venv/pip in isolated mode with the security pip pin. The current release target
is refused before unpacking.

The updater prepares the complete new environment while the current app/API
remain running. Only then does it stop services and activate once. If that
switch was started, the exit path makes one update-UI stop and one normal
service restart attempt even after an error. Failures remain failed. This is
not an atomic systemd/config rollback or proof that asynchronously restarted
services are healthy; actual installed smoke remains a separate gate.

Installed rc.6 updater bytes are immutable and are not retroactively corrected.
The initial rc.6-to-rc.7 interpreter migration must use the qualified protected
installer route; this fix governs the updater delivered in rc.7 and successors.
PR133 was already merged by pcvantol at2026-10-26T08:46:01Z as78594211; the
candidate incorporates that actual main normally and is requalified with
setuptools84.1.0. No second merge or retroactive review claim is made for133.
