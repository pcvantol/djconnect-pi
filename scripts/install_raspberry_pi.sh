#!/usr/bin/env bash
set -euo pipefail

DJCONNECT_VERSION="${DJCONNECT_VERSION:-3.1.15}"
DJCONNECT_REPO="${DJCONNECT_REPO:-pcvantol/djconnect-pi-releases}"
DJCONNECT_HA_URL="${DJCONNECT_HA_URL:-http://homeassistant.local:8123}"
DJCONNECT_TIMEZONE="${DJCONNECT_TIMEZONE:-Europe/Amsterdam}"
DJCONNECT_INSTALL_HYPERPIXEL="${DJCONNECT_INSTALL_HYPERPIXEL:-1}"
DJCONNECT_HYPERPIXEL_MODEL="${DJCONNECT_HYPERPIXEL_MODEL:-square}"
DJCONNECT_HYPERPIXEL_ROTATE="${DJCONNECT_HYPERPIXEL_ROTATE:-}"
DJCONNECT_ENABLE_RPI_CONNECT="${DJCONNECT_ENABLE_RPI_CONNECT:-1}"
DJCONNECT_FULL_UPGRADE="${DJCONNECT_FULL_UPGRADE:-1}"
DJCONNECT_CONFIGURE_DARK_MODE="${DJCONNECT_CONFIGURE_DARK_MODE:-1}"
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
  DJCONNECT_TIMEZONE=Europe/Amsterdam
  DJCONNECT_INSTALL_HYPERPIXEL=1
  DJCONNECT_HYPERPIXEL_MODEL=square
  DJCONNECT_HYPERPIXEL_ROTATE=
  DJCONNECT_ENABLE_RPI_CONNECT=1
  DJCONNECT_FULL_UPGRADE=1
  DJCONNECT_CONFIGURE_DARK_MODE=1

This installs a dedicated wall-mounted DJConnect Pi client:
- checks for Raspberry Pi OS Desktop/GUI 64-bit baseline
- configures boot to console
- starts the DJConnect Qt frontend automatically after boot through xinit
- timezone Europe/Amsterdam
- SSH enabled
- Raspberry Pi Connect enabled when available
- Raspberry Pi OS desktop dark mode for debug/VNC fallback sessions
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

install_hyperpixel() {
  if [[ "$DJCONNECT_INSTALL_HYPERPIXEL" != "1" ]]; then
    log "Skipping HyperPixel configuration"
    return
  fi

  log "Configuring HyperPixel 4 KMS DPI overlay"
  local boot_config="/boot/firmware/config.txt"
  local overlay
  local overlay_line

  if [[ ! -f "$boot_config" ]]; then
    boot_config="/boot/config.txt"
  fi
  if [[ ! -f "$boot_config" ]]; then
    echo "Could not find Raspberry Pi boot config at /boot/firmware/config.txt or /boot/config.txt." >&2
    return 1
  fi

  case "$DJCONNECT_HYPERPIXEL_MODEL" in
    square|sq)
      overlay="vc4-kms-dpi-hyperpixel4sq"
      ;;
    rectangular|rect)
      overlay="vc4-kms-dpi-hyperpixel4"
      ;;
    *)
      echo "DJCONNECT_HYPERPIXEL_MODEL must be square or rectangular." >&2
      return 1
      ;;
  esac

  overlay_line="dtoverlay=${overlay}"
  if [[ -n "$DJCONNECT_HYPERPIXEL_ROTATE" ]]; then
    case "$DJCONNECT_HYPERPIXEL_ROTATE" in
      0)
        ;;
      90|180|270)
        overlay_line="${overlay_line},rotate=${DJCONNECT_HYPERPIXEL_ROTATE}"
        ;;
      *)
        echo "DJCONNECT_HYPERPIXEL_ROTATE must be empty, 0, 90, 180 or 270." >&2
        return 1
        ;;
    esac
  fi

  if command -v raspi-config >/dev/null 2>&1; then
    raspi-config nonint do_i2c 1 || true
    raspi-config nonint do_spi 1 || true
  fi

  systemctl disable --now hyperpixel4-init.service >/dev/null 2>&1 || true

  sed -i.bak \
    -e '/^dtoverlay=vc4-kms-dpi-hyperpixel4/d' \
    -e '/^dtoverlay=hyperpixel4/d' \
    -e '/^dtoverlay=hyperpixel4sq/d' \
    "$boot_config"

  printf '\n# DJConnect Pi HyperPixel 4 display\n%s\n' "$overlay_line" >> "$boot_config"
  echo "Configured ${overlay_line} in ${boot_config}."
  echo "Reboot is required before HyperPixel display output appears."
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

