# Architecture

DJConnect Pi has three intentionally separate parts.

## Touch Client

`djconnect-pi-client` is the fullscreen Qt Quick/QML UI. It runs without root
privileges and talks only to Home Assistant through a PySide6 backend object.

Responsibilities:

- persist local client config
- pair with Home Assistant
- send periodic status
- send playback commands
- render now-playing and connection state
- handle touch gestures and animated control states

It does not expose local HTTP endpoints in the initial product shape.

The app split is:

```text
src/djconnect_pi/app.py       PySide6 backend, properties, slots, polling
src/djconnect_pi/ha.py        Home Assistant HTTP contract
src/djconnect_pi/qml/*.qml    touch UI, gestures and animations
```

## Updater

`djconnect-pi-updater` checks GitHub Releases for `pcvantol/djconnect-pi`.
It downloads a `.tar.gz` release asset and matching `.sha256`, verifies the
checksum and installs the release under `/opt/djconnect/releases/<version>`.

The active release is selected by atomically replacing:

```text
/opt/djconnect/current -> /opt/djconnect/releases/<version>
```

After install, the updater restarts `djconnect-client.service`.

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
  "device_name": "DJConnect Pi",
  "client_type": "raspberry_pi",
  "version": "3.1.17",
  "capabilities": {
    "touch": true,
    "voice": false,
    "local_audio": false,
    "local_dj_response_endpoint": false
  }
}
```

Runtime traffic uses:

- `POST /api/djconnect/pair`
- `POST /api/djconnect/status`
- `POST /api/djconnect/command`

Spotify credentials remain in Home Assistant.
