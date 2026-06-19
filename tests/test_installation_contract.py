from __future__ import annotations

import json
import subprocess
from pathlib import Path
import tomllib
import os
import re


ROOT = Path(__file__).resolve().parents[1]


def _project_version() -> str:
    data = tomllib.loads(ROOT.joinpath("pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def test_install_script_enables_local_api_service() -> None:
    script = ROOT.joinpath("scripts/install.sh").read_text(encoding="utf-8")

    assert "stop_running_updater_early" in script
    assert "systemctl disable --now djconnect-updater.timer" in script
    assert "systemctl stop djconnect-updater.timer" in script
    assert "systemctl stop djconnect-updater.service" in script
    assert "stop_running_client_early" in script
    assert "systemctl disable --now djconnect-client.service" in script
    assert "systemctl stop djconnect-client.service" in script
    assert "pkill -TERM -f 'djconnect-pi-client|djconnect_pi\\.app'" in script
    main_body = script.split("main() {", 1)[1]
    assert main_body.index("stop_running_updater_early") < main_body.index("stop_running_client_early")
    assert main_body.index("stop_running_client_early") < main_body.index("check_runtime_dependencies")
    assert "systemctl enable djconnect-api.service" in script
    assert "systemctl enable djconnect-client.service" in script
    assert "systemctl restart djconnect-api.service" in script
    assert "systemctl restart djconnect-client.service" in script
    assert "djconnect-reboot" in script
    assert "NOPASSWD: /usr/bin/systemctl reboot, /bin/systemctl reboot" in script
    assert ", systemctl reboot" not in script
    assert ", systemctl poweroff" not in script
    assert ", systemctl start djconnect-updater.service" not in script
    assert "/usr/bin/systemctl start djconnect-updater.service" in script
    assert "/bin/systemctl start djconnect-updater.service" in script
    assert "visudo -cf" in script
    assert "Local Client API starts automatically via djconnect-api.service." in script


def test_bootstrap_configures_narrow_installer_sudoers_for_pi_user() -> None:
    script = ROOT.joinpath("scripts/bootstrap_raspberry_pi_os.sh").read_text(encoding="utf-8")

    assert 'DJCONNECT_INSTALL_USER="${DJCONNECT_INSTALL_USER:-pi}"' in script
    assert "configure_installer_sudoers" in script
    assert "djconnect-installer" in script
    assert "NOPASSWD: /home/${DJCONNECT_INSTALL_USER}/djconnect-install/djconnect-pi-*/scripts/install.sh" in script
    assert "/home/${DJCONNECT_INSTALL_USER}/djconnect-pi/scripts/install.sh" in script
    assert "visudo -cf" in script
    assert "ALL=(ALL) NOPASSWD: ALL" not in script


def test_install_script_refreshes_narrow_installer_sudoers_for_pi_user() -> None:
    script = ROOT.joinpath("scripts/install.sh").read_text(encoding="utf-8")

    assert 'DJCONNECT_INSTALL_USER="${DJCONNECT_INSTALL_USER:-${SUDO_USER:-pi}}"' in script
    assert "configure_installer_sudoers" in script
    assert "djconnect-installer" in script
    assert "NOPASSWD: /home/${DJCONNECT_INSTALL_USER}/djconnect-install/djconnect-pi-*/scripts/install.sh" in script
    assert "/home/${DJCONNECT_INSTALL_USER}/djconnect-pi/scripts/install.sh" in script
    assert "ALL=(ALL) NOPASSWD: ALL" not in script


def test_install_script_is_executable_in_git() -> None:
    result = subprocess.run(
        ["git", "ls-files", "-s", "scripts/install.sh"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.startswith("100755 ")


def test_os_bootstrap_script_is_executable_in_git() -> None:
    script = ROOT.joinpath("scripts/bootstrap_raspberry_pi_os.sh")

    assert script.exists()
    assert os.access(script, os.X_OK)


def test_systemd_runs_api_separately_from_touch_ui() -> None:
    api_service = ROOT.joinpath("systemd/djconnect-api.service").read_text(encoding="utf-8")
    client_service = ROOT.joinpath("systemd/djconnect-client.service").read_text(encoding="utf-8")
    update_ui_service = ROOT.joinpath("systemd/djconnect-update-ui.service").read_text(encoding="utf-8")
    pyproject = ROOT.joinpath("pyproject.toml").read_text(encoding="utf-8")

    assert "djconnect-pi-api --config /opt/djconnect/config/client.json" in api_service
    assert "Restart=always" in api_service
    assert "djconnect-pi-client --config /opt/djconnect/config/client.json" in client_service
    assert "Wants=network-online.target djconnect-updater.service" in client_service
    assert "After=network-online.target systemd-user-sessions.service djconnect-updater.service" in client_service
    assert "DJCONNECT_DISABLE_CLIENT_API" not in client_service
    assert "Conflicts=djconnect-client.service" in update_ui_service
    assert "djconnect-pi-update-ui --config /opt/djconnect/config/client.json" in update_ui_service
    assert "SuccessExitStatus=1 SIGTERM" in update_ui_service
    assert 'djconnect-pi-update-ui = "djconnect_pi.update_ui:main"' in pyproject


def test_systemd_has_nightly_reboot_timer() -> None:
    service = ROOT.joinpath("systemd/djconnect-nightly-reboot.service").read_text(encoding="utf-8")
    timer = ROOT.joinpath("systemd/djconnect-nightly-reboot.timer").read_text(encoding="utf-8")
    install_script = ROOT.joinpath("scripts/install.sh").read_text(encoding="utf-8")
    bootstrap = ROOT.joinpath("scripts/bootstrap_raspberry_pi_os.sh").read_text(encoding="utf-8")

    assert "ExecStart=/usr/bin/systemctl reboot -i" in service
    assert "OnCalendar=*-*-* 04:30:00" in timer
    assert "Persistent=false" in timer
    assert "systemctl enable --now djconnect-nightly-reboot.timer" in install_script
    assert "DJCONNECT_ENABLE_NIGHTLY_REBOOT" in bootstrap
    assert "configure_nightly_reboot" in bootstrap


def test_pyproject_exposes_client_api_daemon_entrypoint() -> None:
    pyproject = ROOT.joinpath("pyproject.toml").read_text(encoding="utf-8")

    assert 'djconnect-pi-api = "djconnect_pi.client_api_daemon:main"' in pyproject


def test_updater_service_reads_touchscreen_config() -> None:
    service = ROOT.joinpath("systemd/djconnect-updater.service").read_text(encoding="utf-8")

    assert "--config /opt/djconnect/config/client.json" in service
    assert "--channel stable" not in service
    assert "--repo pcvantol/djconnect-pi" not in service


def test_release_workflow_publishes_to_public_distribution_repo() -> None:
    workflow = ROOT.joinpath(".github/workflows/publish-release.yml").read_text(encoding="utf-8")

    assert "pcvantol/djconnect-pi-releases" in workflow
    assert "DJCONNECT_PI_RELEASES_TOKEN" in workflow
    assert 'tags:' in workflow
    assert '"v*.*.*"' in workflow


def test_cleanup_script_removes_completed_actions_runs_for_deleted_tags() -> None:
    script = ROOT.joinpath("cleanup_old_releases.sh").read_text(encoding="utf-8")

    assert "--skip-actions" in script
    assert "--public" in script
    assert "pcvantol/djconnect-pi-releases" in script
    assert 'gh run list' in script
    assert '--branch "$tag"' in script
    assert "--status completed" in script
    assert 'gh run delete "$run_id"' in script
    assert 'gh release delete "$tag" --repo "$PUBLIC_REPO" --yes' in script
    assert 'echo "Nothing to delete."\n  cleanup_public_repo\n  exit 0' in script


def test_release_assets_include_installation_materials() -> None:
    release_script = ROOT.joinpath("release.sh").read_text(encoding="utf-8")
    workflow = ROOT.joinpath(".github/workflows/publish-release.yml").read_text(encoding="utf-8")

    for text in (release_script, workflow):
        assert "README.md CHANGELOG.md docs examples systemd" in text
        assert "docs src systemd" not in text
        assert "cp -R pyproject.toml" not in text
        assert "python" in text
        assert "pip wheel --no-deps" in text
        assert "wheels" in text
        assert 'mkdir -p "$dist/scripts"' in text or 'mkdir -p "${dist}/scripts"' in text
        assert "cp scripts/install.sh" in text
        assert "cp scripts/bootstrap_raspberry_pi_os.sh" not in text


def test_technical_design_decisions_document_is_part_of_docs() -> None:
    readme = ROOT.joinpath("README.md").read_text(encoding="utf-8")
    doc = ROOT.joinpath("docs/TECHNICAL_DESIGN_DECISIONS.md").read_text(encoding="utf-8")
    contributing = ROOT.joinpath("CONTRIBUTING.md").read_text(encoding="utf-8")

    assert "[Technical Design Decisions](docs/TECHNICAL_DESIGN_DECISIONS.md)" in readme
    assert "## Python Design Patterns" in doc
    assert "## QML / Qt Quick Design Patterns" in doc
    assert "## Shell / Systemd Design Patterns" in doc
    assert "## Dependency Inventory" in doc
    assert "PySide6" in doc
    assert "requests" in doc
    assert "zeroconf" in doc
    assert "## Release Maintenance Rule" in doc
    assert "clean stale files from `screenshots/`" in doc
    assert "regenerate the representative\n  720x720 screen set" in doc
    assert "Clean out stale files in\n`screenshots/`" in contributing


def test_repo_only_os_bootstrap_targets_lite_with_minimal_kiosk_runtime() -> None:
    script = ROOT.joinpath("scripts/bootstrap_raspberry_pi_os.sh").read_text(encoding="utf-8")

    assert "Raspberry Pi OS Lite 64-bit" in script
    assert "DJCONNECT_HYPERPIXEL_MODEL" in script
    assert "vc4-kms-dpi-hyperpixel4sq" in script
    assert "vc4-kms-dpi-hyperpixel4" in script
    assert "hyperpixel4-init.service" in script
    assert "raspi-config nonint do_i2c 1" in script
    assert "raspi-config nonint do_spi 1" in script
    assert "DJCONNECT_TIMEZONE" in script
    assert "Europe/Amsterdam" in script
    assert "configure_time_sync" in script
    assert "timedatectl set-ntp true" in script
    assert "systemctl enable --now systemd-timesyncd.service" in script
    assert "timedatectl status" in script
    assert "raspi-config nonint do_expand_rootfs" in script
    assert "configure_filesystem_checks" in script
    assert "fsck.repair=yes" in script
    assert "fsck.mode=skip" in script
    assert "tune2fs -c" in script
    assert "DJCONNECT_FSCK_MAX_MOUNTS" in script
    assert "DJCONNECT_FSCK_INTERVAL" in script
    assert "DJCONNECT_SWAPFILE" in script
    assert "DJCONNECT_SWAP_MB" in script
    assert "mkswap" in script
    assert "swapon" in script
    assert "/etc/fstab" in script
    assert "/swapfile" in script
    assert "raspi-config nonint do_ssh 0" in script
    assert "apt-get -y full-upgrade" in script
    assert "locales" in script
    assert "locale-gen en_GB.UTF-8 nl_NL.UTF-8" in script
    assert "update-locale LANG=en_GB.UTF-8 LC_CTYPE=en_GB.UTF-8" in script
    assert "xinit" in script
    assert "xserver-xorg" in script
    assert "libxkbcommon-x11-0" in script
    assert "libxcb-cursor0" in script
    assert "openbox" not in script
    assert "gtk-application-prefer-dark-theme=true" not in script
    assert "glances" not in script.lower()
    assert "rpi-connect" in script
    assert "systemctl enable --now rpi-connect || true" not in script
    assert "systemctl list-unit-files rpi-connect.service" in script
    assert "systemctl list-unit-files rpi-connect-wayvnc.service" in script
    assert re.search(r"^\s+raspberrypi-ui-mods\s*\\?$", script, re.MULTILINE) is None
    assert "pi-greeter" not in script


def test_install_script_excludes_repo_only_os_bootstrap_tasks() -> None:
    script = ROOT.joinpath("scripts/install.sh").read_text(encoding="utf-8")

    assert "DJCONNECT_TIMEZONE" not in script
    assert "DJCONNECT_FULL_UPGRADE" not in script
    assert "DJCONNECT_ENABLE_RPI_CONNECT" not in script
    assert "DJCONNECT_INSTALL_HYPERPIXEL" not in script
    assert "DJCONNECT_CONFIGURE_DARK_MODE" not in script
    assert "timedatectl set-timezone" not in script
    assert "raspi-config nonint do_ssh" not in script
    assert "apt-get -y full-upgrade" not in script
    assert "apt-get install -y" not in script
    assert "systemctl enable --now rpi-connect" not in script
    assert "hyperpixel4-init.service" not in script
    assert "gtk-application-prefer-dark-theme=true" not in script


def test_install_script_sets_locale_fallback_for_lite_images() -> None:
    script = ROOT.joinpath("scripts/install.sh").read_text(encoding="utf-8")

    assert "/etc/default/locale" in script
    assert 'export LANG="${LANG:-C.UTF-8}"' in script
    assert 'export LC_CTYPE="${LC_CTYPE:-${LANG}}"' in script


def test_install_script_does_not_provision_wifi() -> None:
    script = ROOT.joinpath("scripts/install.sh").read_text(encoding="utf-8")

    assert "DJCONNECT_WIFI" not in script
    assert "configure_wifi" not in script
    assert "wpa_supplicant" not in script
    assert "nmcli" not in script
    assert "wpa_passphrase" not in script


def test_install_script_reports_version_in_help_and_runtime() -> None:
    script = ROOT.joinpath("scripts/install.sh").read_text(encoding="utf-8")

    assert "Version:" in script
    assert "DJConnect Pi installer for client ${DJCONNECT_VERSION}" in script
    assert 'log "DJConnect Pi installer ${DJCONNECT_VERSION}"' in script


def test_install_script_verifies_release_checksum_independent_of_sha_filename() -> None:
    script = ROOT.joinpath("scripts/install.sh").read_text(encoding="utf-8")

    assert "shasum -a 256 -c release.sha256" not in script
    assert "expected_hash=" in script
    assert "actual_hash=" in script
    assert "Release checksum mismatch" in script


def test_install_script_can_resume_after_reboot_or_interruption() -> None:
    script = ROOT.joinpath("scripts/install.sh").read_text(encoding="utf-8")

    assert "DJCONNECT_INSTALL_STATE" in script
    assert "DJCONNECT_PIP_CACHE" in script
    assert 'DJCONNECT_PIP_CACHE="${DJCONNECT_PIP_CACHE:-/var/cache/djconnect-pip}"' in script
    assert 'marker_done "release_unpacked"' in script
    assert 'mark_done "release_unpacked"' in script
    assert 'marker_done "venv_ready"' in script
    assert 'mark_done "venv_ready"' in script
    assert 'djconnect-pi-client' in script
    assert 'djconnect-pi-api' in script
    assert 'djconnect-pi-updater' in script
    assert 'djconnect-pi-maintenance' in script
    assert "install_python_dependencies" in script
    assert "activate_release" in script
    assert "PIP_CACHE_DIR=\"$DJCONNECT_PIP_CACHE\"" in script
    assert "TMPDIR=\"$pip_tmp\"" in script
    assert "${DJCONNECT_PIP_CACHE}/tmp" in script
    assert 'DJCONNECT_UPGRADE_PIP="${DJCONNECT_UPGRADE_PIP:-0}"' in script
    assert "Skipping pip self-upgrade" in script
    assert "DJCONNECT_UPGRADE_PIP=1" in script
    assert '${release_dir}/.venv/bin/python" -m pip install --upgrade pip' in script
    assert '${release_dir}/.venv/bin/python" -m pip install --only-binary=:all: "$wheel_path"' in script
    assert 'release_state_dir="${release_dir}/.install-state"' in script
    assert '${release_state_dir}/venv_created' in script
    assert '${release_state_dir}/build_tools_installed' in script
    assert '${release_state_dir}/shiboken6_installed' in script
    assert '${release_state_dir}/pyside6_essentials_installed' in script
    assert '${release_state_dir}/pyside6_addons_installed' in script
    assert '${release_state_dir}/pyside6_installed' in script
    assert '${release_state_dir}/requests_installed' in script
    assert '${release_state_dir}/zeroconf_installed' in script
    assert '${release_state_dir}/wheel_installed' in script
    assert '"PySide6>=6.7" "requests>=2.31" "zeroconf>=0.132"' not in script
    assert '"PySide6_Essentials>=6.7"' in script
    assert '"PySide6_Addons>=6.7"' in script
    assert '"shiboken6>=6.7"' in script
    assert '".venv/bin/pip" install' not in script
    assert "Removing incomplete Python virtualenv before retry" in script
    assert 'rm -rf "${release_dir}/.venv" "${release_dir}/bin"' in script
    assert "wheel_path=" in script
    assert "djconnect_pi-${version}-*.whl" in script
    assert 'install --only-binary=:all: "$wheel_path"' in script
    assert 'install --only-binary=:all: "$release_dir"' not in script
    assert "DJConnect Pi wheel not found" in script


def test_shared_voice_intent_examples_are_available_for_docs_alignment() -> None:
    examples = json.loads(ROOT.joinpath("examples/voice_intents.json").read_text(encoding="utf-8"))

    assert examples["version"] == "3.1.x"
    assert examples["handling_order"][:2] == ["current_track", "playback_control"]
    assert "current_track" in examples["intents"]
    assert "playback_control" in examples["intents"]
    assert "artist" in examples["intents"]
    assert "playlist" in examples["intents"]
    assert "Welk nummer draait er nu?" in examples["intents"]["current_track"]["nl"]
    assert "What song is playing?" in examples["intents"]["current_track"]["en"]
    assert "Stop muziek" in examples["intents"]["playback_control"]["commands"]["pause"]["nl"]
    assert "Start muziek" in examples["intents"]["playback_control"]["commands"]["play"]["nl"]
    assert "Zet harder" in examples["intents"]["playback_control"]["commands"]["volume_up"]["nl"]
    assert "Zet zachter" in examples["intents"]["playback_control"]["commands"]["volume_down"]["nl"]
    assert "Volgende nummer" in examples["intents"]["playback_control"]["commands"]["next"]["nl"]
    assert "Vorig nummer" in examples["intents"]["playback_control"]["commands"]["previous"]["nl"]
    assert "Speel playlist DJConnect" in examples["intents"]["playlist"]["nl"]


def test_install_script_configures_xwrapper_for_systemd_kiosk_start() -> None:
    script = ROOT.joinpath("scripts/install.sh").read_text(encoding="utf-8")

    assert "configure_xwrapper" in script
    assert "/etc/X11/Xwrapper.config" in script
    assert "allowed_users=anybody" in script
    assert "needs_root_rights=yes" in script
    assert "sed -i" in script
    assert "configure_xwrapper" in script.split("cp \"${DJCONNECT_ROOT}/current/systemd/\"", 1)[0]
    assert "install --only-binary=:all:" in script
    assert 'install -d -o root -g root "$DJCONNECT_PIP_CACHE"' in script
    assert "/opt/djconnect/pip-cache" not in script
    assert "resumes completed install steps after an interrupted run or reboot" in script


def test_install_script_checks_free_space_before_large_dependency_downloads() -> None:
    script = ROOT.joinpath("scripts/install.sh").read_text(encoding="utf-8")

    assert "DJCONNECT_MIN_FREE_MB" in script
    assert 'DJCONNECT_MIN_FREE_MB="${DJCONNECT_MIN_FREE_MB:-3000}"' in script
    assert "check_free_space" in script
    assert "df -Pm" in script
    assert "df -ih" in script
    assert "Not enough free disk space" in script
    assert "Run the repo bootstrap to expand the root filesystem" in script
    assert "check_free_space" in script.split("download_release", 1)[0]


def test_install_script_checks_active_swap_before_large_dependency_downloads() -> None:
    script = ROOT.joinpath("scripts/install.sh").read_text(encoding="utf-8")

    assert "DJCONNECT_MIN_SWAP_MB" in script
    assert "check_swap" in script
    assert "SwapTotal" in script
    assert "Not enough active swap" in script
    assert "Run the repo bootstrap to configure the 1GB swapfile" in script
    assert "check_swap" in script.split("download_release", 1)[0]


def test_install_script_outputs_resources_and_extra_prerequisite_checks() -> None:
    script = ROOT.joinpath("scripts/install.sh").read_text(encoding="utf-8")

    assert "print_resources" in script
    assert "installer start" in script
    assert "installer complete" in script
    assert "MemAvailable" in script
    assert "SwapTotal" in script
    assert "df -h" in script
    assert "print_thermal_status" in script
    assert "vcgencmd measure_temp" in script
    assert "vcgencmd get_throttled" in script
    assert "check_cpu_architecture" in script
    assert "aarch64|arm64" in script
    assert "check_python_version" in script
    assert "Python 3.11 or newer is required" in script
    assert "check_writable_paths" in script
    assert "check_github_reachable" in script
    assert "curl -fsSIL" in script
    assert "Cannot reach DJConnect Pi release asset" in script


def test_bootstrap_release_download_matches_project_version() -> None:
    bootstrap = ROOT.joinpath("docs/BOOTSTRAP.md").read_text(encoding="utf-8")
    readme = ROOT.joinpath("README.md").read_text(encoding="utf-8")
    version = _project_version()

    assert f"djconnect-pi-{version}.tar.gz" in bootstrap
    assert f"cd djconnect-pi-{version}" in bootstrap
    assert f"djconnect-pi-{version}.tar.gz" in readme
    assert f"cd djconnect-pi-{version}" in readme


def test_manual_update_documentation_describes_public_release_and_dev_checkout_paths() -> None:
    bootstrap = ROOT.joinpath("docs/BOOTSTRAP.md").read_text(encoding="utf-8")
    readme = ROOT.joinpath("README.md").read_text(encoding="utf-8")

    assert "Manual Software Update" in bootstrap
    assert "Manual Pi Software Update" in readme
    assert "public release tarball" in bootstrap
    assert "git pull --ff-only" in bootstrap
    assert "git pull --ff-only" in readme
    assert "keeps an existing `/opt/djconnect/config/client.json`" in bootstrap
    assert "restarts `djconnect-api.service` and `djconnect-client.service`" in readme


def test_os_bootstrap_documentation_uses_idempotent_checkout_flow() -> None:
    bootstrap = ROOT.joinpath("docs/BOOTSTRAP.md").read_text(encoding="utf-8")
    readme = ROOT.joinpath("README.md").read_text(encoding="utf-8")

    for text in (bootstrap, readme):
        assert 'if [ -d "$HOME/djconnect-pi/.git" ]; then' in text
        assert "git pull --ff-only" in text
        assert 'git clone https://github.com/pcvantol/djconnect-pi.git "$HOME/djconnect-pi"' in text
        assert "sudo ./scripts/bootstrap_raspberry_pi_os.sh" in text


def test_bootstrap_documentation_targets_raspberry_pi_os_lite() -> None:
    bootstrap = ROOT.joinpath("docs/BOOTSTRAP.md").read_text(encoding="utf-8")
    readme = ROOT.joinpath("README.md").read_text(encoding="utf-8")

    for text in (bootstrap, readme):
        assert "Raspberry Pi OS Lite 64-bit" in text
    assert "Choose Raspberry Pi OS Lite 64-bit Bookworm" in bootstrap
    assert "Raspberry Pi OS Desktop/GUI" not in bootstrap
    assert "Desktop/GUI image" not in readme


def test_glances_is_not_installed_or_documented() -> None:
    script = ROOT.joinpath("scripts/bootstrap_raspberry_pi_os.sh").read_text(encoding="utf-8")
    bootstrap = ROOT.joinpath("docs/BOOTSTRAP.md").read_text(encoding="utf-8")
    readme = ROOT.joinpath("README.md").read_text(encoding="utf-8")

    for text in (script, bootstrap, readme):
        assert "glances" not in text.lower()
        assert "61208" not in text
        assert "djconnect-glances" not in text
        assert "glances-web.service" not in text


def test_syncprompt_and_roadmap_policy_use_canonical_home_assistant_repo_only() -> None:
    forbidden = [
        "SYNC_PROMPTS.md",
        "PRODUCT_ROADMAP.md",
        "HA_SYNC_PROMPT.md",
        "ESP_SYNC_PROMPT.md",
        "IOS_MACOS_APP_HANDOFF.md",
        "APPLE_APP_SYNC_PROMPTS.md",
        "docs/SYNC_PROMPTS.md",
    ]

    for relative in forbidden:
        assert not ROOT.joinpath(relative).exists(), f"{relative} must not exist in the Raspberry Pi repo"

    agent_notes = ROOT.joinpath("AGENTS.md").read_text(encoding="utf-8")
    handoff = ROOT.joinpath("HANDOFF.md").read_text(encoding="utf-8")
    assert "pcvantol/djconnect/SYNC_PROMPTS.md" in agent_notes
    assert "pcvantol/djconnect/SYNC_PROMPTS.md" in handoff
    assert "pcvantol/djconnect/PRODUCT_ROADMAP.md" in handoff
    assert "byte-for-byte across" not in agent_notes
