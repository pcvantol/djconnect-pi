# Changelog

## 3.1.28

- Initial Raspberry Pi display-remote scaffold with Qt Quick/QML, fullscreen
  720x720 touch UI, playback controls and app-like DJConnect pairing, status
  and command client contract.
- Split the local Client API into `djconnect-pi-api` and
  `djconnect-api.service`; the Qt touch UI no longer hosts the API itself.
- Added full-screen startup splash and blocking first-run pairing screen with
  Client API URL and pairing code input.
- Added Home Assistant version compatibility guard. A `3.1.z` Pi client accepts
  HA `>=3.1.0` and `<3.2.0`; mismatches show a blocking screen and trigger
  `djconnect-updater.service`.
- Added local demo mode before pairing and a "Demomodus stoppen" action that
  returns to the blocking pairing flow.
- Added touch-only local games matching the Apple app set: Paddle Rally, Meteor
  Run, Sky Dash and Maze Chase.
- Set default touch screen blanking to 2 minutes with tap-to-wake and a
  configurable timeout in settings.
- Added unattended GitHub release updater, apt maintenance service, systemd
  units, release scripts and bootstrap documentation.
- Added persistent rotating file logging, configurable screen blanking,
  stable/beta update channel selection and expanded tests.
- Added startup Raspberry Pi system-info logging for both UI and API daemon.
- Hardened config writes with private file permissions and atomic replacement.
- Added Client API request size limiting and expanded regression, monkey,
  installer contract and QML tests.
- Switched unattended app updates to the public release repository
  `pcvantol/djconnect-pi-releases` and added a GitHub Actions publish workflow.
- Added complete release bundles with `docs/`, `scripts/`, `src/` and
  `systemd/` so production Pi installs can run from the public release tarball.
- Added modern HyperPixel 4 KMS DPI overlay setup, Raspberry Pi OS Lite 64-bit
  bootstrap with minimal X11/Qt runtime dependencies and installer version
  output.
- Added dark DJConnect blue/purple gradient styling across the touch UI.
- Updated the cross-repo sync prompt with full HA-side Raspberry Pi mDNS
  autodiscovery requirements.
- Documented manual production updates from the public release tarball and made
  the installer restart API/UI services when rerun over an existing install.
- Reviewed Dutch/English translations, moved game titles behind i18n keys and
  fixed the playback fallback so "nothing playing" is translated by the UI.
- Removed Wi-Fi provisioning from the installer; Wi-Fi/hostname/SSH/locale are
  handled by Raspberry Pi Imager before first boot.
- Split general Raspberry Pi OS bootstrap into repo-only
  `scripts/bootstrap_raspberry_pi_os.sh` and excluded it from release tarballs.
  The DJConnect app installer no longer performs timezone, SSH, apt
  full-upgrade, Raspberry Pi Connect, minimal X11/Qt runtime or
  HyperPixel setup.
- Fixed public release install checksum verification so the installer compares
  SHA256 hash values instead of relying on the filename stored in the `.sha256`
  asset.
- Removed third-party system monitoring setup from all bootstrap scripts and
  documentation; monitoring is no longer installed or managed by DJConnect Pi.
- Made the public release installer resumable across reboot, power loss or
  thermal freezes. Release unpack and Python dependency install steps now use
  markers under `/opt/djconnect/install-state/<version>/`, and pip downloads
  are cached under `/var/cache/djconnect-pip`.
- Moved the pip cache outside `/opt/djconnect` so pip can use it while the
  installer runs as root without ownership warnings.
- Added root filesystem expansion to the repo-only Raspberry Pi bootstrap and
  an early free-space check to the release installer so large PySide6 downloads
  fail with a clear recovery message instead of filling the SD card mid-install.
- Added persistent 1GB swapfile setup to the repo-only bootstrap and an early
  active-swap requirement check to the release installer.
- Renamed the public app installer to `scripts/install.sh`, added resource
  snapshots around major install steps, and added prerequisite checks for
  architecture, Python version, writable paths, GitHub release access and
  Raspberry Pi thermal/throttling status.
- Changed public release tarballs to install from a bundled wheel under
  `wheels/` and stop shipping the loose `src/` app source tree.
- Increased the installer free-space requirement to 3GB, added inode reporting,
  cleaned incomplete `.venv` directories before dependency retries, and moved
  pip temporary files under `/var/cache/djconnect-pip/tmp`.
- Hardened installer recovery for partial venv installs by requiring all
  DJConnect console entrypoints before marking dependencies complete.
- Configured `/etc/X11/Xwrapper.config` with `allowed_users=anybody` during
  install so the systemd-managed touch client can start Xorg on Raspberry Pi OS
  Lite.
- Added `needs_root_rights=yes` to the Xwrapper install step so Xorg can open
  `/dev/tty0` when launched by the systemd-managed touch client.
