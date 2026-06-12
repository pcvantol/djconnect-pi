# Performance and Security Review

This file records the first pass review for the wall-mounted Pi client.

## Performance

- Rendering uses Qt Quick/QML instead of a browser or Tkinter. This keeps the UI
  GPU-friendly and avoids Chromium overhead on a Pi Zero 2 W.
- Home Assistant calls run in a small `ThreadPoolExecutor` so QML animations and
  touch feedback do not wait on network I/O.
- Polling is fixed at 5 seconds for now. That is responsive enough for a wall
  remote without hammering Home Assistant.
- Album art is loaded asynchronously by QML. Local caching is still a TODO.
- Screen blanking after inactivity reduces always-on visual load and burn-in
  risk. Hardware backlight/DPMS control still needs HyperPixel validation.
- Release installs are atomic at the symlink level, avoiding partially updated
  app directories after power loss.

## Memory and Latency

- The app keeps only one playback model in memory.
- The backend executor is capped at two workers to avoid piling up network
  requests on a weak Wi-Fi link.
- QML uses fixed 720x720 layout dimensions to avoid layout churn on the target
  display.

## Security

- Spotify credentials stay in Home Assistant.
- The Pi stores only the DJConnect device bearer token and local HA URL.
- Pair/status/command requests include `client_type: raspberry_pi` and app-like
  capabilities that explicitly disable voice/audio/local response handling.
- Persistent logging uses rotating files and redacts messages that obviously
  contain tokens, bearer auth, passwords or secrets.
- GitHub release updates require at least SHA256 verification before install.
  Signed manifests are still recommended for a later hardening pass.
- The UI process should run as the unprivileged `djconnect` user. Only updater
  and OS maintenance services need root.
- OS maintenance reboots only when `/var/run/reboot-required` exists and the
  configured maintenance timer runs.

