# Changelog

## 3.1.3

- Added Home Assistant version compatibility guard. A `3.1.z` Pi client accepts
  HA `>=3.1.0` and `<3.2.0`; mismatches show a blocking screen and trigger
  `djconnect-updater.service`.

## 3.1.3

- Split the local Client API into `djconnect-pi-api` and
  `djconnect-api.service`; the Qt touch UI no longer hosts the API itself.
- Added full-screen startup splash and blocking first-run pairing screen with
  Client API URL and pairing code input.
- Added local demo mode before pairing and a "Demo modus stoppen" action that
  returns to the blocking pairing flow.
- Set default touch screen blanking to 2 minutes with tap-to-wake and a
  configurable timeout in settings.
- Added startup Raspberry Pi system-info logging for both UI and API daemon.
- Hardened config writes with private file permissions and atomic replacement.
- Added Client API request size limiting and expanded regression, monkey,
  installer contract and QML tests.
- Switched unattended app updates to the public release repository
  `pcvantol/djconnect-pi-releases` and added a GitHub Actions publish workflow.

## 3.1.3

- Initial Raspberry Pi display-remote scaffold.
- Added app-like DJConnect pairing/status/command client contract.
- Added fullscreen 720x720 touch UI with playback controls.
- Added unattended GitHub release updater and apt maintenance service.
- Added systemd units, release scripts and bootstrap documentation.
- Added Qt Quick/QML interface, persistent rotating file logging, configurable
  screen blanking, stable/beta update channel selection and expanded tests.
