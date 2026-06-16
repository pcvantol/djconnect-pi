# Technical Design Decisions

This document is reverse-engineered from the current codebase. It records the
code-level design patterns, coding conventions and third-party dependency model
used by DJConnect Pi. Keep it current for every release that changes code,
packaging, runtime services or dependencies.

## Scope

DJConnect Pi is a Raspberry Pi OS Lite kiosk client with:

- a PySide6/Python backend and Qt Quick/QML touch UI
- a separate local HTTP Client API daemon with mDNS discovery
- a separate GitHub release updater
- a separate apt maintenance command
- systemd services/timers for process supervision
- shell scripts for release installation and repo-only OS bootstrap

The source of truth for runtime package constraints is `pyproject.toml`.
The source of truth for OS bootstrap packages is
`scripts/bootstrap_raspberry_pi_os.sh`. The release installer intentionally does
not install apt packages.

## Python Design Patterns

| Pattern | Where | Why |
| --- | --- | --- |
| Backend-for-frontend QObject | `src/djconnect_pi/app.py` | Exposes typed Qt properties, signals and slots to QML while keeping HTTP/config logic in Python. |
| Signal/slot state propagation | `DJConnectBackend` signals and `_apply_*` methods | Keeps QML declarative: QML observes backend properties and Python emits updates after HA/API work. |
| Worker-thread offload | `ThreadPoolExecutor` in `app.py` | Prevents HA command/status calls and media-list preparation from blocking the UI thread. |
| In-flight request guard | `loadQueue`, `loadPlaylists` | Prevents repeated touch/navigation taps from flooding Home Assistant or stacking expensive work. |
| Immediate list emission with background artwork cache | `_load_queue_worker`, `_load_playlists_worker`, `_cache_media_artwork_async` | Shows Queue/Playlist text and play controls as soon as HA returns, while slower artwork downloads happen afterward on a worker. |
| Backend health state | `backendAvailable`, `AuthenticationError`, `BackendUnavailable` | Keeps pairing state separate from live HA/backend reachability, letting the kiosk show red/green status and short toasts without losing pairing. |
| Bounded log display | `_read_tail_text`, `_format_logs_for_display` | Prevents large persistent log files from freezing the UI when the user opens Logs on a Pi Zero 2 W. |
| Event-file bridge | `client_api_daemon.py` + `app.py` local event polling | Keeps the API daemon separate from the UI process while still letting HA-triggered commands affect the live UI. |
| Separate daemon boundary | `djconnect-pi-api`, `djconnect-pi-client`, `djconnect-pi-updater`, `djconnect-pi-maintenance` entrypoints | Avoids port ownership conflicts and keeps UI, API, updater and OS maintenance independently supervised by systemd. |
| Dataclass config model | `src/djconnect_pi/config.py` | Provides a stable, serializable config shape with defaults and migration/backfill logic. |
| Atomic config writes | `save_config` | Reduces risk of corrupting pairing/config data on power loss. |
| Protocol facade | `HAClient` in `src/djconnect_pi/ha.py` | Centralizes Home Assistant URL construction, payload shape, version compatibility and response parsing. |
| Parser normalization | `playback_from_status`, `parse_queue_items`, `parse_playlist_items` | Accepts HA contract aliases, treats `success:true` with empty playback as valid and exposes one UI-friendly model shape. |
| Defensive protocol validation | `_compatible_ha_version`, local API auth, body size checks | Fails early on incompatible HA versions, oversized local requests or missing bearer tokens. |
| Immutable-ish runtime constants | `CLIENT_TYPE`, `PROTOCOL_VERSION` | Keeps protocol identity explicit and testable. |
| Resource-aware installer/updater | `scripts/install.sh`, `updater.py` | Pi Zero 2 W has limited RAM/IO; installs check disk/swap and use cache-local pip temp directories. |
| Test-as-contract | `tests/test_*` | Tests assert protocol payloads, systemd/service contracts, release bundle contents and QML structure. |
| Shared examples as docs contract | `examples/voice_intents.json` | Keeps website/docs intent examples aligned with HA/ESP post-STT behavior without adding local Pi voice capture. |

