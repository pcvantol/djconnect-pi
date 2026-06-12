from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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
    assert "DJCONNECT_RELEASES_TOKEN" in workflow
    assert 'tags:' in workflow
    assert '"v*.*.*"' in workflow
