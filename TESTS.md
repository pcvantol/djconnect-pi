# Tests

Install development dependencies:

```sh
python3 -m pip install -e ".[dev]"
```

Run the full suite:

```sh
python3 -m pytest
```

Run syntax/package smoke checks:

```sh
python3 -m compileall src tests
QT_QPA_PLATFORM=offscreen python3 -m djconnect_pi.app --windowed --exit-after-ms 1500
```

## Coverage Areas

- config creation, persistence and device ID backfill
- Home Assistant pairing/status/command payloads
- playback response alias parsing
- protocol mismatch error handling
- PySide backend properties and command dispatch
- persistent logging and redaction
- bundled QML files and offscreen QML load
- updater release asset selection, SHA256 verification and atomic install
- updater stable/beta prerelease channel handling
- apt maintenance windows, upgrade command flow and reboot gating
