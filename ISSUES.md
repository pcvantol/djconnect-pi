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
- Raspberry Pi Zero 2 W performance still needs a dedicated hardware profiling
  pass for polling cadence, QML Canvas repaints, log viewer size, album-art
  cache pressure and PySide6 memory/CPU usage.

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
- Album art rendering and 24-hour local artwork caching added for Speelt nu,
  Wachtrij and Afspeellijsten.
- HA initiated `/api/device/command` calls are bridged from the API daemon to
  the UI process through a local command-event queue.
