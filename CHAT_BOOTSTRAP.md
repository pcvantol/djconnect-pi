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
- Laatste voorbereide release in deze werkronde is `v3.2.12`.
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
- Source release voor `v3.2.12` moet nog worden afgerond als deze bootstrap in
  een half-afgebroken release-run wordt gelezen. Controleer:
  `git tag --list v3.2.12`.
- Public publish workflow en public assets voor `v3.2.12` moeten na de
  source release worden gecontroleerd:
  - `djconnect-pi-3.2.12.tar.gz`
  - `djconnect-pi-3.2.12.sha256`
  - `djconnect-pi-latest.json`
- Pi deployment voor `v3.2.12` moet nog worden uitgevoerd/geverifieerd via de
  public tarball installer-route:
  `~/djconnect-install/djconnect-pi-3.2.12/scripts/install.sh`.
- Vorige Pi deployment draaide `3.1.112`. Deployment was gedaan via de public
  tarball installer-route:
  `~/djconnect-install/djconnect-pi-3.1.112/scripts/install.sh`.
  De eerste installpogingen werden tijdens grote PySide6 stappen door een
  gesloten SSH sessie onderbroken, maar de resumable install markers werkten;
  herstarten van dezelfde installer rondde de installatie en activatie af.
- Validatie voor `v3.2.12`:
  - `/Users/pcvantol/.platformio/penv/bin/pytest -q`
    -> ok, 314 passed, 13 skipped
  - `python -m compileall src tests` -> ok
  - `bash -n scripts/install.sh scripts/bootstrap_raspberry_pi_os.sh cleanup_old_releases.sh release.sh` -> ok
  - `git diff --check` -> ok
  - GitHub Actions publish workflow voor `v3.2.12` -> nog controleren na release
  - Source release assets voor `v3.2.12` -> nog controleren na release
  - Public release assets voor `v3.2.12` -> nog controleren na release

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