### Python Conventions

| Convention | Evidence/source |
| --- | --- |
| Python 3.11+ syntax and typing | `pyproject.toml` has `requires-python = ">=3.11"`; modules use `from __future__ import annotations`, `list[...]`, `dict[...]` and typed signatures. |
| Standard library first, third-party next, local imports last | Visible consistently in `src/djconnect_pi/*.py`. |
| `pathlib.Path` for filesystem paths | Used across config, updater, installer tests and daemon code. |
| `logging.getLogger(__name__)` per module | Used in app, HA client, API daemon, updater and system-info modules. |
| No broad framework dependency injection container | Objects are composed explicitly from config/client classes. |
| HTTP timeouts are mandatory on external requests | HA client and updater use `requests` with explicit timeouts. |
| HA/UI performance paths log elapsed milliseconds | `ha.py` and `app.py` use `time.monotonic()` around HTTP calls and UI workers. |
| User-facing strings go through translation keys | `src/djconnect_pi/i18n.py`; QML calls `djconnect.t(...)`; tests assert translation parity. |
| Sensitive runtime state is kept outside release directories | Config/logs live under `/opt/djconnect/config` and `/opt/djconnect/logs`; releases live under `/opt/djconnect/releases/<version>`. |
| Console entrypoints are declared in package metadata | `pyproject.toml` `[project.scripts]`. |
| Tests prefer focused contract assertions | `tests/test_installation_contract.py`, `tests/test_qml.py`, `tests/test_client_api.py`. |

No formatter/linter configuration such as Black, Ruff, Flake8 or Mypy is
currently present in the repo. Style is therefore convention-based and enforced
mainly by tests plus `compileall`.

## QML / Qt Quick Design Patterns

| Pattern | Where | Why |
| --- | --- | --- |
| Declarative shell with Python backend | `src/djconnect_pi/qml/Main.qml` | QML owns rendering and touch interaction; Python owns state, IO and persistence. |
| Local reusable components | `PurpleButton`, `NavButton`, `IconButton`, `MediaListPanel`, `MediaPlayButton` in `Main.qml`; `GamesPanel.qml` | Keeps the kiosk UI visually consistent without a separate component package. |
| Full-screen state panels | Now Playing, Queue, Playlists, Games, Settings, logs, about and pairing overlays | Prevents background screen tap-through and matches kiosk operation. |
| Modal touch blockers | `ModalBlocker` | Consumes pointer/wheel events while overlays are visible. |
| Fixed touch target dimensions | bottom nav, media rows, media play buttons, Bediening controls | Reduces layout shift on a 720x720 4-inch touch display. |
| Display/control screen split | `nowPanel`, `controlPanel` in `Main.qml` | Keeps Speelt nu readable as a large album-art status screen while Bediening can dedicate the full page to larger touch playback controls. |
| Shared app background component | `AppBackground` in `Main.qml` | Keeps Speelt nu, Bediening, Queue, Playlists, Logs, Settings and About visually consistent and avoids one-off screen backgrounds. |
| Explicit media-list row geometry | `MediaListPanel` delegates place artwork, text and play button with x/y/width expressions | Avoids `RowLayout` and cross-item anchor ordering differences on the Pi runtime that previously misplaced or hid album art, titles and play icons. |
| Async image rendering | `Image { asynchronous: true }` | Lets QML decode/render artwork without blocking interaction. Network/cache preparation is handled outside QML delegates. |
| Canvas icons only where dynamic state matters | playback controls and game canvas | Avoids external icon packs while keeping touch controls scalable. |
| Kiosk-first navigation | bottom menu bar and no visible app close button | Device is intended to be wall-mounted and dedicated. |

### QML Conventions

