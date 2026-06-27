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
- Laatste release in deze werkronde is `v3.2.1`.
- Public updater assets staan in `pcvantol/djconnect-pi-releases`, inclusief
  `djconnect-pi-latest.json`.
- Release `v3.2.0` upgrade de Raspberry Pi client naar protocol `3.2.x`:
  Pi blijft local-only, pairing gebruikt alleen `ha_local_url`, accidental
  `ha_remote_url`/Nabu Casa runtime URLs worden genegeerd, en de client blijft
  `client_type: raspberry_pi`.
- `v3.2.0` parseert de HA music-backend summary:
  `music_backend`, `music_backend_name`, `music_backend_available`,
  `music_backend_revision`, `music_backend_capabilities`,
  `music_target_player` en `music_backend_error`. About/status/diagnostics
  tonen transport Local only, backend, target player, availability/error en
  compacte capabilities.
- Ask DJ blijft tekst-only via `/api/djconnect/ask_dj/message`, stuurt
  identity (`client_type`, `device_id`, `device_name`) mee, accepteert
  backend-aware `playback_actions[]` zonder Spotify URI te vereisen en toont
  unsupported capability/stale backend action responses als nette meldingen
  zonder Spotify-specific fallbacks.
- Release `v3.2.1` sync't de Pi verder met het HA 3.2 backendcontract:
  typed Ask DJ requests sturen nu `audio_response:"never"`, capabilities
  rapporteren expliciet `ask_dj_voice_supported:false` en
  `ask_dj_audio_response_supported:false`, en object-vormige
  `music_backend_error` waarden worden veilig als code/message tekst getoond.
- Source release is aangemaakt:
  - source repo tag/release: `v3.2.1`
- Directe push naar `main` is gedaan met tijdelijke branch-protection/admin
  policy override voor de release push; policy is daarna teruggezet.
- Public publish workflow voor `v3.2.1` is geslaagd:
  - run `28279973929`
- Public assets voor `v3.2.1` zijn gepubliceerd:
  - `djconnect-pi-3.2.1.tar.gz`
  - `djconnect-pi-3.2.1.sha256`
  - `djconnect-pi-latest.json`
- Release cleanup is uitgevoerd met `--keep 1 --public --execute`.
  Oude source/public release en tag `v3.2.0` zijn verwijderd; de
  public tag cleanup is na een HTTPS git-auth fout afgemaakt via de GitHub API.
- Pi deployment moet nog worden uitgevoerd/geverifieerd na public publish via
  de gedocumenteerde public tarball installer-route:
  `~/djconnect-install/djconnect-pi-3.2.1/scripts/install.sh`.
- Vorige Pi deployment draaide `3.1.112`. Deployment was gedaan via de public
  tarball installer-route:
  `~/djconnect-install/djconnect-pi-3.1.112/scripts/install.sh`.
  De eerste installpogingen werden tijdens grote PySide6 stappen door een
  gesloten SSH sessie onderbroken, maar de resumable install markers werkten;
  herstarten van dezelfde installer rondde de installatie en activatie af.
- Validatie voor `v3.2.1`:
  - `/Users/pcvantol/.platformio/penv/bin/pytest -q`
    -> ok, 266 passed, 12 skipped
  - `python3 -m py_compile src/djconnect_pi/config.py src/djconnect_pi/ha.py src/djconnect_pi/client_api.py src/djconnect_pi/app.py src/djconnect_pi/i18n.py tests/test_ha.py tests/test_client_api.py tests/test_app_backend.py tests/test_installation_contract.py` -> ok
  - `bash -n scripts/install.sh scripts/bootstrap_raspberry_pi_os.sh cleanup_old_releases.sh release.sh` -> ok
  - `git diff --check` -> ok
  - GitHub Actions publish workflow voor `v3.2.1` -> success
  - Source release assets voor `v3.2.1` -> gepubliceerd
  - Public release assets voor `v3.2.1` -> gepubliceerd

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
