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
- Nieuwe review/QA-stap: check deze Pi-repo bij release- of
  Ask DJ/status-werk tegen de `DJ Announcement Output Sync` sectie in
  `pcvantol/djconnect/SYNC_PROMPTS.md`.

Huidige stand:
- Laatste release/deployment in deze werkronde is `v3.2.20`.
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
- Ask DJ is `readonly_actions`: de Pi pollt server-side history/status, toont
  assistant/system/status/user bubbles en stuurt alleen HA-provided structured
  action payloads via `/api/djconnect/v1/command`. Geen vrije prompt input,
  lokale history-clear, voice/PTT, TTS of lokale audio playback toevoegen.
- Release `v3.2.1` sync't de Pi verder met het HA 3.2 backendcontract:
  capabilities rapporteren expliciet `ask_dj_voice_supported:false` en
  `ask_dj_audio_response_supported:false`, en object-vormige
  `music_backend_error` waarden worden veilig als code/message tekst getoond.
- Release `v3.2.7` fixt Raspberry Pi queue rendering voor het actuele
  HA/backend queuecontract: flat `queue:[...]` en nested `queue.items` worden
  geaccepteerd, playlist/search `items` worden niet als queue behandeld,
  artist metadata wordt getoond via `artist ?? artist_name ?? subtitle`, album
  metadata wordt meegenomen en artwork gebruikt `album_image_url ?? image_url
  ?? thumbnail_url`.
- Release `v3.2.8` sync't de Pi met het actuele HA Ask DJ/Music DNA/Track
  Insight contract: relevante requests sturen taal/locale en optionele mood
  mee, Ask DJ gebruikt `audio_response:"auto"`, Music DNA profile/settings/clear
  client calls zijn server-backed, Track Insight stuurt actuele trackmetadata
  mee en toont geen BPM/toonsoort meer.
- Release `v3.2.9` voegt de server-authoritative Music DNA dashboard/opt-in
  flow en de hoofdnav-pagina Ontdek/Music Discovery toe. Ontdek werkt alleen
  na Music DNA consent, rendert uitsluitend HA-aanbevelingen/reasons, gebruikt
  `/api/djconnect/v1/music_discovery` plus refresh/play endpoints en ondersteunt
  de geadverteerde websocket message types met HTTP fallback.
- Release `v3.2.10` zet alle Raspberry Pi Home Assistant DJConnect HTTP-routes
  op de canonical `/api/djconnect/v1/...` prefix, behoudt
  `client_type: raspberry_pi` en voegt regressietest toe zodat DJConnect
  API-routes altijd de canonical `/v1` prefix gebruiken.
- Release `v3.2.11` maakt Track Insight contract-complete voor de server-side
  Home Assistant response, inclusief direct/wrapped response decoding,
  taal/locale/mood/Music DNA context, actuele trackmetadata, nette
  `no_track_playing`/`rate_limited` states en geen BPM/key/modelvelden in het
  UI-model.
- Release `v3.2.11` hardent Ontdek/Music Discovery: de Pi rendert alleen
  backend `sections[].items[]`, dedupet op `id`/`uri`, toont compacte repeated
  counts en stuurt play uitsluitend via
  `/api/djconnect/v1/music_discovery/play` met `section_id` en
  `discovery_item_id`.
- Release `v3.2.12` corrigeert de Ask DJ capability voor `readonly_actions`:
  `ask_dj_free_input_supported:false` in zowel de lokale device API als
  Home Assistant pairing/status payloads.
- Release `v3.2.20` labelt legacy Home Assistant contractroutes in de Node
  E2E fixtures en README expliciet als fixture-only compatibility coverage, en
  voegt guardrails toe tegen Pi voice/audio capability claims,
  `/api/device/dj_response`, `/api/djconnect` zonder `/v1` en websocket
  advertising voor compatibility-only voice of legacy Ask DJ clear routes.
- Source release is aangemaakt:
  - source repo tag/release: `v3.2.20`
- Directe push naar `main` is gedaan met tijdelijke branch-protection/admin
  policy override/bypass voor de release push.
- Public publish workflow voor `v3.2.20` is geslaagd:
  - run `29037579716`
- Public assets voor `v3.2.20` zijn gepubliceerd:
  - `djconnect-pi-3.2.20.tar.gz`
  - `djconnect-pi-3.2.20.sha256`
  - `djconnect-pi-latest.json`
- Release cleanup is uitgevoerd met `--keep 1 --public --execute`.
  Oude source releases/tags `v3.2.19` t/m `v3.2.12`, public releases/tags
  `v3.2.19` en `v3.2.17` t/m `v3.2.12` en completed publish/action runs voor
  oude tags zijn verwijderd; lokaal, source releases en public releases houden
  nu alleen `v3.2.20` over.
- Pi deployment voor `v3.2.20` is uitgevoerd en geverifieerd via de public
  tarball installer-route:
  `~/djconnect-install/djconnect-pi-3.2.20/scripts/install.sh`.
- Pi eindvalidatie:
  - `/opt/djconnect/current` -> `/opt/djconnect/releases/3.2.20`
  - Python package version -> `3.2.20`
  - `djconnect-client.service` -> `active`
  - `djconnect-api.service` -> `active`
  - `/api/device/info` op `http://127.0.0.1:18080` ->
    `version/app_version/firmware: 3.2.20`,
    `client_type: raspberry_pi`, paired, `ask_dj_mode:"readonly_actions"` en
    `ask_dj_free_input_supported:false`.
- Validatie voor `v3.2.20`:
  - `/Users/pcvantol/.platformio/penv/bin/pytest -q`
    -> ok, 362 passed, 13 skipped
  - `node Tools/http_e2e_contract.js` -> ok
  - `node Tools/websocket_e2e_contract.js` -> ok
  - `node Tools/validate_ha_contract_fixture_security.js` -> ok
  - `python3 -m compileall src tests` -> ok
  - `bash -n scripts/install.sh scripts/bootstrap_raspberry_pi_os.sh cleanup_old_releases.sh release.sh` -> ok
  - `git diff --check` -> ok
  - GitHub Actions publish workflow voor `v3.2.20` -> success, run `29037579716`
  - Source release assets voor `v3.2.20` -> gepubliceerd
  - Public release assets voor `v3.2.20` -> gepubliceerd
  - Pi public tarball deployment voor `v3.2.20` -> geverifieerd

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
