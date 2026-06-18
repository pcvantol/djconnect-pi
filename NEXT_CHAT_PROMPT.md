# Next Chat Prompt

Use this prompt to initialize a fresh Codex chat for this repository:

```text
Werk in repo: /Users/pcvantol/Documents/GitHub/djconnect-pi

Lees eerst:
- AGENTS.md
- HANDOFF.md
- NEXT_CHAT_PROMPT.md
- git status --short

Belangrijke context:
- Dit is de Raspberry Pi client repo `pcvantol/djconnect-pi`.
- Canonical `client_type` is `raspberry_pi`.
- Device IDs gebruiken `djconnect-raspberry-pi-XXXXXXXXXXXX`.
- Geen PTT/mic/local DJ response audio toevoegen.
- Geen lokale `SYNC_PROMPTS.md` of `PRODUCT_ROADMAP.md`; die staan canoniek in `pcvantol/djconnect`.

Huidige stand:
- Laatste gepubliceerde release is `v3.1.73`.
- Public updater assets staan in `pcvantol/djconnect-pi-releases`, inclusief `djconnect-pi-latest.json`.
- Pi draaide nog `3.1.70`; updater via oude versie kan nog GitHub API rate-limit raken.
- Nieuwe unreleased wijzigingen na v3.1.73:
  - `CONTRIBUTING.md` toegevoegd voor MIT/projectbijdragen.
  - `scripts/install.sh` stopt/kilt `djconnect-client.service` en losse clientprocessen vroeg in de install.
  - `tests/test_installation_contract.py` test dit gedrag.
  - `NEXT_CHAT_PROMPT.md` bevat deze startprompt.
- Validatie na die laatste wijzigingen:
  - `bash -n scripts/install.sh`
  - `python3 -m pytest tests/test_installation_contract.py -q` -> 31 passed

Openstaande gewenste workflow:
- Maak desgevraagd een nieuwe release, vermoedelijk `v3.1.74`.
- Controleer daarna public publish workflow:
  `gh run list --workflow publish-release.yml --limit 3`
- Verifieer public assets:
  `gh release view v3.1.74 --repo pcvantol/djconnect-pi-releases --json tagName,url,assets`
- Deploy/updater op Pi kan pas betrouwbaar nadat de Pi voorbij `3.1.70` is, of via handmatige tarball install.

Handmatig client killen op Pi:
sudo systemctl stop djconnect-client.service
sudo pkill -TERM -f 'djconnect-pi-client|djconnect_pi\.app'
sleep 1
sudo pkill -KILL -f 'djconnect-pi-client|djconnect_pi\.app'

Houd bestaande user/uncommitted wijzigingen intact. Gebruik `apply_patch` voor edits. Run relevante tests.
```
