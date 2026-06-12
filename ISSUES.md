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
- HyperPixel boot/display configuration needs hardware validation on the actual
  Pi Zero 2 W.

## Closed

- Initial repo scaffold created.
