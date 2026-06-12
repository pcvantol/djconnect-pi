#!/usr/bin/env bash
set -euo pipefail

DJCONNECT_VERSION="${DJCONNECT_VERSION:-3.1.16}"
DJCONNECT_REPO="${DJCONNECT_REPO:-pcvantol/djconnect-pi-releases}"
DJCONNECT_HA_URL="${DJCONNECT_HA_URL:-http://homeassistant.local:8123}"
DJCONNECT_RUNTIME_USER="${DJCONNECT_RUNTIME_USER:-djconnect}"
DJCONNECT_ROOT="${DJCONNECT_ROOT:-/opt/djconnect}"

usage() {
  cat <<EOF
Usage:
  sudo ./scripts/install_raspberry_pi.sh

Version:
  DJConnect Pi installer for client ${DJCONNECT_VERSION}

Environment:
  DJCONNECT_VERSION=${DJCONNECT_VERSION}
  DJCONNECT_REPO=pcvantol/djconnect-pi-releases
  DJCONNECT_HA_URL=http://homeassistant.local:8123
  DJCONNECT_RUNTIME_USER=djconnect
  DJCONNECT_ROOT=/opt/djconnect

This installs or updates the DJConnect Pi application only:
- creates/updates the dedicated runtime user and /opt/djconnect layout
- downloads and verifies the selected public DJConnect Pi release
- preserves existing pairing/configuration
- installs/refreshes the local Client API, frontend, updater, maintenance and
  night screen schedule systemd units
- restarts the DJConnect API and touch UI services

General Raspberry Pi OS bootstrap tasks, such as timezone, SSH, apt full-upgrade,
glances, Raspberry Pi Connect and HyperPixel display setup, are intentionally
handled by scripts/bootstrap_raspberry_pi_os.sh from a source checkout. That
bootstrap script is not shipped in release tarballs.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: sudo $0" >&2
  exit 1
fi

log() {
  printf '\n==> %s\n' "$*"
}

check_runtime_dependencies() {
  log "Checking DJConnect installer dependencies"
  local missing=()
  for command_name in curl shasum tar python3 systemctl useradd install; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
      missing+=("$command_name")
    fi
  done

  if ! python3 -m venv --help >/dev/null 2>&1; then
    missing+=("python3-venv")
  fi

  if [[ "${#missing[@]}" -gt 0 ]]; then
    echo "Missing required installer dependency/dependencies: ${missing[*]}" >&2
    echo "Prepare Raspberry Pi OS first with scripts/bootstrap_raspberry_pi_os.sh from a source checkout, or install the missing packages manually." >&2
    exit 1
  fi
}

check_os_baseline() {
  log "Checking Raspberry Pi OS 64-bit baseline"
  if [[ "$(getconf LONG_BIT)" != "64" ]]; then
    echo "This client is intended for Raspberry Pi OS 64-bit. Reflash with the 64-bit GUI image." >&2
    exit 1
  fi

  if [[ ! -f /etc/rpi-issue ]] || ! grep -qi "Raspberry Pi" /etc/rpi-issue; then
    echo "Warning: /etc/rpi-issue does not look like Raspberry Pi OS; continuing anyway." >&2
  fi
}

create_runtime_user() {
  log "Creating runtime user ${DJCONNECT_RUNTIME_USER}"
  if ! id "$DJCONNECT_RUNTIME_USER" >/dev/null 2>&1; then
    useradd --system --create-home --groups video,input,render,netdev "$DJCONNECT_RUNTIME_USER"
  fi
  install -d -o "$DJCONNECT_RUNTIME_USER" -g "$DJCONNECT_RUNTIME_USER" "$DJCONNECT_ROOT/config" "$DJCONNECT_ROOT/releases"
}

download_release() {
  local tag="v${DJCONNECT_VERSION#v}"
  local version="${DJCONNECT_VERSION#v}"
  local tmp
  tmp="$(mktemp -d)"

  log "Downloading DJConnect Pi ${tag}"
  curl -fsSL "https://github.com/${DJCONNECT_REPO}/releases/download/${tag}/djconnect-pi-${version}.tar.gz" -o "${tmp}/release.tar.gz"
  curl -fsSL "https://github.com/${DJCONNECT_REPO}/releases/download/${tag}/djconnect-pi-${version}.sha256" -o "${tmp}/release.sha256"
  (cd "$tmp" && shasum -a 256 -c release.sha256)

  rm -rf "${DJCONNECT_ROOT}/releases/${version}" "${DJCONNECT_ROOT}/releases/.${version}.tmp"
  mkdir -p "${DJCONNECT_ROOT}/releases/.${version}.tmp"
  tar -xzf "${tmp}/release.tar.gz" -C "${DJCONNECT_ROOT}/releases/.${version}.tmp" --strip-components=1
  mv "${DJCONNECT_ROOT}/releases/.${version}.tmp" "${DJCONNECT_ROOT}/releases/${version}"

  log "Installing DJConnect Python dependencies"
  python3 -m venv "${DJCONNECT_ROOT}/releases/${version}/.venv"
  "${DJCONNECT_ROOT}/releases/${version}/.venv/bin/python" -m pip install --upgrade pip
  "${DJCONNECT_ROOT}/releases/${version}/.venv/bin/pip" install "${DJCONNECT_ROOT}/releases/${version}"
  ln -sfn ".venv/bin" "${DJCONNECT_ROOT}/releases/${version}/bin"
  ln -sfn "${DJCONNECT_ROOT}/releases/${version}" "${DJCONNECT_ROOT}/current"
  chown -R "$DJCONNECT_RUNTIME_USER:$DJCONNECT_RUNTIME_USER" "$DJCONNECT_ROOT"
}

write_initial_config() {
  local config="${DJCONNECT_ROOT}/config/client.json"
  if [[ -f "$config" ]]; then
    log "Keeping existing DJConnect config at ${config}"
    return
  fi

  log "Writing initial DJConnect config"
  python3 - "$config" "$DJCONNECT_HA_URL" <<'PY'
from pathlib import Path
import json
import sys
import uuid

config = Path(sys.argv[1])
ha_url = sys.argv[2]
suffix = uuid.getnode().to_bytes(6, "big").hex().upper()[:12]
payload = {
    "ha_url": ha_url,
    "device_id": f"djconnect-raspberry-pi-{suffix}",
    "device_name": "DJConnect Pi",
    "device_token": "",
    "paired": False,
    "version": "3.1.16",
    "update_repo": "pcvantol/djconnect-pi-releases",
    "update_channel": "stable",
    "screen_timeout_seconds": 120,
    "screen_brightness_percent": 100,
    "log_file": "/opt/djconnect/logs/client.log",
    "dj_response_file": "/opt/djconnect/config/dj-response.json",
    "log_level": "INFO",
}
config.parent.mkdir(parents=True, exist_ok=True)
config.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
  install -d -o "$DJCONNECT_RUNTIME_USER" -g "$DJCONNECT_RUNTIME_USER" "$DJCONNECT_ROOT/logs"
  chown "$DJCONNECT_RUNTIME_USER:$DJCONNECT_RUNTIME_USER" "$config"
}

install_systemd_units() {
  log "Installing systemd units"
  cp "${DJCONNECT_ROOT}/current/systemd/"*.service /etc/systemd/system/
  cp "${DJCONNECT_ROOT}/current/systemd/"*.timer /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable djconnect-api.service
  systemctl enable djconnect-client.service
  systemctl restart djconnect-api.service
  systemctl restart djconnect-client.service
  systemctl enable --now djconnect-updater.timer
  systemctl enable --now djconnect-maintenance.timer
  systemctl enable --now djconnect-screen-off.timer
  systemctl enable --now djconnect-screen-on.timer
}

main() {
  log "DJConnect Pi installer ${DJCONNECT_VERSION}"
  check_runtime_dependencies
  check_os_baseline
  create_runtime_user
  download_release
  write_initial_config
  install_systemd_units

  log "DJConnect Pi installation complete"
  echo "Local Client API starts automatically via djconnect-api.service."
  echo "DJConnect frontend starts automatically after boot via djconnect-client.service."
  echo "Night screen schedule: off at 23:00, on at 07:00"
}

main "$@"
