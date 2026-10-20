# Pi 4.0.0-rc.5 deployment preparation

Peter requested screenshots of the actual deployed shared app on both the 4-inch Pi and Pi10 after a completed slice. This preparation creates a distinct version for the shared Apple-experience candidate; it does not overwrite rc.3 or rc.4, activate a device, publish a release or qualify full parity.

Runtime/installer/bootstrap version is `4.0.0-rc.5`; wheel metadata uses `4.0.0rc5`. Dependencies remain locked. README/bootstrap download examples match the rc.5 candidate and are explicitly gated on its separate publication.

## Fresh device preflight, 20 October 2026

- 4-inch: SSH alias `djconnect-wall-4inch`, actual `rbpi-djconnect`, Raspberry Pi Zero 2 W, aarch64, current `/opt/djconnect/releases/4.0.0-rc.3-pi-zero-2w-arm64`; native app active, browser kiosk inactive. Python3.13.5/PySide6 and Qt6.11.2; paired flag true. No token or Profile identifier was retrieved. About12GiB free; approximately140MiB available memory and1.2GiB free swap. General privileged Python and display reads require a password, but fresh `sudo -n -l` confirms the existing narrowly allowlisted installer paths are NOPASSWD. This is not an installation-access blocker for the normal allowed installer; no sudo rule/password change is needed or authorized.
- Pi10: SSH alias `djconnect-pi10`, actual `rbpi5-djconnect`, Raspberry Pi5, aarch64, current `/opt/djconnect/releases/4.0.0-rc.4-pi5-arm64`, installed source `16b385ed5d8f79acaa3847d194f442c2cb85671c`; native app active, browser kiosk inactive. Python3.13.5/PySide6 and Qt6.11.2; paired flag false, no explicit/active Profile. X11 reports1200x1920 with existing inverted DSI2 orientation. About102GiB free. No pairing/configuration/display change was made.

The predecessor6078e706 has25successful applicable CI checks/4conditional skips. An in-memory compile of all29 candidate Python modules passed on each ARM runtime; this does not import/install the candidate or render its QML. Exact results are external evidence under `pi-deployment-screenshot-preflight`. No new full-suite or installed proof follows from these checks.

## Delivery gates and capture plan

1. Qualify and independently review the exact rc.5 source; obtain exact-candidate authorization and protected source/main/Finalization readbacks required by normal delivery. A draft PR or green CI alone is insufficient.
2. Build the same shared wheel into both target profiles, bind immutable artifact SHA256/source/requirements, and qualify ARM/QML separately. Publish only a new explicitly approved version; never substitute `latest` or overwrite rc.4.
3. Bind installation authority to both actual hosts and exact published artifact hashes. The existing deploy workflow permits only `rbpi-djconnect` and the old operational manifest is not a Pi5 approval. Do not broaden its enum or forge a Core manifest here. Resolve the actual target authority and the actual 4-inch installer-access prerequisite before activation.
4. Preserve current release directories, pairing/config and Profile selection. Activate one target at a time with native UI/API health and exact installed version/source readback. Stop on failure; retain a known rollback target. Do not auto-pair Pi10 or silently select a Profile to manufacture an active Session screenshot.
5. Use each installed local loopback `/api/debug/screenshot` scenegraph route over SSH. Capture actual Session/More/controls where genuinely available; label unpaired/unavailable states honestly. Save PNG hashes, dimensions, host/profile identity, timestamp and installed-source/package receipts. Review screenshots before displaying them to Peter; no credentials or pairing codes in published captures. No fixture data injected into the installed app.
6. Report installed screenshot evidence separately from live HA/Profile, physical touch, audible output, complete Apple parity and hardware performance acceptance.

This preparation does not adopt the new Core Brand2.0.1 assets; the protected handoff is recorded as available for a separate bounded owning-source adoption. No Core/Apple source, release-repository source, operational manifest or other-lane evidence was mutated.
