from __future__ import annotations

from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def _project_version() -> str:
    data = tomllib.loads(ROOT.joinpath("pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def test_install_script_enables_local_api_service() -> None:
    script = ROOT.joinpath("scripts/install_raspberry_pi.sh").read_text(encoding="utf-8")

    assert "systemctl enable --now djconnect-api.service" in script
    assert "systemctl enable --now djconnect-client.service" in script
    assert "Local Client API starts automatically via djconnect-api.service." in script


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
        assert "docs scripts src systemd" in text
        assert "scripts/install_raspberry_pi.sh" in text or "scripts" in text


def test_install_script_uses_modern_hyperpixel_overlay_and_dark_mode() -> None:
    script = ROOT.joinpath("scripts/install_raspberry_pi.sh").read_text(encoding="utf-8")

    assert "DJCONNECT_HYPERPIXEL_MODEL" in script
    assert "vc4-kms-dpi-hyperpixel4sq" in script
    assert "vc4-kms-dpi-hyperpixel4" in script
    assert "hyperpixel4-init.service" in script
    assert "raspi-config nonint do_i2c 1" in script
    assert "raspi-config nonint do_spi 1" in script
    assert "DJCONNECT_CONFIGURE_DARK_MODE" in script
    assert "gtk-application-prefer-dark-theme=true" in script


def test_install_script_reports_version_in_help_and_runtime() -> None:
    script = ROOT.joinpath("scripts/install_raspberry_pi.sh").read_text(encoding="utf-8")

    assert "Version:" in script
    assert "DJConnect Pi installer for client ${DJCONNECT_VERSION}" in script
    assert 'log "DJConnect Pi installer ${DJCONNECT_VERSION}"' in script


def test_bootstrap_release_download_matches_project_version() -> None:
    bootstrap = ROOT.joinpath("docs/BOOTSTRAP.md").read_text(encoding="utf-8")
    readme = ROOT.joinpath("README.md").read_text(encoding="utf-8")
    version = _project_version()

    assert f"djconnect-pi-{version}.tar.gz" in bootstrap
    assert f"cd djconnect-pi-{version}" in bootstrap
    assert f"djconnect-pi-{version}.tar.gz" in readme
    assert f"cd djconnect-pi-{version}" in readme