| Convention | Evidence/source |
| --- | --- |
| Imports are explicit Qt modules | `import QtQuick`, `QtQuick.Controls`, `QtQuick.Layouts`, `QtQuick.Window`. |
| Root screen size is 720x720 | `Window { width: 720; height: 720 }`, matching HyperPixel square target. |
| Colors are literal design tokens in QML | Existing code uses hardcoded DJConnect blue/purple values. No external theme file exists. |
| Text is localized through backend | QML uses `djconnect.t("...")` for user-facing copy. |
| Buttons use fixed radii and dimensions | Most button backgrounds use `radius: 8`; media play uses fixed 68x58. |
| Avoid blocking Python calls from delegates | Queue/playlist rows must not call `cachedImageUrl()`; backend pre-caches artwork before updating the QML model. |
| Opaque main screens | Logs, Over and Instellingen use fully opaque backgrounds | Prevents underlying Speelt nu controls/content from bleeding through kiosk screens. |

## Shell / Systemd Design Patterns

| Pattern | Where | Why |
| --- | --- | --- |
| Strict shell mode | `set -euo pipefail` in shell scripts | Fails fast on missing variables and command errors. |
| Environment-overridable defaults | `DJCONNECT_*="${DJCONNECT_*:-...}"` | Allows release/install customization without editing scripts. |
| Idempotent/resumable install markers | `/opt/djconnect/install-state/<version>/*.done` | Allows retry after freeze/reboot during dependency installation. |
| Atomic release activation | `/opt/djconnect/current -> /opt/djconnect/releases/<version>` | Makes upgrades switch at symlink level after validation. |
| Separate systemd units | `systemd/*.service`, `systemd/*.timer` | Keeps API, UI, updater, maintenance and screen schedule isolated. |
| Narrow sudoers rule | installer writes `djconnect-reboot` | Allows only reboot, poweroff and starting `djconnect-updater.service` from the runtime user. |
| OS bootstrap excluded from release tarball | release script copies only app install material | Keeps Raspberry Pi OS preparation out of the app release cycle. |

### Shell Conventions

| Convention | Evidence/source |
| --- | --- |
| Bash scripts are executable and tested | `tests/test_installation_contract.py` asserts executable bit and shell contract. |
| Installer does not run `apt-get install` | Tests assert OS bootstrap tasks are absent from `scripts/install.sh`. |
| Bootstrap owns OS packages | `scripts/bootstrap_raspberry_pi_os.sh` contains apt package list. |
| Scripts print clear step headings | `log()` helper emits `==>` sections. |
| Resource output around heavy steps | `print_resources()` prints memory, swap, disk and inode state. |

## HTTP / Protocol Design Decisions

| Decision | Code source | Rationale |
| --- | --- | --- |
| Canonical Pi client type is `raspberry_pi` | `CLIENT_TYPE` in `config.py` | HA validates client family; this must not regress to command-only payloads. |
| Device IDs use `djconnect-raspberry-pi-XXXXXXXXXXXX` | `config.py` | Stable app-like Pi identity, separate from ESP IDs. |
| Local API is separate from UI | `client_api_daemon.py`, systemd units | Avoids port conflicts and keeps HTTP available if the UI restarts. |
| mDNS type is `_djconnect._tcp` while unpaired | `client_api.py` | HA autodiscovery should help pair new clients, but already paired Pi clients should not keep appearing as pairing candidates. |
| `GET /api/debug/screenshot` is authenticated after pairing except loopback | `client_api.py` | Screenshot may expose live screen content; LAN callers need the bearer token, while SSH diagnostics can use `127.0.0.1` without reading the token file. |
| `GET /api/debug/screen` is loopback-only | `client_api.py`, `app.py`, `Main.qml` | Allows post-deploy screenshot automation without exposing screen-control routes on the LAN. |
| Pi power endpoints are explicit and Pi-only | `POST /api/device/restart`, `POST /api/device/shutdown` in `client_api.py` | HA can expose Raspberry Pi restart/shutdown buttons without introducing ESP-only `/api/device/reboot` or OTA behavior. |
| Text DJ responses are toast-only | `app.py`, `client_api_daemon.py` | Product decision: no local Pi audio/DJ response playback. |
| HA version compatibility is major/minor bounded | `ha.py` | Client `3.1.z` accepts HA `>=3.1.0` and `<3.2.0`. |
| Output-device selector uses status plus devices fallback | `app.py`, `ha.py` | Bediening must let users switch HA-provided playback devices even when the status response omits the device list. |
| Output-device changes are optimistic but validated | `_set_output_worker` | The UI feels responsive, but if HA rejects or normalizes the selected output device the client rolls back and logs the rejection. |
| Web portal shares the local API daemon | `client_api.py`, `web_portal.py` | Keeps browser diagnostics and controls on the same always-on Client API URL used for pairing, avoiding another supervised process. |
| Portal stays on the Client API port by default | `Config.local_api_port` | Binding to port 80 would require root or Linux capabilities; the safer default is the existing local API port with an optional future reverse proxy if needed. |
| Portal diagnostics normalize component health | `client_api_daemon.py` | Converts systemd service/timer states to running/stopped/failed/unknown so the browser UI can show DJConnect component health consistently. |
| HTTP 401 is an authentication state | `AuthenticationError` in `ha.py`, `_run` in `app.py` | Prevents raw HA JSON from being shown on the kiosk and turns the connection dot red with a concise translated toast/status. |
| Backend unavailable is not a UI crash state | `BackendUnavailable` in `ha.py`, `_run` in `app.py` | Spotify/HA backend downtime is surfaced as a short status/toast while the UI remains interactive. |

