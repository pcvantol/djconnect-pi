# Contributing to DJConnect

Thanks for helping improve DJConnect.

This repository is part of the DJConnect project and is MIT-licensed. Related
DJConnect repositories are also MIT-licensed unless their own repository
metadata or a third-party dependency states otherwise. See the local
[`LICENSE`](LICENSE) for the project license.

## What Belongs Here

This repository contains the Raspberry Pi DJConnect client:

- Raspberry Pi touch UI and local Client API source.
- Raspberry Pi web portal source served by the local Client API.
- Docs, tests, build scripts, systemd units and release workflow files.
- Public release-bundle contents for the Pi app, including installer scripts
  and service/timer templates.

Do not commit secrets, tokens, Wi-Fi passwords, OAuth credentials, private user
data, local diagnostics containing secrets or logs containing credentials.

## Development Setup

Use Python 3.11 or newer.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```

Run the test suite:

```sh
python3 -m pytest
```

Run the installer contract tests when changing packaging, bootstrap, systemd or
release behavior:

```sh
python3 -m pytest tests/test_installation_contract.py -q
```

Run a desktop development client:

```sh
djconnect-pi-client --windowed
```

Run a headless smoke test:

```sh
QT_QPA_PLATFORM=offscreen djconnect-pi-client --windowed --exit-after-ms 1500
```

Build and dry-run the release flow:

```sh
./release.sh X.Y.Z --dry-run
```

Use the next semantic version for real releases.

## Cross-Repo Contract

Changes to protocol, endpoints, client types, pairing, updater behavior,
Assist/STT/TTS expectations, Spotify playback, queue payloads, branding or
shared user-facing terminology must be coordinated with the wider DJConnect
project.

Coordinate with:

- `pcvantol/djconnect` for the Home Assistant integration.
- Relevant DJConnect client or firmware repositories.
- `SYNC_PROMPTS.md` in `pcvantol/djconnect` when the shared contract changes.
- `PRODUCT_ROADMAP.md` in `pcvantol/djconnect` when roadmap or product intent
  changes.

Do not add local copies of `SYNC_PROMPTS.md` or `PRODUCT_ROADMAP.md` in this
repository.

## Contribution Guidelines

- Follow the community standards in [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
- Keep changes small and focused.
- Add tests for code, packaging or contract changes.
- Update docs and examples when behavior, setup or user-facing text changes.
- Keep secrets out of commits, logs and diagnostics.
- Preserve the Raspberry Pi client contract: `client_type` is `raspberry_pi`,
  and device IDs use `djconnect-raspberry-pi-XXXXXXXXXXXX`.
- Keep app updates, OS maintenance and the touch UI as separate processes.
- Respect Spotify trademark and non-affiliation: DJConnect is not affiliated
  with, endorsed by or sponsored by Spotify AB.
- Use real DJConnect brand assets; do not redraw the logo or icon unless the
  asset is intentionally being replaced.

## AI-Assisted Development

DJConnect is developed and maintained with AI-assisted and agentic engineering
workflows, including Codex. AI assistance may be used for code changes,
documentation, tests, release preparation and cross-repo consistency checks.

All accepted changes remain maintainer-reviewed. Contributors are responsible
for ensuring their changes are correct, testable, license-compatible and free of
secrets or private data. Do not include tokens, passwords, private URLs,
personal data or proprietary third-party material in prompts, issues, logs,
screenshots or test fixtures.

## Pull Requests

Before opening a PR:

1. Run the repo-specific tests and relevant build or release dry-run commands.
2. Check `git status`.
3. Describe what changed.
4. List the checks you ran.
5. Note any impact on other DJConnect repositories.
6. For release or Ask DJ/status behavior changes, review this repo against the
   `DJ Announcement Output Sync` section in
   `pcvantol/djconnect/SYNC_PROMPTS.md`. For Raspberry Pi, confirm only
   `text_only` and, when HA reports a configured speaker, `ha_speaker` are
   exposed, and never add local TTS/audio playback.

## Releases

Releases use semantic versions and `vX.Y.Z` Git tags.

The normal release command is:

```sh
./release.sh X.Y.Z
```

The release script updates version metadata, builds a wheel-based release
tarball, writes a checksum, commits, tags, pushes `main`, pushes the tag and
creates the source GitHub release.

The source repository publishes public distribution artifacts to
`pcvantol/djconnect-pi-releases` through `.github/workflows/publish-release.yml`.
The public release contains the Pi install tarball, checksum and
`djconnect-pi-latest.json` manifest used by the stable updater.

After release, verify the public release assets and update related DJConnect
repositories when the release changes shared contracts, Home Assistant
integration behavior, docs or product roadmap. Also update
`CHAT_BOOTSTRAP.md` so a fresh Codex chat starts from the current release
state, validation status and next expected action. Clean out stale files in
`screenshots/` and regenerate the current 720x720 screen set after a successful
install or UI validation so release screenshots never mix old and new versions.

## Licensing

By contributing to this repository, you agree that your contribution is licensed
under the MIT License in `LICENSE`.

Spotify is a trademark of Spotify AB. DJConnect is not affiliated with,
endorsed by, or sponsored by Spotify AB.
