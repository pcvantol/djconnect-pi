#!/usr/bin/env bash
set -euo pipefail

DJCONNECT_VERSION="${DJCONNECT_VERSION:-3.1.22}"
DJCONNECT_REPO="${DJCONNECT_REPO:-pcvantol/djconnect-pi-releases}"
DJCONNECT_HA_URL="${DJCONNECT_HA_URL:-http://homeassistant.local:8123}"
DJCONNECT_RUNTIME_USER="${DJCONNECT_RUNTIME_USER:-djconnect}"
DJCONNECT_ROOT="${DJCONNECT_ROOT:-/opt/djconnect}"
DJCONNECT_INSTALL_STATE="${DJCONNECT_INSTALL_STATE:-${DJCONNECT_ROOT}/install-state}"
DJCONNECT_PIP_CACHE="${DJCONNECT_PIP_CACHE:-/var/cache/djconnect-pip}"
DJCONNECT_MIN_FREE_MB="${DJCONNECT_MIN_FREE_MB:-1800}"

if [[ -f /etc/default/locale ]]; then
  # shellcheck disable=SC1091
  . /etc/default/locale
fi
export LANG="${LANG:-C.UTF-8}"
export LC_CTYPE="${LC_CTYPE:-${LANG}}"

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
  DJCONNECT_INSTALL_STATE=/opt/djconnect/install-state
  DJCONNECT_PIP_CACHE=/var/cache/djconnect-pip
  DJCONNECT_MIN_FREE_MB=1800

This installs or updates the DJConnect Pi application only:
- creates/updates the dedicated runtime user and /opt/djconnect layout
- downloads and verifies the selected public DJConnect Pi release
- resumes completed install steps after an interrupted run or reboot
- preserves existing pairing/configuration
- installs/refreshes the local Client API, frontend, updater, maintenance and
  night screen schedule systemd units
- restarts the DJConnect API and touch UI services

General Raspberry Pi OS bootstrap tasks, such as timezone, SSH, apt full-upgrade,
Raspberry Pi Connect and HyperPixel display setup, are intentionally
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

version() {
  printf '%s\n' "${DJCONNECT_VERSION#v}"
}

state_dir() {
  printf '%s\n' "${DJCONNECT_INSTALL_STATE}/$(version)"
}

marker_done() {
  [[ -f "$(state_dir)/$1.done" ]]
}

mark_done() {
  install -d "$(state_dir)"
  touch "$(state_dir)/$1.done"
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

check_free_space() {
  log "Checking free disk space"
  local required="$DJCONNECT_MIN_FREE_MB"
  local opt_free
  local cache_parent
  local cache_free

  opt_free="$(df -Pm "$DJCONNECT_ROOT" 2>/dev/null | awk 'NR==2 {print $4}')"
  cache_parent="$(dirname "$DJCONNECT_PIP_CACHE")"
  install -d "$cache_parent"
  cache_free="$(df -Pm "$cache_parent" 2>/dev/null | awk 'NR==2 {print $4}')"

  if [[ -n "$opt_free" && "$opt_free" -lt "$required" ]]; then
    echo "Not enough free disk space for DJConnect install on ${DJCONNECT_ROOT}: ${opt_free} MB available, ${required} MB required." >&2
    echo "Run the repo bootstrap to expand the root filesystem, reboot if requested, then rerun this installer." >&2
    exit 1
  fi

  if [[ -n "$cache_free" && "$cache_free" -lt "$required" ]]; then
    echo "Not enough free disk space for pip cache at ${DJCONNECT_PIP_CACHE}: ${cache_free} MB available, ${required} MB required." >&2
    echo "Run the repo bootstrap to expand the root filesystem, reboot if requested, then rerun this installer." >&2
    exit 1
  fi
}

check_os_baseline() {
  log "Checking Raspberry Pi OS 64-bit baseline"
  if [[ "$(getconf LONG_BIT)" != "64" ]]; then
    echo "This client is intended for Raspberry Pi OS Lite 64-bit or another Raspberry Pi OS 64-bit image." >&2
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
  install -d -o "$DJCONNECT_RUNTIME_USER" -g "$DJCONNECT_RUNTIME_USER" \
    "$DJCONNECT_ROOT/config" \
    "$DJCONNECT_ROOT/releases" \
    "$DJCONNECT_INSTALL_STATE"
  install -d -o root -g root "$DJCONNECT_PIP_CACHE"
}

download_release() {
  local tag="v${DJCONNECT_VERSION#v}"
  local version
  local tmp
  local release_dir
  version="$(version)"
  release_dir="${DJCONNECT_ROOT}/releases/${version}"

  if marker_done "release_unpacked" && [[ -d "$release_dir" ]]; then
    log "Release ${tag} already unpacked; resuming"
    return
  fi

  tmp="$(mktemp -d)"

  log "Downloading DJConnect Pi ${tag}"
  curl -fsSL "https://github.com/${DJCONNECT_REPO}/releases/download/${tag}/djconnect-pi-${version}.tar.gz" -o "${tmp}/release.tar.gz"
  curl -fsSL "https://github.com/${DJCONNECT_REPO}/releases/download/${tag}/djconnect-pi-${version}.sha256" -o "${tmp}/release.sha256"
  local expected_hash
  local actual_hash
  expected_hash="$(awk '{print $1; exit}' "${tmp}/release.sha256")"
  actual_hash="$(shasum -a 256 "${tmp}/release.tar.gz" | awk '{print $1; exit}')"
  if [[ -z "$expected_hash" || "$actual_hash" != "$expected_hash" ]]; then
    echo "Release checksum mismatch for ${tag}" >&2
    echo "Expected: ${expected_hash:-<empty>}" >&2
    echo "Actual:   ${actual_hash}" >&2
    exit 1
  fi

  rm -rf "$release_dir" "${DJCONNECT_ROOT}/releases/.${version}.tmp"
  mkdir -p "${DJCONNECT_ROOT}/releases/.${version}.tmp"
  tar -xzf "${tmp}/release.tar.gz" -C "${DJCONNECT_ROOT}/releases/.${version}.tmp" --strip-components=1
  mv "${DJCONNECT_ROOT}/releases/.${version}.tmp" "$release_dir"
  mark_done "release_unpacked"
}

install_python_dependencies() {
  local version
  local release_dir
  version="$(version)"
  release_dir="${DJCONNECT_ROOT}/releases/${version}"

  if marker_done "venv_ready" && [[ -x "${release_dir}/.venv/bin/djconnect-pi-client" ]]; then
    log "DJConnect Python dependencies already installed; resuming"
    return
  fi

  log "Installing DJConnect Python dependencies"
  python3 -m venv "${release_dir}/.venv"
  PIP_CACHE_DIR="$DJCONNECT_PIP_CACHE" "${release_dir}/.venv/bin/python" -m pip install --upgrade pip
  PIP_CACHE_DIR="$DJCONNECT_PIP_CACHE" "${release_dir}/.venv/bin/pip" install --prefer-binary "$release_dir"
  ln -sfn ".venv/bin" "${release_dir}/bin"
  mark_done "venv_ready"
}

activate_release() {
  local version
  version="$(version)"
  log "Activating DJConnect Pi v${version}"
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
    "version": "3.1.22",
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
  check_free_space
  download_release
  install_python_dependencies
  activate_release
  write_initial_config
  install_systemd_units

  log "DJConnect Pi installation complete"
  echo "Local Client API starts automatically via djconnect-api.service."
  echo "DJConnect frontend starts automatically after boot via djconnect-client.service."
  echo "Night screen schedule: off at 23:00, on at 07:00"
}

main "$@"
