#!/usr/bin/env bash
set -euo pipefail

DJCONNECT_VERSION="${DJCONNECT_VERSION:-3.1.49}"
DJCONNECT_REPO="${DJCONNECT_REPO:-pcvantol/djconnect-pi-releases}"
DJCONNECT_HA_URL="${DJCONNECT_HA_URL:-http://homeassistant.local:8123}"
DJCONNECT_RUNTIME_USER="${DJCONNECT_RUNTIME_USER:-djconnect}"
DJCONNECT_ROOT="${DJCONNECT_ROOT:-/opt/djconnect}"
DJCONNECT_INSTALL_STATE="${DJCONNECT_INSTALL_STATE:-${DJCONNECT_ROOT}/install-state}"
DJCONNECT_PIP_CACHE="${DJCONNECT_PIP_CACHE:-/var/cache/djconnect-pip}"
DJCONNECT_MIN_FREE_MB="${DJCONNECT_MIN_FREE_MB:-3000}"
DJCONNECT_MIN_SWAP_MB="${DJCONNECT_MIN_SWAP_MB:-1000}"

if [[ -f /etc/default/locale ]]; then
  # shellcheck disable=SC1091
  . /etc/default/locale
fi
export LANG="${LANG:-C.UTF-8}"
export LC_CTYPE="${LC_CTYPE:-${LANG}}"

usage() {
  cat <<EOF
Usage:
  sudo ./scripts/install.sh

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
  DJCONNECT_MIN_FREE_MB=3000
  DJCONNECT_MIN_SWAP_MB=1000

This installs or updates the DJConnect Pi application only:
- creates/updates the dedicated runtime user and /opt/djconnect layout
- downloads and verifies the selected public DJConnect Pi release
- resumes completed install steps after an interrupted run or reboot
- checks disk and swap requirements before large PySide6 downloads
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

print_resources() {
  local label="$1"
  local mem_available_mb
  local mem_total_mb
  local swap_free_mb
  local swap_total_mb

  mem_available_mb="$(awk '/^MemAvailable:/ {printf "%d", $2 / 1024}' /proc/meminfo 2>/dev/null || true)"
  mem_total_mb="$(awk '/^MemTotal:/ {printf "%d", $2 / 1024}' /proc/meminfo 2>/dev/null || true)"
  swap_free_mb="$(awk '/^SwapFree:/ {printf "%d", $2 / 1024}' /proc/meminfo 2>/dev/null || true)"
  swap_total_mb="$(awk '/^SwapTotal:/ {printf "%d", $2 / 1024}' /proc/meminfo 2>/dev/null || true)"
  mem_available_mb="${mem_available_mb:-0}"
  mem_total_mb="${mem_total_mb:-0}"
  swap_free_mb="${swap_free_mb:-0}"
  swap_total_mb="${swap_total_mb:-0}"

  printf '\n-- Resources: %s --\n' "$label"
  printf 'Memory: %s MB available / %s MB total\n' "$mem_available_mb" "$mem_total_mb"
  printf 'Swap:   %s MB free / %s MB total\n' "$swap_free_mb" "$swap_total_mb"
  df -h / "$DJCONNECT_ROOT" "$(dirname "$DJCONNECT_PIP_CACHE")" 2>/dev/null | awk 'NR==1 || !seen[$1]++'
  df -ih / "$DJCONNECT_ROOT" "$(dirname "$DJCONNECT_PIP_CACHE")" 2>/dev/null | awk 'NR==1 || !seen[$1]++'
}

print_thermal_status() {
  if ! command -v vcgencmd >/dev/null 2>&1; then
    return
  fi

  local temp
  local throttled
  temp="$(vcgencmd measure_temp 2>/dev/null || true)"
  throttled="$(vcgencmd get_throttled 2>/dev/null || true)"
  if [[ -n "$temp" ]]; then
    echo "Thermal: ${temp}"
  fi
  if [[ -n "$throttled" ]]; then
    echo "Throttle: ${throttled}"
    if [[ "$throttled" != "throttled=0x0" ]]; then
      echo "Warning: Raspberry Pi reports throttling/undervoltage history; cool the Pi and check power before heavy installs." >&2
    fi
  fi
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
  print_resources "before dependency check"
  print_thermal_status
  local missing=()
  for command_name in curl find shasum tar python3 systemctl useradd install; do
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

check_cpu_architecture() {
  log "Checking CPU architecture"
  print_resources "before architecture check"
  local machine
  machine="$(uname -m)"
  case "$machine" in
    aarch64|arm64)
      ;;
    *)
      echo "Unsupported CPU architecture: ${machine}. DJConnect Pi requires Raspberry Pi OS Lite 64-bit on arm64/aarch64." >&2
      exit 1
      ;;
  esac
}

