# Architecture

DJConnect Pi has four intentionally separate parts.

## Touch Client

`djconnect-pi-client` is the fullscreen Qt Quick/QML UI. It runs without root
privileges and talks to Home Assistant through a PySide6 backend object. It does
not host the local Client API.

Responsibilities:

- persist local client config
- pair with Home Assistant
- send periodic status
- send playback commands
- execute HA initiated playback commands received through the local
  command-event queue
- render now-playing and connection state
- keep Speelt nu focused on status, refresh, large album art and title/artist
- render HA-provided output-device choices on Bediening and dispatch
  `command:"set_output"`
- render HA-provided album art asynchronously in Now Playing, Queue and
  Playlists so image downloads do not block the QML UI thread
- render a dark DJConnect blue/purple gradient theme across touch screens
- handle touch gestures and animated control states
- display DJ response text pushed by Home Assistant as a 10-second toast
- show startup splash, blocking pairing and local demo mode
- blank the rendered screen after the configured timeout and wake on tap
- consume touch input on modal overlays so underlying settings controls cannot
  receive taps while logs, about, pairing, version mismatch or confirmation
  screens are visible

The app split is:

```text
src/djconnect_pi/app.py       PySide6 backend, properties, slots, polling
src/djconnect_pi/ha.py        Home Assistant outbound HTTP contract
src/djconnect_pi/qml/*.qml    touch UI, gestures and animations
```

## Local Client API

`djconnect-pi-api` is a separate daemon process installed as
`djconnect-api.service`. It is the only owner of the local HTTP API port and the
`_djconnect._tcp` mDNS advertisement. The HTTP API stays online after pairing,
but the mDNS advertisement is only active while the Pi is unpaired.

The same daemon serves the local Raspberry Pi web portal at `/`. Because the
portal is embedded in the Python package and exposed by `djconnect-api.service`,
normal install and updater flows install it and start it automatically on boot.
The portal includes a Diagnostics section backed by `/api/portal/state` with
Home Assistant API, local API, pairing and DJConnect systemd unit status.

Responsibilities:

- expose `GET /api/device/info`
- expose `GET /api/device/pairing-info`
- accept HA initiated pairing at `POST /api/device/pair`
- reset pairing at `POST /api/device/forget`
- expose `GET /api/debug/screenshot` for authenticated local diagnostics
- authenticate protected requests with the stored bearer token
- queue HA initiated playback commands for the UI process through a local
  command-event file
- request screenshots from the UI process through a local screenshot event file
  and return the saved PNG path once QML `grabToImage` completes
- advertise `device_id`, `client_type=raspberry_pi`, `version`,
  `device_name` and `local_url` through mDNS only while unpaired
- reject oversized HTTP request bodies
- reload the shared config before serving info/pairing-info or accepting local
  pairing so reset-pairing code rotation is reflected immediately

## Updater

`djconnect-pi-updater` checks GitHub Releases for the configured distribution
repo, default `pcvantol/djconnect-pi-releases`.
It downloads a `.tar.gz` release asset and matching `.sha256`, verifies the
checksum and installs the release under `/opt/djconnect/releases/<version>`.

The active release is selected by atomically replacing:

```text
/opt/djconnect/current -> /opt/djconnect/releases/<version>
```

After install, the updater restarts `djconnect-api.service` and
`djconnect-client.service`.
It also removes stale release directories after a successful install. The
default retention is the active `/opt/djconnect/current` release plus one
previous rollback release; leftover hidden `.tmp` unpack directories are always
deleted.
Python dependencies are installed from the bundled wheel using pip cache and
temporary files under `/var/cache/djconnect-pip`, matching the manual installer
so large wheels do not consume the default temporary filesystem.

The normal release closeout is to run `./cleanup_old_releases.sh --keep 1
--public --execute` after the source and public distribution releases have been
published. That removes old private releases/tags, old public distribution
releases/tags and completed tag workflow runs.

The source repo publishes release assets to the public distribution repo through
`.github/workflows/publish-release.yml` on `vX.Y.Z` tags. The workflow needs a
`DJCONNECT_PI_RELEASES_TOKEN` secret with release-write access to
`pcvantol/djconnect-pi-releases`.

Release bundles include `docs/`, `systemd/`, `scripts/install.sh` and a
prebuilt wheel under `wheels/`. They do not include the loose app source tree,
so a prepared Raspberry Pi can install the app from the public release tarball
without cloning the private source repository. Repo-only OS bootstrap helpers,
including `scripts/bootstrap_raspberry_pi_os.sh`, are excluded from release
tarballs.

## Maintenance

`djconnect-pi-maintenance` performs OS package maintenance. It can run:

```sh
apt-get update
apt-get -y upgrade
```

It only reboots when `--reboot` is passed and `/var/run/reboot-required` exists.
The systemd timer schedules this inside the configured maintenance window.

## Home Assistant Contract

The Pi client is an app-like DJConnect client.

```json
{
  "device_id": "djconnect-raspberry-pi-XXXXXXXXXXXX",
  "device_name": "DJConnect",
  "client_type": "raspberry_pi",
  "version": "3.1.57",
  "capabilities": {
    "touch": true,
    "voice": false,
    "local_audio": false,
    "local_dj_response_endpoint": true
  }
}
```

Runtime traffic uses:

- `POST /api/djconnect/pair`
- `POST /api/djconnect/status`
- `POST /api/djconnect/command`

Pairing, status and command payloads all include the stable `device_id` and
`client_type=raspberry_pi`. Command payloads also include the command name and
any command-specific value fields.

HA responses may include `ha_version` or `ha_major_minor`. The Pi enforces
major/minor compatibility: client `3.1.z` accepts HA `>=3.1.0` and `<3.2.0`.
When HA reports an incompatible version, the touch UI shows a blocking
version-mismatch screen and starts `djconnect-updater.service` once in the
background to try downloading a compatible client release.

The local Client API uses:

- `GET /api/device/info`
- `GET /api/device/pairing-info`
- `POST /api/device/pair`
- `POST /api/device/command`
- `POST /api/device/dj_response`
- `POST /api/device/forget`
- `POST /api/device/restart`
- `POST /api/device/shutdown`
- `GET /api/debug/screenshot`

`POST /api/device/restart` and `POST /api/device/shutdown` are Raspberry
Pi-specific endpoints used by Home Assistant power button entities. They use
the same bearer-token device auth as the other local `/api/device/*` endpoints
and also validate `X-DJConnect-Device-ID` when Home Assistant supplies it. The
HTTP response is returned before the Pi actually restarts or powers off.

The Postman collection in
`docs/postman/DJConnect Pi Local Client API.postman_collection.json` covers the
same local API plus diagnostic DJ response and screenshot testing.

`GET /api/debug/screenshot` requires `Authorization: Bearer <device_token>` once
the client is paired. It is intended for local support over SSH/LAN and may
expose the live touchscreen contents, so it should stay authenticated and local.

The Pi advertises `_djconnect._tcp` on the local Client API port only while it
is not paired. After pairing, the local API remains available for HA commands,
debug screenshots and text DJ responses, but discovery is stopped so HA does
not keep presenting the device as a new pairing candidate. DJ responses are
displayed as text on the wall screen and report `audio_played:false`.

Spotify credentials remain in Home Assistant.
