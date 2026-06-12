# DJConnect Pi Agent Notes

- This is the Raspberry Pi client repo: `pcvantol/djconnect-pi`.
- Treat the Pi as an app-like DJConnect client, not ESP firmware.
- Canonical `client_type` is `raspberry_pi`.
- Device IDs use `djconnect-raspberry-pi-XXXXXXXXXXXX`.
- Do not add PTT, microphone upload, local DJ response audio or
  `/api/device/dj_response` unless the product decision changes.
- Keep app updates, OS maintenance and the touch UI as separate processes.
- Sync `SYNC_PROMPTS.md` byte-for-byte across:
  - `pcvantol/djconnect`
  - `pcvantol/djconnect-app`
  - `pcvantol/djconnect-esp32`
  - `pcvantol/djconnect-website`
  - `pcvantol/djconnect-pi`

