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
- Geen PTT/mic/local DJ response audio toevoegen.
- Geen lokale `SYNC_PROMPTS.md` of `PRODUCT_ROADMAP.md`; die staan canoniek in `pcvantol/djconnect`.

Huidige stand:
- Laatste gepubliceerde release is `v3.1.78`.
- Public updater assets staan in `pcvantol/djconnect-pi-releases`, inclusief `djconnect-pi-latest.json`.
- Release `v3.1.78` is gepubliceerd in source en public distribution repo.
- Public assets voor `v3.1.78` zijn geverifieerd:
  - `djconnect-pi-3.1.78.tar.gz`
  - `djconnect-pi-3.1.78.sha256`
  - `djconnect-pi-latest.json`
- Cleanup is gedraaid met `./cleanup_old_releases.sh --keep 1 --public --execute`; alleen `v3.1.78` blijft over als recente source/public release.
- Pi draaide eerder nog `3.1.72`; updater/install via oude versies kon rebooten tijdens monolithische dependency-install.
- Validatie voor `v3.1.78`:
  - `bash -n scripts/install.sh`
  - `python3.11 -m pytest tests/test_installation_contract.py tests/test_updater.py -q` -> 56 passed
  - GitHub Actions publish workflow voor `v3.1.78` -> success

Openstaande gewenste workflow:
- Bij een volgende release: actualiseer `CHAT_BOOTSTRAP.md` als onderdeel van de release closeout.
- Controleer na elke release de public publish workflow:
  `gh run list --workflow publish-release.yml --limit 3`
- Verifieer na elke release de public assets:
  `gh release view vX.Y.Z --repo pcvantol/djconnect-pi-releases --json tagName,url,assets`
- Deploy/updater op Pi gebruikt vanaf `v3.1.78` resumable dependency install markers voor reboot/interruption retries, inclusief losse PySide6-subpackages, en de handmatige installer schakelt eerst de oude updater-timer uit.

Handmatig client killen op Pi:
sudo systemctl stop djconnect-client.service
sudo pkill -TERM -f 'djconnect-pi-client|djconnect_pi\.app'
sleep 1
sudo pkill -KILL -f 'djconnect-pi-client|djconnect_pi\.app'

Houd bestaande user/uncommitted wijzigingen intact. Gebruik `apply_patch` voor edits. Run relevante tests.
```
