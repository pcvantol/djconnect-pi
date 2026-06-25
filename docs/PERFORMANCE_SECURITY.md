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
- Album art is loaded asynchronously by QML and backed by the local artwork
  cache. Now Playing artwork is cached before render, while media-list
  navigation is not blocked by image downloads.
- Queue and Playlist rows are emitted before artwork preparation. Background
  artwork caching is limited to the first 6 media-list items and duplicate
  cache workers are skipped while one is active, which reduces CPU, swap and
  I/O pressure on the Pi Zero 2 W.
- Dynamic artwork is decoded at display size. The main Now Playing artwork can
  use Qt caching because the backend first resolves remote URLs to stable local
  cache files; media-list delegates still avoid retaining extra changing image
  cache entries. Qt's pixmap cache is capped at 4 MB.
- Playback controls live on the dedicated Bediening screen. Speelt nu only
  renders refresh, unobstructed album art and title text, reducing Canvas
  repaint pressure on the default screen.
- Screen blanking defaults to 120 seconds and wakes on tap. Wake refreshes
  playback and screen navigation restarts the idle timer, reducing stale screen
  state while still limiting always-on visual load and burn-in risk. Hardware
  backlight/DPMS control still needs HyperPixel validation.
- Brightness is currently app-level dimming in QML, which is portable across Pi
  images but does not yet lower physical panel backlight power.
- Release installs are atomic at the symlink level, avoiding partially updated
  app directories after power loss.

## Memory and Latency

- The app keeps only one playback model in memory.
- The backend executor is capped at one worker to avoid piling up network
  requests on a weak Wi-Fi link.
- Media-list cache work copies only the bounded visible batch, so long queue or
  playlist responses do not trigger immediate artwork fetches for every row.
- QML uses fixed 720x720 layout dimensions to avoid layout churn on the target
  display.
- The local Client API is a separate daemon, so HTTP/mDNS work cannot block or
  restart the Qt scene.
- The Pi does not expose a local DJ-response endpoint. If Home Assistant returns
  DJ response text in normal command/status responses, the touch UI may display
  that text without adding a local audio or voice path.

## Security

- Spotify credentials stay in Home Assistant.
- The Pi stores only the DJConnect device bearer token and local HA URL. Config
  writes are atomic and stored with `0600` permissions.
- Pair/status/command requests include `client_type: raspberry_pi` and app-like
  capabilities that explicitly disable voice/audio/local response handling.
- Ask DJ is advertised as `text_actions`: the Pi can send typed text to Home
  Assistant, poll shared history and send HA-provided structured action
  payloads, while microphone input, wake word, TTS and local Ask DJ audio
  playback remain unsupported.
- Persistent logging uses rotating files and redacts messages that obviously
  contain tokens, bearer auth, passwords or secrets.
- Startup logs include Raspberry Pi system information such as OS, kernel,
  model, CPU and memory to simplify hardware/debug triage.
- HA and local Client API calls log endpoint, command, HTTP status, JSON parse
  errors and exceptions without logging bearer tokens.
- Local Client API request bodies are capped to reduce accidental memory spikes
  and obvious abuse.
- The repo-only OS bootstrap installs `x11vnc` as `djconnect-vnc.service`
  bound to `127.0.0.1:5901` by default, intended for SSH-tunneled screen
  viewing instead of exposing an unauthenticated VNC port on the LAN.
- GitHub release updates require at least SHA256 verification before install.
  Signed manifests are still recommended for a later hardening pass.
- Stable release discovery uses the public `djconnect-pi-latest.json` asset
  through GitHub's normal release download path instead of unauthenticated
  GitHub API listing calls, avoiding API rate-limit failures on the wall Pi.
- The UI process should run as the unprivileged `djconnect` user. Only updater
  and OS maintenance services need root.
- OS maintenance reboots only when `/var/run/reboot-required` exists and the
  configured maintenance timer runs.
