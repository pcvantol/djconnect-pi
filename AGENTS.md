# DJConnect Pi Agent Notes

- This is the Raspberry Pi client repo: `pcvantol/djconnect-pi`.
- Treat the Pi as an app-like DJConnect client, not ESP firmware.
- Canonical `client_type` is `raspberry_pi`.
- Device IDs use `djconnect-raspberry-pi-XXXXXXXXXXXX`.
- Do not add PTT, microphone upload, local DJ response audio or
  `/api/device/dj_response` unless the product decision changes.
- Keep app updates, OS maintenance and the touch UI as separate processes.
- Do not keep a local `SYNC_PROMPTS.md` in this repo. The canonical cross-repo
  contract source is `pcvantol/djconnect/SYNC_PROMPTS.md`.
- Do not keep a local `PRODUCT_ROADMAP.md` in this repo. The canonical product
  roadmap source is `pcvantol/djconnect/PRODUCT_ROADMAP.md`.
- For cross-repo contract changes originating here, make a follow-up
  change/commit in `pcvantol/djconnect`.
- User-facing touch UI, web portal, updater UI, setup/status/toast/API-display
  strings must use stable keys in `src/djconnect_pi/i18n.py` and be present for
  every supported locale: `en`, `nl`, `de`, `fr`, `es`. Keep protocol values,
  endpoint paths, JSON keys, command names, auth tokens, machine-parsed error
  codes and developer log tokens unlocalized.
