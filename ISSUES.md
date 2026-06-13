# Issues

## Open

- The Qt Quick UI can render album art from `image_url`, but it does not yet
  cache artwork locally for offline/repeated playback.
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

## Closed

- Initial repo scaffold created.
- Home Assistant request payload tests added.
- HyperPixel boot/display configuration validated on the Pi Zero 2 W with the
  modern `vc4-kms-dpi-hyperpixel4sq` overlay.
- Dutch/English translation parity reviewed and covered by tests.
