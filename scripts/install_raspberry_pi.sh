#!/usr/bin/env bash
set -euo pipefail

DJCONNECT_VERSION="${DJCONNECT_VERSION:-3.1.7}"
DJCONNECT_REPO="${DJCONNECT_REPO:-pcvantol/djconnect-pi-releases}"
DJCONNECT_HA_URL="${DJCONNECT_HA_URL:-http://homeassistant.local:8123}"
DJCONNECT_WIFI_SSID="${DJCONNECT_WIFI_SSID:-}"
DJCONNECT_WIFI_PASSWORD="${DJCONNECT_WIFI_PASSWORD:-}"
DJCONNECT_WIFI_COUNTRY="${DJCONNECT_WIFI_COUNTRY:-NL}"
DJCONNECT_TIMEZONE="${DJCONNECT_TIMEZONE:-Europe/Amsterdam}"
DJCONNECT_INSTALL_HYPERPIXEL="${DJCONNECT_INSTALL_HYPERPIXEL:-1}"
DJCONNECT_ENABLE_RPI_CONNECT="${DJCONNECT_ENABLE_RPI_CONNECT:-1}"
DJCONNECT_FULL_UPGRADE="${DJCONNECT_FULL_UPGRADE:-1}"
DJCONNECT_RUNTIME_USER="${DJCONNECT_RUNTIME_USER:-djconnect}"
DJCONNECT_ROOT="${DJCONNECT_ROOT:-/opt/djconnect}"