## Dependency Inventory

### Python Runtime Dependencies

Versions below are package constraints from `pyproject.toml` plus the concrete
versions observed during the 3.1.42 Pi install where available. Transitive
dependencies are listed because they are installed into the release venv.

| Package | Constraint / observed version | Used by | License model | Source URL |
| --- | --- | --- | --- | --- |
| Python | `>=3.11`; observed Pi Python `3.13.5` | all Python entrypoints | Python Software Foundation License | https://www.python.org/ |
| PySide6 | `>=6.7`; observed `6.11.1` | Qt Quick/QML UI bridge | LGPL-3.0-only/GPL-3.0-only/commercial Qt licensing | https://pypi.org/project/PySide6/ |
| PySide6_Addons | transitive; observed `6.11.1` | PySide6 runtime | LGPL-3.0-only/GPL-3.0-only/commercial Qt licensing | https://pypi.org/project/PySide6-Addons/ |
| PySide6_Essentials | transitive; observed `6.11.1` | PySide6 runtime | LGPL-3.0-only/GPL-3.0-only/commercial Qt licensing | https://pypi.org/project/PySide6-Essentials/ |
| shiboken6 | transitive; observed `6.11.1` | PySide6 binding generator/runtime | LGPL-3.0-only/GPL-3.0-only/commercial Qt licensing | https://pypi.org/project/shiboken6/ |
| requests | `>=2.31`; observed `2.34.2` | HA HTTP, updater GitHub HTTP, album-art cache | Apache-2.0 | https://pypi.org/project/requests/ |
| certifi | transitive; observed `2026.5.20` | TLS CA bundle for requests | MPL-2.0 | https://pypi.org/project/certifi/ |
| charset-normalizer | transitive; observed `3.4.7` | requests text decoding | MIT | https://pypi.org/project/charset-normalizer/ |
| idna | transitive; observed `3.18` | requests IDNA support | BSD-3-Clause | https://pypi.org/project/idna/ |
| urllib3 | transitive; observed `2.7.0` | requests HTTP transport | MIT | https://pypi.org/project/urllib3/ |
| zeroconf | `>=0.132`; observed `0.149.16` | `_djconnect._tcp` mDNS advertisement | LGPL-2.1-or-later | https://pypi.org/project/zeroconf/ |
| ifaddr | transitive; observed `0.2.0` | zeroconf network interface discovery | MIT | https://pypi.org/project/ifaddr/ |

### Python Build/Test Dependencies

