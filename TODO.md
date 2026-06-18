# Todo

- Add vertical edge swipe for volume.
- Polish the pairing/settings screen with an on-screen keyboard strategy.
- Add a richer backend-unavailable UI state.
- Continue hardware profiling for polling cadence, remaining QML repaint work,
  output-device refresh latency and PySide6 memory/CPU on the Raspberry Pi
  Zero 2 W. Album-art cache pressure has an initial mitigation: only the first
  visible media-list batch is cached, dynamic artwork is decoded at display
  size and duplicate cache workers are skipped.
- Reduce Home Assistant polling and UI refresh work when playback is idle or
  the screen is blanked.
- Cap the on-screen log viewer to the newest lines while keeping full persisted
  file logging on disk.
- Implement full HA-side Raspberry Pi mDNS autodiscovery in `pcvantol/djconnect`
  according to canonical `pcvantol/djconnect/SYNC_PROMPTS.md`.
- Validate the separate API daemon command-event queue, output-device selector,
  HA `devices` fallback and DJ-response toast bridge on real Pi hardware with
  Home Assistant.
- Validate HyperPixel rotation/touch mapping on hardware.
- Wire QML screen blanking to OS-level display power management if HyperPixel
  supports it reliably on the target image.
- Investigate HyperPixel hardware backlight control and map the brightness
  slider to it when reliable.
