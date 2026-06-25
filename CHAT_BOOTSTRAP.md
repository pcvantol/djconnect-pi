# Chat Bootstrap Prompt

Use this prompt to initialize a fresh Codex chat for this repository:

```text
Werk in repo: /Users/pcvantol/Documents/GitHub/djconnect-pi

Lees eerst:
- AGENTS.md
- HANDOFF.md
- CHAT_BOOTSTRAP.md
- git status --short

Belangrijke context:
- Dit is de Raspberry Pi client repo `pcvantol/djconnect-pi`.
- DJConnect wordt ontwikkeld en onderhouden met AI-assisted/agentic engineering workflows, inclusief Codex; accepted changes blijven maintainer-reviewed en prompts/logs/issues mogen geen secrets of private data bevatten.
- Canonical `client_type` is `raspberry_pi`.
- Device IDs gebruiken `djconnect-raspberry-pi-XXXXXXXXXXXX`.
- Geen PTT/mic/local DJ response audio of Pi-local `/api/device/dj_response`
  endpoint toevoegen.
- Geen lokale `SYNC_PROMPTS.md` of `PRODUCT_ROADMAP.md`; die staan canoniek in `pcvantol/djconnect`.

Huidige stand:
- Laatste release in deze werkronde is `v3.1.109`.
- Public updater assets staan in `pcvantol/djconnect-pi-releases`, inclusief
  `djconnect-pi-latest.json`.
- Release `v3.1.109` voegt Add to favorites toe voor Now Playing en Ask DJ:
  Now Playing stuurt `save_current_track` via `/api/djconnect/command`, en
  Ask DJ `playback_actions[]` met `kind:"control"` en
  `command:"save_current_track"` worden als directe favorietenknop gerenderd
  zonder recommendation playback of extra artwork.
- Source release is aangemaakt:
  - source repo tag/release: `v3.1.109`
  - source PR naar `main`: `#16`
- Public publish workflow voor `v3.1.109` is geslaagd.
- Public assets voor `v3.1.109` zijn gepubliceerd:
  - `djconnect-pi-3.1.109.tar.gz`
  - `djconnect-pi-3.1.109.sha256`
  - `djconnect-pi-latest.json`
- Pi is via de normale updater-route naar `3.1.109` gebracht.
- Validatie voor `v3.1.109`:
  - `python3 -m py_compile src/djconnect_pi/app.py src/djconnect_pi/ha.py src/djconnect_pi/i18n.py tests/test_ha.py tests/test_app_backend.py tests/test_qml.py tests/test_i18n.py` -> ok
  - `git diff --check` -> ok
  - GitHub Actions publish workflow voor `v3.1.109` -> success
  - Pi services na updater install: `djconnect-api.service`,
    `djconnect-client.service` en `djconnect-updater.timer` active
  - Lokale `pytest` is niet gedraaid omdat pytest niet in de beschikbare
    Python interpreters geïnstalleerd is.

Openstaande gewenste workflow:
- Controleer na elke release de public publish workflow:
  `gh run list --workflow publish-release.yml --limit 3`
- Verifieer na elke release de public assets:
  `gh release view vX.Y.Z --repo pcvantol/djconnect-pi-releases --json tagName,url,assets`
- Actualiseer `CHAT_BOOTSTRAP.md` als onderdeel van elke release closeout.
- Ruim `screenshots/` op en genereer de actuele 720x720 screenshotset opnieuw
  na release/UI-validatie.
- Vanaf `v3.1.85` heeft de updater een losse `djconnect-update-ui.service`; de
  normale touch UI wordt gestopt voordat de installer echt begint, terwijl het
  aparte updater scherm voortgang en live logs toont.

Handmatig client killen op Pi:
sudo systemctl stop djconnect-client.service
sudo pkill -TERM -f 'djconnect-pi-client|djconnect_pi\.app'
sleep 1
sudo pkill -KILL -f 'djconnect-pi-client|djconnect_pi\.app'

Houd bestaande user/uncommitted wijzigingen intact. Gebruik `apply_patch` voor edits. Run relevante tests.
```