check_python_version() {
  log "Checking Python version"
  print_resources "before Python version check"
  python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit(f"Python 3.11 or newer is required, found {sys.version.split()[0]}")
PY
}

check_writable_paths() {
  log "Checking writable install paths"
  print_resources "before writable path check"
  local path
  for path in "$DJCONNECT_ROOT" "$DJCONNECT_INSTALL_STATE" "$DJCONNECT_PIP_CACHE"; do
    install -d "$path"
    if [[ ! -w "$path" ]]; then
      echo "Install path is not writable: ${path}" >&2
      exit 1
    fi
  done
}

check_github_reachable() {
  log "Checking GitHub release access"
  print_resources "before GitHub access check"
  local tag="v${DJCONNECT_VERSION#v}"
  local version="${DJCONNECT_VERSION#v}"
  local url="https://github.com/${DJCONNECT_REPO}/releases/download/${tag}/djconnect-pi-${version}.sha256"

  if ! curl -fsSIL --connect-timeout 15 --max-time 30 "$url" >/dev/null; then
    echo "Cannot reach DJConnect Pi release asset: ${url}" >&2
    echo "Check network/DNS from the Pi and verify that release ${tag} exists in ${DJCONNECT_REPO}." >&2
    exit 1
  fi
}

check_free_space() {
  log "Checking free disk space"
  print_resources "before disk check"
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

check_swap() {
  log "Checking active swap"
  print_resources "before swap check"
  local required_kb=$((DJCONNECT_MIN_SWAP_MB * 1024))
  local swap_total_kb
  swap_total_kb="$(awk '/^SwapTotal:/ {print $2}' /proc/meminfo)"

  if [[ -z "$swap_total_kb" || "$swap_total_kb" -lt "$required_kb" ]]; then
    echo "Not enough active swap for DJConnect install: $((swap_total_kb / 1024)) MB available, ${DJCONNECT_MIN_SWAP_MB} MB required." >&2
    echo "Run the repo bootstrap to configure the 1GB swapfile, reboot if requested, then rerun this installer." >&2
    exit 1
  fi
}

check_os_baseline() {
  log "Checking Raspberry Pi OS 64-bit baseline"
  print_resources "before OS baseline check"
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
  print_resources "before runtime user setup"
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
    print_resources "release already unpacked"
    return
  fi

  tmp="$(mktemp -d)"

  log "Downloading DJConnect Pi ${tag}"
  print_resources "before release download"
  curl -fsSL "https://github.com/${DJCONNECT_REPO}/releases/download/${tag}/djconnect-pi-${version}.tar.gz" -o "${tmp}/release.tar.gz"
  curl -fsSL "https://github.com/${DJCONNECT_REPO}/releases/download/${tag}/djconnect-pi-${version}.sha256" -o "${tmp}/release.sha256"
  print_resources "after release download"
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
  print_resources "before release unpack"
  tar -xzf "${tmp}/release.tar.gz" -C "${DJCONNECT_ROOT}/releases/.${version}.tmp" --strip-components=1
  mv "${DJCONNECT_ROOT}/releases/.${version}.tmp" "$release_dir"
  mark_done "release_unpacked"
  print_resources "after release unpack"
}

install_python_dependencies() {
  local version
  local release_dir
  local wheel_path
  local pip_tmp
  version="$(version)"
  release_dir="${DJCONNECT_ROOT}/releases/${version}"
  wheel_path="$(find "$release_dir/wheels" -maxdepth 1 -type f -name "djconnect_pi-${version}-*.whl" 2>/dev/null | head -n 1 || true)"
  pip_tmp="${DJCONNECT_PIP_CACHE}/tmp"

  if marker_done "venv_ready" \
    && [[ -x "${release_dir}/.venv/bin/djconnect-pi-client" ]] \
    && [[ -x "${release_dir}/.venv/bin/djconnect-pi-api" ]] \
    && [[ -x "${release_dir}/.venv/bin/djconnect-pi-updater" ]] \
    && [[ -x "${release_dir}/.venv/bin/djconnect-pi-maintenance" ]]; then
    log "DJConnect Python dependencies already installed; resuming"
    print_resources "dependencies already installed"
    return
  fi

  if [[ -z "$wheel_path" || ! -f "$wheel_path" ]]; then
    echo "DJConnect Pi wheel not found in release bundle: ${release_dir}/wheels/djconnect_pi-${version}-*.whl" >&2
    exit 1
  fi

  log "Installing DJConnect Python dependencies"
  if [[ -d "${release_dir}/.venv" ]]; then
    echo "Removing incomplete Python virtualenv before retry: ${release_dir}/.venv"
    rm -rf "${release_dir}/.venv" "${release_dir}/bin"
  fi
  install -d -o root -g root "$DJCONNECT_PIP_CACHE" "$pip_tmp"
  check_free_space
  print_resources "before Python dependency install"
  python3 -m venv "${release_dir}/.venv"
  TMPDIR="$pip_tmp" PIP_CACHE_DIR="$DJCONNECT_PIP_CACHE" "${release_dir}/.venv/bin/python" -m pip install --upgrade pip
  TMPDIR="$pip_tmp" PIP_CACHE_DIR="$DJCONNECT_PIP_CACHE" "${release_dir}/.venv/bin/python" -m pip install --upgrade setuptools wheel
  TMPDIR="$pip_tmp" PIP_CACHE_DIR="$DJCONNECT_PIP_CACHE" "${release_dir}/.venv/bin/python" -m pip install --upgrade --prefer-binary "PySide6>=6.7" "requests>=2.31" "zeroconf>=0.132"
  TMPDIR="$pip_tmp" PIP_CACHE_DIR="$DJCONNECT_PIP_CACHE" "${release_dir}/.venv/bin/python" -m pip install --prefer-binary "$wheel_path"
  ln -sfn ".venv/bin" "${release_dir}/bin"
  mark_done "venv_ready"
  print_resources "after Python dependency install"
}

activate_release() {
  local version
  version="$(version)"
  log "Activating DJConnect Pi v${version}"
  print_resources "before release activation"
  ln -sfn "${DJCONNECT_ROOT}/releases/${version}" "${DJCONNECT_ROOT}/current"
  chown -R "$DJCONNECT_RUNTIME_USER:$DJCONNECT_RUNTIME_USER" "$DJCONNECT_ROOT"
  print_resources "after release activation"
}

write_initial_config() {
  local config="${DJCONNECT_ROOT}/config/client.json"
  if [[ -f "$config" ]]; then
    log "Keeping existing DJConnect config at ${config}"
    print_resources "config already present"
    return
  fi

  log "Writing initial DJConnect config"
  print_resources "before config write"
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
    "version": "3.1.49",
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
  print_resources "after config write"
}

install_systemd_units() {
  log "Installing systemd units"
  print_resources "before systemd install"
  configure_xwrapper
  configure_reboot_sudoers
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
  systemctl enable --now djconnect-watchdog.timer
  print_resources "after systemd install"
}

configure_reboot_sudoers() {
  local sudoers_dir="/etc/sudoers.d"
  local sudoers_file="${sudoers_dir}/djconnect-reboot"

  if [[ ! -d "$sudoers_dir" ]]; then
    echo "Warning: ${sudoers_dir} does not exist; reboot button may require system policy configuration." >&2
    return
  fi

  cat >"$sudoers_file" <<EOF
${DJCONNECT_RUNTIME_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl reboot, /bin/systemctl reboot
EOF
  chmod 0440 "$sudoers_file"
}

configure_xwrapper() {
  local config="/etc/X11/Xwrapper.config"

  if [[ ! -d "/etc/X11" ]]; then
    echo "Warning: /etc/X11 does not exist yet; skipping Xwrapper configuration." >&2
    return
  fi

  if [[ -f "$config" ]] && grep -q '^allowed_users=' "$config"; then
    sed -i 's/^allowed_users=.*/allowed_users=anybody/' "$config"
  else
    printf 'allowed_users=anybody\n' >> "$config"
  fi

  if grep -q '^needs_root_rights=' "$config"; then
    sed -i 's/^needs_root_rights=.*/needs_root_rights=yes/' "$config"
  else
    printf 'needs_root_rights=yes\n' >> "$config"
  fi
}

main() {
  log "DJConnect Pi installer ${DJCONNECT_VERSION}"
  print_resources "installer start"
  print_thermal_status
  check_runtime_dependencies
  check_cpu_architecture
  check_python_version
  check_os_baseline
  create_runtime_user
  check_writable_paths
  check_free_space
  check_swap
  check_github_reachable
  download_release
  install_python_dependencies
  activate_release
  write_initial_config
  install_systemd_units

  log "DJConnect Pi installation complete"
  print_resources "installer complete"
  print_thermal_status
  echo "Local Client API starts automatically via djconnect-api.service."
  echo "DJConnect frontend starts automatically after boot via djconnect-client.service."
  echo "Night screen schedule: off at 23:00, on at 07:00"
}

main "$@"
