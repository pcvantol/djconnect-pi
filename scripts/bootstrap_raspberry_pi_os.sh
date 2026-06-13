#!/usr/bin/env bash
set -euo pipefail

DJCONNECT_BOOTSTRAP_VERSION="${DJCONNECT_BOOTSTRAP_VERSION:-3.1.19}"
DJCONNECT_TIMEZONE="${DJCONNECT_TIMEZONE:-Europe/Amsterdam}"
DJCONNECT_INSTALL_HYPERPIXEL="${DJCONNECT_INSTALL_HYPERPIXEL:-1}"
DJCONNECT_HYPERPIXEL_MODEL="${DJCONNECT_HYPERPIXEL_MODEL:-square}"
DJCONNECT_HYPERPIXEL_ROTATE="${DJCONNECT_HYPERPIXEL_ROTATE:-}"
DJCONNECT_ENABLE_RPI_CONNECT="${DJCONNECT_ENABLE_RPI_CONNECT:-1}"
DJCONNECT_FULL_UPGRADE="${DJCONNECT_FULL_UPGRADE:-1}"
DJCONNECT_RUNTIME_USER="${DJCONNECT_RUNTIME_USER:-djconnect}"

usage() {
  cat <<EOF
Usage:
  sudo ./scripts/bootstrap_raspberry_pi_os.sh

Version:
  DJConnect Pi OS bootstrap helper ${DJCONNECT_BOOTSTRAP_VERSION}

Environment:
  DJCONNECT_TIMEZONE=Europe/Amsterdam
  DJCONNECT_INSTALL_HYPERPIXEL=1
  DJCONNECT_HYPERPIXEL_MODEL=square
  DJCONNECT_HYPERPIXEL_ROTATE=
  DJCONNECT_ENABLE_RPI_CONNECT=1
  DJCONNECT_FULL_UPGRADE=1
  DJCONNECT_RUNTIME_USER=djconnect

This prepares a Raspberry Pi OS Lite 64-bit image for a wall-mounted
DJConnect Pi:
- validates the Raspberry Pi OS 64-bit baseline
- configures boot to console
- sets timezone to Europe/Amsterdam by default
- enables SSH
- runs apt update and optional apt full-upgrade
- installs OS packages including minimal X11/kiosk, Qt runtime and Python
- attempts to install and enable Raspberry Pi Connect
- configures the modern HyperPixel 4 KMS DPI overlay

This is a repo-only bootstrap helper. It is intentionally not included in
DJConnect Pi release tarballs and is not part of the app release cycle.
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
  log "Checking Raspberry Pi OS 64-bit baseline"
  if [[ "$(getconf LONG_BIT)" != "64" ]]; then
    echo "This bootstrap is intended for Raspberry Pi OS Lite 64-bit or another Raspberry Pi OS 64-bit image." >&2
    exit 1
  fi

  if [[ ! -f /etc/rpi-issue ]] || ! grep -qi "Raspberry Pi" /etc/rpi-issue; then
    echo "Warning: /etc/rpi-issue does not look like Raspberry Pi OS; continuing anyway." >&2
  fi
}

configure_timezone() {
  log "Configuring timezone ${DJCONNECT_TIMEZONE}"
  timedatectl set-timezone "$DJCONNECT_TIMEZONE"
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

repair_package_state() {
  if ! dpkg --audit | grep -q .; then
    return
  fi

  log "Repairing interrupted apt/dpkg state"
  DEBIAN_FRONTEND=noninteractive apt-get -f install -y
}

install_base_packages() {
  log "Updating apt metadata"
  apt-get update
  repair_package_state

  if [[ "$DJCONNECT_FULL_UPGRADE" == "1" ]]; then
    log "Running apt full-upgrade"
    DEBIAN_FRONTEND=noninteractive apt-get -y full-upgrade
    repair_package_state
  fi

  log "Installing Raspberry Pi OS bootstrap packages"
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ca-certificates \
    curl \
    git \
    jq \
    libegl1 \
    libgl1 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xinerama0 \
    libxcb-xinput0 \
    python3-pip \
    python3-venv \
    ssh \
    unzip \
    x11-xserver-utils \
    xinit \
    xserver-xorg \
    xserver-xorg-video-fbdev \
    xserver-xorg-input-libinput
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

  if systemctl list-unit-files rpi-connect.service --no-legend 2>/dev/null | grep -q '^rpi-connect\.service'; then
    systemctl enable --now rpi-connect.service || true
  elif systemctl list-unit-files rpi-connect-wayvnc.service --no-legend 2>/dev/null | grep -q '^rpi-connect-wayvnc\.service'; then
    systemctl enable --now rpi-connect-wayvnc.service || true
  else
    echo "rpi-connect installed, but no system service was found; continuing." >&2
  fi

  if command -v rpi-connect >/dev/null 2>&1; then
    echo "Run 'rpi-connect signin' on the Pi to link it to your Raspberry Pi account."
  fi
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

main() {
  log "DJConnect Pi OS bootstrap ${DJCONNECT_BOOTSTRAP_VERSION}"
  check_os_baseline
  configure_timezone
  configure_console_boot
  enable_ssh
  install_base_packages
  install_rpi_connect
  install_hyperpixel

  log "Raspberry Pi OS bootstrap complete"
  echo "Wi-Fi provisioning is intentionally not handled here; configure it with Raspberry Pi Imager."
  echo "Run 'sudo ./scripts/install_raspberry_pi.sh' from a DJConnect Pi release bundle to install the app."
  echo "Reboot is recommended after OS, HyperPixel and full-upgrade changes."
}

main "$@"
