# DJConnect Pi Agent Instructions

This repository follows the canonical DJConnect design foundation in `pcvantol/djconnect`.

Read first:

- `pcvantol/djconnect/DJCONNECT_CONSTITUTION.md`
- `pcvantol/djconnect/PRODUCT_VISION.md`
- `pcvantol/djconnect/DESIGN_PRINCIPLES.md`
- `pcvantol/djconnect/ARCHITECTURE_PRINCIPLES.md`
- `pcvantol/djconnect/SYNC_PROMPTS.md`
- `pcvantol/djconnect/PRODUCT_ROADMAP.md`
- `pcvantol/djconnect/INNOVATION_LAB.md`

## Role

This repo is the community Raspberry Pi / household display client.

Canonical `client_type` is `raspberry_pi`. Device IDs use `djconnect-raspberry-pi-XXXXXXXXXXXX`.

## Rules

- Pi is an ambient/shared client by default.
- Shared devices should resolve to Household, Living Room, Kitchen, Kids or Guest profiles unless explicitly configured otherwise.
- Do not show personal chat history or Music DNA on shared displays unless the device is explicitly linked to a personal profile.
- Pi renders lightweight insight, playback, readonly Ask DJ stream and Discover surfaces.
- Durable intelligence and profile state belong to the backend.
- Do not add PTT, microphone upload, local DJ response audio or `/api/device/dj_response` unless the product decision changes.
- Keep app updates, OS maintenance and touch UI as separate processes.
- Do not keep a local full copy of cross-repo contracts; canonical sync prompts and roadmap live in `pcvantol/djconnect`.
- User-facing touch UI, web portal, updater UI, setup/status/toast/API-display strings must use stable keys and be present for every supported locale.
