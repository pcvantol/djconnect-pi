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
- Laatste beoogde release in deze werkronde is `v3.1.94`.
- Public updater assets staan in `pcvantol/djconnect-pi-releases`, inclusief `djconnect-pi-latest.json`.
- Release `v3.1.94` verwijdert het Pi-local `/api/device/dj_response`
  endpoint en adverteert `local_dj_response_endpoint:false`, conform de
  canonical syncprompt. Tekst-only DJ response weergave blijft alleen mogelijk
  via normale Home Assistant command/status responses.
- Na publicatie moeten public assets voor `v3.1.94` worden geverifieerd:
  - `djconnect-pi-3.1.94.tar.gz`
  - `djconnect-pi-3.1.94.sha256`
  - `djconnect-pi-latest.json`
- Pi moet via de normale updater-route naar `3.1.94` worden gebracht.
- Validatie voor `v3.1.94`:
  - run `python3 -m pytest -q`
  - `git diff --check` -> ok
  - GitHub Actions publish workflow voor `v3.1.94` controleren
  - Pi services na updater install: `djconnect-api.service`,
    `djconnect-client.service` en `djconnect-updater.timer` active

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