configure_gui_dark_mode_for_user() {
  local user="$1"
  local home="$2"
  local uid
  local gtk_theme="PiXflat"
  local icon_theme="PiXflat"
  local color_scheme="prefer-dark"

  if [[ -z "$home" || ! -d "$home" ]]; then
    return
  fi

  uid="$(id -u "$user" 2>/dev/null || true)"

  install -d -o "$user" -g "$user" \
    "$home/.config/gtk-3.0" \
    "$home/.config/gtk-4.0" \
    "$home/.config/openbox"

  cat > "$home/.config/gtk-3.0/settings.ini" <<EOF
[Settings]
gtk-theme-name=${gtk_theme}
gtk-icon-theme-name=${icon_theme}
gtk-application-prefer-dark-theme=true
EOF

  cat > "$home/.config/gtk-4.0/settings.ini" <<EOF
[Settings]
gtk-theme-name=${gtk_theme}
gtk-icon-theme-name=${icon_theme}
gtk-application-prefer-dark-theme=true
EOF

  cat > "$home/.config/openbox/lxde-pi-rc.xml" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <theme>
    <name>${gtk_theme}</name>
  </theme>
</openbox_config>
EOF

  chown -R "$user:$user" "$home/.config/gtk-3.0" "$home/.config/gtk-4.0" "$home/.config/openbox"

  if [[ -n "$uid" && -S "/run/user/${uid}/bus" ]] && command -v gsettings >/dev/null 2>&1; then
    sudo -u "$user" \
      XDG_RUNTIME_DIR="/run/user/${uid}" \
      DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" \
      gsettings set org.gnome.desktop.interface color-scheme "$color_scheme" || true
    sudo -u "$user" \
      XDG_RUNTIME_DIR="/run/user/${uid}" \
      DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" \
      gsettings set org.gnome.desktop.interface gtk-theme "$gtk_theme" || true
  fi
}

configure_gui_dark_mode() {
  if [[ "$DJCONNECT_CONFIGURE_DARK_MODE" != "1" ]]; then
    log "Skipping Raspberry Pi OS desktop dark mode"
    return
  fi

  log "Configuring Raspberry Pi OS desktop dark mode"
  if id pi >/dev/null 2>&1; then
    configure_gui_dark_mode_for_user pi "$(getent passwd pi | cut -d: -f6)"
  fi
  if [[ "$DJCONNECT_RUNTIME_USER" != "pi" ]] && id "$DJCONNECT_RUNTIME_USER" >/dev/null 2>&1; then
    configure_gui_dark_mode_for_user "$DJCONNECT_RUNTIME_USER" "$(getent passwd "$DJCONNECT_RUNTIME_USER" | cut -d: -f6)"
  fi
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
    "version": "3.1.15",
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

configure_timezone() {
  log "Configuring timezone ${DJCONNECT_TIMEZONE}"
  timedatectl set-timezone "$DJCONNECT_TIMEZONE"
}

main() {
  log "DJConnect Pi installer ${DJCONNECT_VERSION}"
  check_os_baseline
  configure_timezone
  configure_console_boot
  enable_ssh
  install_base_packages
  install_rpi_connect
  create_runtime_user
  configure_gui_dark_mode
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
