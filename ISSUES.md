# Issues

## Open

- Pairing response shapes should be validated against the current Home
  Assistant integration once the Pi client is tested against a live instance.
- Release signing currently supports SHA256 assets only; signed manifests would
  be stronger for unattended installs.
- The systemd service assumes an X11 session on `DISPLAY=:0`; Wayland/Labwc
  Raspberry Pi OS images may need a compositor-specific wrapper.
- HyperPixel rotation/touch mapping still needs validation for the final
  wall-mount orientation.
- Screen blanking currently hides the UI with a black overlay. It reduces burn-in
  risk but is not yet verified as a true panel/backlight power-off.
- Brightness currently dims the rendered UI in QML. It does not yet control the
  HyperPixel backlight at the hardware level.
- Persistent logs rotate locally, but log retention has not yet been tuned on
  the wall device's SD card.
- Raspberry Pi Zero 2 W performance still needs continued hardware profiling
  for polling cadence, remaining QML repaint work, output-device refresh
  latency and PySide6 memory/CPU usage. The high-load album-art cache path has
  an initial mitigation in place, including smaller cache batches and bounded
  Qt/QML image retention.
- Output-device list availability still depends on the HA contract returning a
  usable `devices`/`output_devices` shape; the Pi now falls back to
  `command:"devices"` when status omits it, but live HA variants should be
  monitored.

## Closed

- Initial repo scaffold created.
- Home Assistant request payload tests added.
- HyperPixel boot/display configuration validated on the Pi Zero 2 W with the
  modern `vc4-kms-dpi-hyperpixel4sq` overlay.
- Dutch/English translation parity reviewed and covered by tests.
- HA `invalid_client_type` during refresh fixed by including
  `client_type=raspberry_pi` and the stable device ID in command payloads.
- Stale mDNS pairing code after reset fixed by reloading shared config in the
  local API daemon before pairing-info and local pair requests.
- Full-screen overlay tap-through fixed by adding modal touch blockers.
- Games screen tap-through fixed by consuming background touch input before it
  reaches underlying Speelt nu controls.
- Empty Home Assistant queue/playlist responses now show explicit empty-state
  labels instead of stale demo entries.
- Bottom navigation made taller with tab icons for more reliable touch use on
  the 4-inch HyperPixel screen.
- Maze Chase ghost pacing and power-pellet behavior improved for a closer
  Pac-Man-like touch game feel.
- Album art rendering and 24-hour local artwork caching added for Speelt nu,
  Wachtrij and Afspeellijsten.
- Queue/playlist artwork regression fixed by pre-caching art in backend workers
  and keeping QML delegates free of blocking Python cache calls.
- Queue/playlist artwork/play-icon placement regression fixed by using anchored
  media rows with fixed artwork and play-button columns.
- Instellingen, Over and Logs no longer render as translucent overlays and
  Instellingen/Over disable horizontal scrolling.
- HA initiated `/api/device/command` calls are bridged from the API daemon to
  the UI process through a local command-event queue.
- Speelt nu playback controls moved to a dedicated Bediening screen so the
  now-playing display can show larger album art and Bediening can use larger
  touch targets.
- Speelt nu album art no longer has a play/pause overlay, leaving the artwork
  unobstructed.
- Queue row playback now uses `play_context_at` with nested `value.uri`, keeps
  direct Spotify track/episode rows playable without queue context and only
  sends `offset_uri` for playlist, album and show contexts.
- Media-list artwork caching is capped to the first visible batch and duplicate
  cache workers are skipped to reduce Pi Zero 2 W CPU, swap and I/O load.
