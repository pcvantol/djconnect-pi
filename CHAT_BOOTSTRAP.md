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
- Laatste release in deze werkronde is `v3.1.112`.
- Public updater assets staan in `pcvantol/djconnect-pi-releases`, inclusief
  `djconnect-pi-latest.json`.
- Release `v3.1.112` voegt Raspberry Pi client support toe voor Ask DJ
  technical track analysis contract v2: responses met
  `intent.intent=="technical_track_analysis"` of `action=="track_analysis"`
  renderen read-only analysis sections, optionele timeline, DJ tips en
  limitations; v1 `measured`/`inferred` fallback blijft ondersteund zonder
  prose uit `text`/`dj_text` te parsen; expliciete `playback_actions[]` blijven
  de enige technische analyse playback controls.
- Source release is aangemaakt:
  - source repo tag/release: `v3.1.112`
  - source PR naar `main`: `#17`
- Directe push naar `main` is geprobeerd met tijdelijke admin override, maar
  GitHub branch protection bleef PR-only afdwingen. Branch/tag/release zijn
  wel gepubliceerd.
- Public publish workflow voor `v3.1.112` is geslaagd.
- Public assets voor `v3.1.112` zijn gepubliceerd:
  - `djconnect-pi-3.1.112.tar.gz`
  - `djconnect-pi-3.1.112.sha256`
  - `djconnect-pi-latest.json`
- Pi draait `3.1.112`. Deployment is gedaan via de gedocumenteerde public
  tarball installer-route:
  `~/djconnect-install/djconnect-pi-3.1.112/scripts/install.sh`.
  De eerste installpogingen werden tijdens grote PySide6 stappen door een
  gesloten SSH sessie onderbroken, maar de resumable install markers werkten;
  herstarten van dezelfde installer rondde de installatie en activatie af.
- Validatie voor `v3.1.112`:
  - `/Users/pcvantol/.platformio/penv/bin/pytest tests/test_ha.py tests/test_app_backend.py tests/test_qml.py tests/test_i18n.py -q`
    -> ok, 143 passed
  - `python3 -m py_compile src/djconnect_pi/app.py src/djconnect_pi/ha.py src/djconnect_pi/i18n.py tests/test_ha.py tests/test_app_backend.py tests/test_qml.py tests/test_i18n.py` -> ok
  - `bash -n scripts/install.sh scripts/bootstrap_raspberry_pi_os.sh cleanup_old_releases.sh release.sh` -> ok
  - `git diff --check` -> ok
  - GitHub Actions publish workflow voor `v3.1.112` -> success
  - Pi services na install: `djconnect-api.service`,
    `djconnect-client.service` en `djconnect-updater.timer` active
  - Pi local API `/api/device/info` op `127.0.0.1:18080` meldt
    `version/app_version/firmware` als `3.1.112`

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