usage() {
  cat <<'EOF'
Usage:
  sudo ./scripts/install_raspberry_pi.sh

Environment:
  DJCONNECT_VERSION=3.1.7
  DJCONNECT_REPO=pcvantol/djconnect-pi-releases
  DJCONNECT_HA_URL=http://homeassistant.local:8123
  DJCONNECT_WIFI_SSID="My WiFi"
  DJCONNECT_WIFI_PASSWORD="wifi-password"
  DJCONNECT_WIFI_COUNTRY=NL
  DJCONNECT_TIMEZONE=Europe/Amsterdam
  DJCONNECT_INSTALL_HYPERPIXEL=1
  DJCONNECT_ENABLE_RPI_CONNECT=1
  DJCONNECT_FULL_UPGRADE=1

This installs a dedicated wall-mounted DJConnect Pi client:
- checks for Raspberry Pi OS Desktop/GUI 64-bit baseline
- configures boot to console
- starts the DJConnect Qt frontend automatically after boot through xinit
- timezone Europe/Amsterdam
- optional Wi-Fi provisioning
- SSH enabled
- Raspberry Pi Connect enabled when available
- apt full-upgrade
- glances
- HyperPixel support hook
- DJConnect dependencies and current release
- local Client API, frontend, updater, maintenance and night screen schedule systemd units
- screen off at 23:00 and on at 07:00
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

check_os_baseline() {
  log "Checking Raspberry Pi OS Desktop 64-bit baseline"
  if [[ "$(getconf LONG_BIT)" != "64" ]]; then
    echo "This client is intended for Raspberry Pi OS Desktop 64-bit. Reflash with the 64-bit GUI image." >&2
    exit 1
  fi

  if [[ ! -f /etc/rpi-issue ]] || ! grep -qi "Raspberry Pi" /etc/rpi-issue; then
    echo "Warning: /etc/rpi-issue does not look like Raspberry Pi OS; continuing anyway." >&2
  fi

  if ! dpkg -s raspberrypi-ui-mods >/dev/null 2>&1; then
    echo "Raspberry Pi OS Desktop UI package is not installed; installing GUI baseline packages." >&2
  fi
}

configure_console_boot() {
  log "Configuring boot to console"
  if command -v raspi-config >/dev/null 2>&1; then
    raspi-config nonint do_boot_behaviour B1 || true
  fi
  systemctl set-default multi-user.target
}

enable_ssh() {
  log "Enabling SSH"
  if command -v raspi-config >/dev/null 2>&1; then
    raspi-config nonint do_ssh 0 || true
  fi
  systemctl enable --now ssh || systemctl enable --now ssh.service
}

configure_wifi() {
  if [[ -z "$DJCONNECT_WIFI_SSID" ]]; then
    log "Skipping Wi-Fi provisioning; DJCONNECT_WIFI_SSID is empty"
    return
  fi

  log "Provisioning Wi-Fi network ${DJCONNECT_WIFI_SSID}"
  raspi-config nonint do_wifi_country "$DJCONNECT_WIFI_COUNTRY" || true

  if command -v nmcli >/dev/null 2>&1; then
    nmcli radio wifi on
    nmcli dev wifi connect "$DJCONNECT_WIFI_SSID" password "$DJCONNECT_WIFI_PASSWORD"
    return
  fi

  install -m 600 /dev/null /etc/wpa_supplicant/wpa_supplicant.conf
  {
    printf 'country=%s\n' "$DJCONNECT_WIFI_COUNTRY"
    printf 'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n'
    printf 'update_config=1\n\n'
    wpa_passphrase "$DJCONNECT_WIFI_SSID" "$DJCONNECT_WIFI_PASSWORD"
  } > /etc/wpa_supplicant/wpa_supplicant.conf
  systemctl restart wpa_supplicant || true
}

install_hyperpixel() {
  if [[ "$DJCONNECT_INSTALL_HYPERPIXEL" != "1" ]]; then
    log "Skipping HyperPixel driver install"
    return
  fi

  log "Installing HyperPixel support"
  apt-get install -y git curl
  if curl -fsSL https://get.pimoroni.com/hyperpixel4 -o /tmp/hyperpixel4-install.sh; then
    bash /tmp/hyperpixel4-install.sh || {
      echo "HyperPixel installer failed; check Pimoroni docs for your display revision." >&2
      return 1
    }
  else
    echo "Could not download Pimoroni HyperPixel installer; install drivers manually." >&2
    return 1
  fi
}

install_rpi_connect() {
  if [[ "$DJCONNECT_ENABLE_RPI_CONNECT" != "1" ]]; then
    log "Skipping Raspberry Pi Connect"
    return
  fi

  log "Installing/enabling Raspberry Pi Connect"
  apt-get install -y rpi-connect || {
    echo "rpi-connect package was not available on this image; continuing." >&2
    return 0
  }
  systemctl enable --now rpi-connect || true
  if command -v rpi-connect >/dev/null 2>&1; then
    echo "Run 'rpi-connect signin' on the Pi to link it to your Raspberry Pi account."
  fi
}

install_base_packages() {
  log "Updating apt metadata"
  apt-get update

  if [[ "$DJCONNECT_FULL_UPGRADE" == "1" ]]; then
    log "Running apt full-upgrade"
    DEBIAN_FRONTEND=noninteractive apt-get -y full-upgrade
  fi

  log "Installing base packages"
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ca-certificates \
    curl \
    git \
    glances \
    jq \
    openbox \
    python3-pip \
    python3-venv \
    raspberrypi-ui-mods \
    ssh \
    unzip \
    x11-xserver-utils \
    xinit \
    xserver-xorg
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
    "version": "3.1.7",
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
  systemctl enable --now djconnect-api.service
  systemctl enable --now djconnect-client.service
  systemctl enable --now djconnect-updater.timer
  systemctl enable --now djconnect-maintenance.timer
  systemctl enable --now djconnect-screen-off.timer
  systemctl enable --now djconnect-screen-on.timer
}

configure_timezone() {
  log "Configuring timezone ${DJCONNECT_TIMEZONE}"
  timedatectl set-timezone "$DJCONNECT_TIMEZONE"
}

main() {
  check_os_baseline
  configure_timezone
  configure_console_boot
  configure_wifi
  enable_ssh
  install_base_packages
  install_rpi_connect
  create_runtime_user
  install_hyperpixel
  download_release
  write_initial_config
  install_systemd_units

  log "DJConnect Pi installation complete"
  echo "Local Client API starts automatically via djconnect-api.service."
  echo "DJConnect frontend starts automatically after boot via djconnect-client.service."
  echo "Night screen schedule: off at 23:00, on at 07:00"
  echo "Raspberry Pi Connect may require: rpi-connect signin"
  echo "Reboot is recommended after HyperPixel and full-upgrade changes."
}

main "$@"