| Package/tool | Constraint / version source | Used by | License model | Source URL |
| --- | --- | --- | --- | --- |
| setuptools | build requirement `>=68` | PEP 517 build backend | MIT | https://pypi.org/project/setuptools/ |
| pip | OS/venv managed; observed updater upgraded to `26.1.2` | wheel/install operations | MIT | https://pypi.org/project/pip/ |
| pytest | dev dependency `>=8`; local test run used `9.0.3` | test suite | MIT | https://pypi.org/project/pytest/ |
| pluggy | pytest transitive; local test run used `1.6.0` | pytest plugin system | MIT | https://pypi.org/project/pluggy/ |
| anyio | local pytest plugin environment used `4.13.0` | test plugin environment on maintainer machine | MIT | https://pypi.org/project/anyio/ |

### Python Standard Library Modules

These are not third-party dependencies and follow the Python license:

`argparse`, `concurrent.futures`, `dataclasses`, `hashlib`, `http`,
`http.server`, `importlib.resources`, `json`, `locale`, `logging`,
`logging.handlers`, `os`, `pathlib`, `platform`, `re`, `secrets`, `shutil`,
`signal`, `socket`, `stat`, `subprocess`, `sys`, `tarfile`, `tempfile`,
`threading`, `time`, `typing`, `unittest.mock`, `urllib.parse`, `uuid`.

### QML / Qt Modules

Qt module versions are supplied by the installed PySide6/Qt runtime. The 3.1.42
Pi install observed PySide6 `6.11.1`.

| Module | Version source | Used by | License model | Source URL |
| --- | --- | --- | --- | --- |
| Qt Quick | PySide6/Qt runtime | QML scene, animations, Canvas, Image, handlers | Qt LGPL/GPL/commercial | https://doc.qt.io/qt-6/qtquick-index.html |
| Qt Quick Controls | PySide6/Qt runtime | Button, ComboBox, Slider, SpinBox, ScrollView | Qt LGPL/GPL/commercial | https://doc.qt.io/qt-6/qtquickcontrols-index.html |
| Qt Quick Layouts | PySide6/Qt runtime | RowLayout, ColumnLayout sizing | Qt LGPL/GPL/commercial | https://doc.qt.io/qt-6/qtquicklayouts-index.html |
| Qt Quick Window | PySide6/Qt runtime | Fullscreen/windowed application shell | Qt LGPL/GPL/commercial | https://doc.qt.io/qt-6/qml-qtquick-window-window.html |

### OS / Apt Dependencies

The bootstrap installs these packages from the Raspberry Pi OS/Debian
repositories. Versions are intentionally not pinned in this repo; the installed
version depends on the Raspberry Pi OS Lite 64-bit image and apt repository
state. License metadata is maintained by Debian/Raspberry Pi packages in
`/usr/share/doc/<package>/copyright` on the device.

