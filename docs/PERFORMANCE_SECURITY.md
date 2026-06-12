# Performance and Security Review

This file records the first pass review for the wall-mounted Pi client.

## Performance

- Rendering uses Qt Quick/QML instead of a browser or Tkinter. This keeps the UI
  GPU-friendly and avoids Chromium overhead on a Pi Zero 2 W.
- Home Assistant calls run in a small `ThreadPoolExecutor` so QML animations and
  touch feedback do not wait on network I/O.
- Polling is fixed at 5 seconds once a Home Assistant URL exists. Before
  pairing/configuration, refresh exits locally so the blocking pairing screen
  does not generate repeated network failures.
- Album art is loaded asynchronously by QML. Local caching is still a TODO.
- Screen blanking defaults to 120 seconds and wakes on tap. It reduces always-on
  visual load and burn-in risk. Hardware backlight/DPMS control still needs
  HyperPixel validation.
- Brightness is currently app-level dimming in QML, which is portable across Pi
  images but does not yet lower physical panel backlight power.
- Release installs are atomic at the symlink level, avoiding partially updated
  app directories after power loss.

## Memory and Latency

- The app keeps only one playback model in memory.
- The backend executor is capped at two workers to avoid piling up network
  requests on a weak Wi-Fi link.
- QML uses fixed 720x720 layout dimensions to avoid layout churn on the target
  display.
- The local Client API is a separate daemon, so HTTP/mDNS work cannot block or
  restart the Qt scene.
- DJ responses cross from the API daemon to the UI through a small local event
  file instead of sharing an HTTP listener in the UI process.

## Security

- Spotify credentials stay in Home Assistant.
- The Pi stores only the DJConnect device bearer token and local HA URL. Config
  writes are atomic and stored with `0600` permissions.
- Pair/status/command requests include `client_type: raspberry_pi` and app-like
  capabilities that explicitly disable voice/audio/local response handling.
- Persistent logging uses rotating files and redacts messages that obviously
  contain tokens, bearer auth, passwords or secrets.
- Startup logs include Raspberry Pi system information such as OS, kernel,
  model, CPU and memory to simplify hardware/debug triage.
- HA and local Client API calls log endpoint, command, HTTP status, JSON parse
  errors and exceptions without logging bearer tokens.
- Local Client API request bodies are capped to reduce accidental memory spikes
  and obvious abuse.
- GitHub release updates require at least SHA256 verification before install.
  Signed manifests are still recommended for a later hardening pass.
- The UI process should run as the unprivileged `djconnect` user. Only updater
  and OS maintenance services need root.
- OS maintenance reboots only when `/var/run/reboot-required` exists and the
  configured maintenance timer runs.
