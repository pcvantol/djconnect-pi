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
- Canonical `client_type` is `raspberry_pi`.
- Device IDs gebruiken `djconnect-raspberry-pi-XXXXXXXXXXXX`.
- Geen PTT/mic/local DJ response audio toevoegen.
- Geen lokale `SYNC_PROMPTS.md` of `PRODUCT_ROADMAP.md`; die staan canoniek in `pcvantol/djconnect`.

Huidige stand:
- Laatste gepubliceerde release is `v3.1.74`.
- Public updater assets staan in `pcvantol/djconnect-pi-releases`, inclusief `djconnect-pi-latest.json`.
- Release `v3.1.74` is gepubliceerd in source en public distribution repo.
- Public assets voor `v3.1.74` zijn geverifieerd:
  - `djconnect-pi-3.1.74.tar.gz`
  - `djconnect-pi-3.1.74.sha256`
  - `djconnect-pi-latest.json`
- Cleanup is gedraaid met `./cleanup_old_releases.sh --keep 1 --public --execute`; alleen `v3.1.74` blijft over als recente source/public release.
- Pi draaide eerder nog `3.1.70`; updater via oude versie kan nog GitHub API rate-limit raken.
- Validatie voor `v3.1.74`:
  - `bash -n scripts/install.sh`
  - `python3.11 -m pytest tests/test_installation_contract.py -q` -> 31 passed
  - GitHub Actions publish workflow voor `v3.1.74` -> success

Openstaande gewenste workflow:
- Bij een volgende release: actualiseer `CHAT_BOOTSTRAP.md` als onderdeel van de release closeout.
- Controleer na elke release de public publish workflow:
  `gh run list --workflow publish-release.yml --limit 3`
- Verifieer na elke release de public assets:
  `gh release view vX.Y.Z --repo pcvantol/djconnect-pi-releases --json tagName,url,assets`
- Deploy/updater op Pi kan pas betrouwbaar nadat de Pi voorbij `3.1.70` is, of via handmatige tarball install.

Handmatig client killen op Pi:
sudo systemctl stop djconnect-client.service
sudo pkill -TERM -f 'djconnect-pi-client|djconnect_pi\.app'
sleep 1
sudo pkill -KILL -f 'djconnect-pi-client|djconnect_pi\.app'

Houd bestaande user/uncommitted wijzigingen intact. Gebruik `apply_patch` voor edits. Run relevante tests.
```
