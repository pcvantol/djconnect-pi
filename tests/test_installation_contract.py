from __future__ import annotations

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
    script = ROOT.joinpath("scripts/install_raspberry_pi.sh").read_text(encoding="utf-8")

    assert "systemctl enable djconnect-api.service" in script
    assert "systemctl enable djconnect-client.service" in script
    assert "systemctl restart djconnect-api.service" in script
    assert "systemctl restart djconnect-client.service" in script
    assert "Local Client API starts automatically via djconnect-api.service." in script


def test_install_script_is_executable_in_git() -> None:
    result = subprocess.run(
        ["git", "ls-files", "-s", "scripts/install_raspberry_pi.sh"],
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

    assert "djconnect-pi-api --config /opt/djconnect/config/client.json" in api_service
    assert "Restart=always" in api_service
    assert "djconnect-pi-client --config /opt/djconnect/config/client.json" in client_service
    assert "DJCONNECT_DISABLE_CLIENT_API" not in client_service


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
    assert 'gh run list' in script
    assert '--branch "$tag"' in script
    assert "--status completed" in script
    assert 'gh run delete "$run_id"' in script


def test_release_assets_include_installation_materials() -> None:
    release_script = ROOT.joinpath("release.sh").read_text(encoding="utf-8")
    workflow = ROOT.joinpath(".github/workflows/publish-release.yml").read_text(encoding="utf-8")

    for text in (release_script, workflow):
        assert "docs src systemd" in text
        assert 'mkdir -p "$dist/scripts"' in text or 'mkdir -p "${dist}/scripts"' in text
        assert "cp scripts/install_raspberry_pi.sh" in text
        assert "cp scripts/bootstrap_raspberry_pi_os.sh" not in text


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
    script = ROOT.joinpath("scripts/install_raspberry_pi.sh").read_text(encoding="utf-8")

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
    script = ROOT.joinpath("scripts/install_raspberry_pi.sh").read_text(encoding="utf-8")

    assert "/etc/default/locale" in script
    assert 'export LANG="${LANG:-C.UTF-8}"' in script
    assert 'export LC_CTYPE="${LC_CTYPE:-${LANG}}"' in script


def test_install_script_does_not_provision_wifi() -> None:
    script = ROOT.joinpath("scripts/install_raspberry_pi.sh").read_text(encoding="utf-8")

    assert "DJCONNECT_WIFI" not in script
    assert "configure_wifi" not in script
    assert "wpa_supplicant" not in script
    assert "nmcli" not in script
    assert "wpa_passphrase" not in script


def test_install_script_reports_version_in_help_and_runtime() -> None:
    script = ROOT.joinpath("scripts/install_raspberry_pi.sh").read_text(encoding="utf-8")

    assert "Version:" in script
    assert "DJConnect Pi installer for client ${DJCONNECT_VERSION}" in script
    assert 'log "DJConnect Pi installer ${DJCONNECT_VERSION}"' in script


def test_install_script_verifies_release_checksum_independent_of_sha_filename() -> None:
    script = ROOT.joinpath("scripts/install_raspberry_pi.sh").read_text(encoding="utf-8")

    assert "shasum -a 256 -c release.sha256" not in script
    assert "expected_hash=" in script
    assert "actual_hash=" in script
    assert "Release checksum mismatch" in script


def test_install_script_can_resume_after_reboot_or_interruption() -> None:
    script = ROOT.joinpath("scripts/install_raspberry_pi.sh").read_text(encoding="utf-8")

    assert "DJCONNECT_INSTALL_STATE" in script
    assert "DJCONNECT_PIP_CACHE" in script
    assert 'marker_done "release_unpacked"' in script
    assert 'mark_done "release_unpacked"' in script
    assert 'marker_done "venv_ready"' in script
    assert 'mark_done "venv_ready"' in script
    assert "install_python_dependencies" in script
    assert "activate_release" in script
    assert "PIP_CACHE_DIR=\"$DJCONNECT_PIP_CACHE\"" in script
    assert "install --prefer-binary" in script
    assert "resumes completed install steps after an interrupted run or reboot" in script


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
    sync_prompt = ROOT.joinpath("SYNC_PROMPTS.md").read_text(encoding="utf-8")

    for text in (script, bootstrap, readme):
        assert "glances" not in text.lower()
        assert "61208" not in text
        assert "djconnect-glances" not in text
        assert "glances-web.service" not in text
    assert "must not install or manage\n  Glances" in sync_prompt