| Package | Version model | Used by | License/source reference |
| --- | --- | --- | --- |
| `ca-certificates` | OS repository managed | TLS trust store for curl/Python | https://packages.debian.org/trixie/ca-certificates |
| `curl` | OS repository managed | release downloads, GitHub reachability checks | https://packages.debian.org/trixie/curl |
| `git` | OS repository managed | repo checkout/bootstrap workflow | https://packages.debian.org/trixie/git |
| `jq` | OS repository managed | shell JSON utility for operators | https://packages.debian.org/trixie/jq |
| `libegl1` | OS repository managed | Qt/OpenGL runtime | https://packages.debian.org/trixie/libegl1 |
| `libgl1` | OS repository managed | Qt/OpenGL runtime | https://packages.debian.org/trixie/libgl1 |
| `libxkbcommon-x11-0` | OS repository managed | Qt X11 keyboard/input runtime | https://packages.debian.org/trixie/libxkbcommon-x11-0 |
| `libxcb-cursor0` | OS repository managed | Qt xcb platform plugin runtime | https://packages.debian.org/trixie/libxcb-cursor0 |
| `libxcb-icccm4` | OS repository managed | Qt xcb platform plugin runtime | https://packages.debian.org/trixie/libxcb-icccm4 |
| `libxcb-image0` | OS repository managed | Qt xcb platform plugin runtime | https://packages.debian.org/trixie/libxcb-image0 |
| `libxcb-keysyms1` | OS repository managed | Qt xcb platform plugin runtime | https://packages.debian.org/trixie/libxcb-keysyms1 |
| `libxcb-randr0` | OS repository managed | Qt xcb platform plugin runtime | https://packages.debian.org/trixie/libxcb-randr0 |
| `libxcb-render-util0` | OS repository managed | Qt xcb platform plugin runtime | https://packages.debian.org/trixie/libxcb-render-util0 |
| `libxcb-shape0` | OS repository managed | Qt xcb platform plugin runtime | https://packages.debian.org/trixie/libxcb-shape0 |
| `libxcb-xinerama0` | OS repository managed | Qt xcb platform plugin runtime | https://packages.debian.org/trixie/libxcb-xinerama0 |
| `libxcb-xinput0` | OS repository managed | Qt xcb touch/input runtime | https://packages.debian.org/trixie/libxcb-xinput0 |
| `locales` | OS repository managed | `en_GB.UTF-8`, `nl_NL.UTF-8` locale generation | https://packages.debian.org/trixie/locales |
| `python3-pip` | OS repository managed | bootstrap/venv package tooling | https://packages.debian.org/trixie/python3-pip |
| `python3-venv` | OS repository managed | release virtualenv creation | https://packages.debian.org/trixie/python3-venv |
| `ssh` | OS repository managed | remote maintenance and deploy access | https://packages.debian.org/trixie/ssh |
| `unzip` | OS repository managed | operator utility | https://packages.debian.org/trixie/unzip |
| `x11-xserver-utils` | OS repository managed | X11 utilities | https://packages.debian.org/trixie/x11-xserver-utils |
| `xinit` | OS repository managed | systemd-started X11 kiosk session | https://packages.debian.org/trixie/xinit |
| `xserver-xorg` | OS repository managed | X server for Qt kiosk UI | https://packages.debian.org/trixie/xserver-xorg |
| `xserver-xorg-video-fbdev` | OS repository managed | framebuffer Xorg video driver fallback | https://packages.debian.org/trixie/xserver-xorg-video-fbdev |
| `xserver-xorg-input-libinput` | OS repository managed | touch input driver | https://packages.debian.org/trixie/xserver-xorg-input-libinput |
| `rpi-connect` | Raspberry Pi OS repository managed, optional | optional remote access bootstrap | https://www.raspberrypi.com/software/connect/ |
| `raspi-config` | Raspberry Pi OS image tool, not installed by this repo | rootfs expansion, SSH, boot behavior, I2C/SPI toggles | https://github.com/RPi-Distro/raspi-config |
| `systemd` | Raspberry Pi OS base system | service/timer supervision | https://systemd.io/ |

### External Services / Distribution Dependencies

| Service | Used by | Version model | Source URL |
| --- | --- | --- | --- |
| GitHub Releases | private source release and public Pi distribution release | SaaS API; not pinned | https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases |
| GitHub Actions | publish tagged source releases to public release repo | SaaS runner; workflow-defined | https://docs.github.com/en/actions |
| Home Assistant DJConnect integration | pairing, status and playback command contract | compatible `3.1.x` integration expected | https://www.home-assistant.io/ |
| Raspberry Pi OS Lite 64-bit | target operating system | image/repository state controlled outside repo | https://www.raspberrypi.com/software/operating-systems/ |

## Release Maintenance Rule

For every future DJConnect Pi release:

- update this document if code structure, patterns, service boundaries,
  dependencies, dependency versions, OS package requirements, packaging or
  release flow changes
- update `README.md`, `CHANGELOG.md`, `HANDOFF.md`, `TESTS.md`, `TODO.md`,
  `ISSUES.md` and relevant `docs/` files
- extend tests when a design decision becomes a regression risk
- keep changelog entries per release; do not consolidate historical versions
- after release deploy to the Pi, capture and attach a live Pi screenshot when
  remote capture is available
