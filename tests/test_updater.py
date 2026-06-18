from __future__ import annotations

import io
import json
import os
import tarfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from djconnect_pi import updater
from djconnect_pi.config import Config, save_config


def make_release() -> dict[str, Any]:
    return {
        "tag_name": "v0.2.0",
        "draft": False,
        "prerelease": False,
        "assets": [
            {"name": "djconnect-pi-0.2.0.tar.gz", "browser_download_url": "https://example/bundle.tar.gz"},
            {"name": "djconnect-pi-0.2.0.sha256", "browser_download_url": "https://example/bundle.sha256"},
        ],
    }


def write_tar(path: Path, version: str = "0.2.0") -> None:
    data = version.encode()
    info = tarfile.TarInfo(f"djconnect-pi-{version}/VERSION")
    info.size = len(data)
    wheel_data = b"wheel"
    wheel_info = tarfile.TarInfo(f"djconnect-pi-{version}/wheels/djconnect_pi-{version}-py3-none-any.whl")
    wheel_info.size = len(wheel_data)
    with tarfile.open(path, "w:gz") as tar:
        tar.addfile(info, io.BytesIO(data))
        tar.addfile(wheel_info, io.BytesIO(wheel_data))


def test_asset_url_finds_suffix() -> None:
    assert updater.asset_url(make_release(), ".sha256") == "https://example/bundle.sha256"


def test_include_prerelease_only_for_beta_channel() -> None:
    assert updater.include_prerelease("stable") is False
    assert updater.include_prerelease("beta") is True


def test_public_latest_release_reads_rate_limit_safe_manifest() -> None:
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "version": "0.2.0",
                "bundle": "https://example/djconnect-pi-0.2.0.tar.gz",
                "checksum": "https://example/djconnect-pi-0.2.0.sha256",
            }

    with patch("djconnect_pi.updater.requests.get", return_value=Response()) as get:
        release = updater.public_latest_release("pcvantol/djconnect-pi-releases")

    get.assert_called_once_with(
        "https://github.com/pcvantol/djconnect-pi-releases/releases/latest/download/djconnect-pi-latest.json",
        timeout=20,
    )
    assert release["tag_name"] == "v0.2.0"
    assert updater.asset_url(release, ".tar.gz") == "https://example/djconnect-pi-0.2.0.tar.gz"


def test_asset_url_raises_for_missing_suffix() -> None:
    with pytest.raises(RuntimeError, match="No release asset"):
        updater.asset_url(make_release(), ".zip")


def test_verify_sha256_accepts_matching_checksum(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle.tar.gz"
    checksum = tmp_path / "bundle.sha256"
    bundle.write_bytes(b"payload")
    checksum.write_text(f"{updater.sha256(bundle)}  bundle.tar.gz\n", encoding="utf-8")

    updater.verify_sha256(bundle, checksum)


def test_verify_sha256_rejects_mismatch(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle.tar.gz"
    checksum = tmp_path / "bundle.sha256"
    bundle.write_bytes(b"payload")
    checksum.write_text("0" * 64, encoding="utf-8")

    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        updater.verify_sha256(bundle, checksum)


def test_unpack_release_strips_bundle_root_directory(tmp_path: Path) -> None:
    bundle = tmp_path / "release.tar.gz"
    root = tmp_path / "root"
    write_tar(bundle)

    target = updater.unpack_release(bundle, "0.2.0", root)

    assert target == root / "releases" / "0.2.0"
    assert (target / "VERSION").read_text(encoding="utf-8") == "0.2.0"
    assert (target / "wheels" / "djconnect_pi-0.2.0-py3-none-any.whl").read_bytes() == b"wheel"
    assert not (target / "djconnect-pi-0.2.0").exists()


def test_unpack_release_keeps_existing_release_for_resume(tmp_path: Path) -> None:
    bundle = tmp_path / "release.tar.gz"
    root = tmp_path / "root"
    target = root / "releases" / "0.2.0"
    state_dir = target / ".install-state"
    (target / "wheels").mkdir(parents=True)
    state_dir.mkdir()
    (target / "VERSION").write_text("0.2.0\n", encoding="utf-8")
    (target / "wheels" / "djconnect_pi-0.2.0-py3-none-any.whl").write_bytes(b"wheel")
    (state_dir / "shiboken6_installed").write_text("ok\n", encoding="utf-8")
    write_tar(bundle)

    assert updater.unpack_release(bundle, "0.2.0", root) == target
    assert (state_dir / "shiboken6_installed").exists()


def test_install_release_installs_dependencies_before_activation(tmp_path: Path) -> None:
    bundle = tmp_path / "release.tar.gz"
    root = tmp_path / "root"
    write_tar(bundle)

    with (
        patch("djconnect_pi.updater.install_python_dependencies") as install_python_dependencies,
        patch("djconnect_pi.updater.activate_release") as activate_release,
    ):
        target = updater.install_release(bundle, "0.2.0", root)

    install_python_dependencies.assert_called_once_with(target, "0.2.0", status=None)
    activate_release.assert_called_once_with(target, root)


def test_activate_release_switches_current_symlink(tmp_path: Path) -> None:
    root = tmp_path / "root"
    target = root / "releases" / "0.2.0"
    target.mkdir(parents=True)
    (target / "VERSION").write_text("0.2.0", encoding="utf-8")

    updater.activate_release(target, root)

    assert (root / "current").is_symlink()
    assert (root / "current" / "VERSION").read_text(encoding="utf-8") == "0.2.0"


def test_wheel_for_release_finds_bundled_wheel(tmp_path: Path) -> None:
    release_dir = tmp_path / "release"
    wheels_dir = release_dir / "wheels"
    wheels_dir.mkdir(parents=True)
    wheel = wheels_dir / "djconnect_pi-0.2.0-py3-none-any.whl"
    wheel.write_bytes(b"wheel")

    assert updater.wheel_for_release(release_dir, "0.2.0") == wheel


def test_pip_environment_uses_cache_local_tmp(tmp_path: Path) -> None:
    env = updater.pip_environment(tmp_path / "pip-cache")

    assert env["PIP_CACHE_DIR"] == str(tmp_path / "pip-cache")
    assert env["TMPDIR"] == str(tmp_path / "pip-cache" / "tmp")
    assert (tmp_path / "pip-cache" / "tmp").is_dir()


def test_install_python_dependencies_uses_pip_cache_env(tmp_path: Path) -> None:
    release_dir = tmp_path / "release"
    wheels_dir = release_dir / "wheels"
    wheels_dir.mkdir(parents=True)
    (wheels_dir / "djconnect_pi-0.2.0-py3-none-any.whl").write_bytes(b"wheel")

    with (
        patch("djconnect_pi.updater.pip_environment", return_value={"PIP_CACHE_DIR": "/cache", "TMPDIR": "/cache/tmp"}),
        patch("djconnect_pi.updater.validate_release_entrypoints"),
        patch("djconnect_pi.updater.subprocess.run") as run,
    ):
        updater.install_python_dependencies(release_dir, "0.2.0")

    assert run.call_args_list[1].kwargs["env"] == {"PIP_CACHE_DIR": "/cache", "TMPDIR": "/cache/tmp"}
    assert run.call_args_list[2].kwargs["env"] == {"PIP_CACHE_DIR": "/cache", "TMPDIR": "/cache/tmp"}
    assert run.call_args_list[1].args[0][-2:] == ["pip", "--version"]
    assert run.call_args_list[3].args[0][-1] == "shiboken6>=6.7"
    assert run.call_args_list[4].args[0][-1] == "PySide6_Essentials>=6.7"
    assert run.call_args_list[5].args[0][-1] == "PySide6_Addons>=6.7"
    assert run.call_args_list[6].args[0][-1] == "PySide6>=6.7"
    assert run.call_args_list[7].args[0][-1] == "requests>=2.31"
    assert run.call_args_list[8].args[0][-1] == "zeroconf>=0.132"


def test_install_python_dependencies_can_force_pip_upgrade(tmp_path: Path, monkeypatch) -> None:
    release_dir = tmp_path / "release"
    wheels_dir = release_dir / "wheels"
    wheels_dir.mkdir(parents=True)
    (wheels_dir / "djconnect_pi-0.2.0-py3-none-any.whl").write_bytes(b"wheel")
    monkeypatch.setenv("DJCONNECT_UPGRADE_PIP", "1")

    with (
        patch("djconnect_pi.updater.pip_environment", return_value={"PIP_CACHE_DIR": "/cache", "TMPDIR": "/cache/tmp"}),
        patch("djconnect_pi.updater.validate_release_entrypoints"),
        patch("djconnect_pi.updater.subprocess.run") as run,
    ):
        updater.install_python_dependencies(release_dir, "0.2.0")

    assert run.call_args_list[1].args[0][-4:] == ["pip", "install", "--upgrade", "pip"]


def test_install_python_dependencies_resumes_completed_steps(tmp_path: Path) -> None:
    release_dir = tmp_path / "release"
    wheels_dir = release_dir / "wheels"
    state_dir = release_dir / ".install-state"
    wheels_dir.mkdir(parents=True)
    state_dir.mkdir()
    (release_dir / ".venv" / "bin").mkdir(parents=True)
    (state_dir / "venv_created").write_text("ok\n", encoding="utf-8")
    (state_dir / "pip_checked").write_text("ok\n", encoding="utf-8")
    (state_dir / "build_tools_installed").write_text("ok\n", encoding="utf-8")
    (state_dir / "shiboken6_installed").write_text("ok\n", encoding="utf-8")
    (state_dir / "pyside6_essentials_installed").write_text("ok\n", encoding="utf-8")
    (state_dir / "pyside6_addons_installed").write_text("ok\n", encoding="utf-8")
    (state_dir / "pyside6_installed").write_text("ok\n", encoding="utf-8")
    (wheels_dir / "djconnect_pi-0.2.0-py3-none-any.whl").write_bytes(b"wheel")

    with (
        patch("djconnect_pi.updater.pip_environment", return_value={"PIP_CACHE_DIR": "/cache", "TMPDIR": "/cache/tmp"}),
        patch("djconnect_pi.updater.validate_release_entrypoints"),
        patch("djconnect_pi.updater.subprocess.run") as run,
    ):
        updater.install_python_dependencies(release_dir, "0.2.0")

    commands = [call.args[0] for call in run.call_args_list]
    assert not any(command[:3] == ["python3", "-m", "venv"] for command in commands)
    assert all("PySide6>=6.7" not in command for command in commands)
    assert all("PySide6_Essentials>=6.7" not in command for command in commands)
    assert all("PySide6_Addons>=6.7" not in command for command in commands)
    assert all("shiboken6>=6.7" not in command for command in commands)
    assert commands[0][-1] == "requests>=2.31"
    assert commands[1][-1] == "zeroconf>=0.132"
    assert commands[2][-1].endswith("djconnect_pi-0.2.0-py3-none-any.whl")
    assert (state_dir / "requests_installed").exists()
    assert (state_dir / "zeroconf_installed").exists()
    assert (state_dir / "wheel_installed").exists()


def test_validate_release_entrypoints_rejects_missing_wrappers(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="missing executable"):
        updater.validate_release_entrypoints(tmp_path)


def test_cleanup_old_releases_keeps_current_and_previous(tmp_path: Path) -> None:
    root = tmp_path / "root"
    releases = root / "releases"
    releases.mkdir(parents=True)
    current = releases / "0.4.0"
    previous = releases / "0.3.0"
    old = releases / "0.2.0"
    tmp = releases / ".0.5.0.tmp"
    for index, path in enumerate((old, previous, current, tmp), start=1):
        path.mkdir()
        (path / "VERSION").write_text(path.name.strip(".tmp"), encoding="utf-8")
        timestamp = 1_700_000_000 + index
        path.touch()
        path.chmod(0o755)
        os.utime(path, (timestamp, timestamp))
    (root / "current").symlink_to(current)

    removed = updater.cleanup_old_releases(root, keep=2)

    assert current.exists()
    assert previous.exists()
    assert not old.exists()
    assert not tmp.exists()
    assert old in removed


def test_run_dry_run_returns_selected_assets(tmp_path: Path) -> None:
    cfg = updater.UpdaterConfig(repo="pcvantol/djconnect-pi-releases", install_root=tmp_path)

    with patch("djconnect_pi.updater.public_latest_release", return_value=make_release()):
        result = json.loads(updater.run(cfg, dry_run=True))

    assert result == {
        "version": "0.2.0",
        "bundle": "https://example/bundle.tar.gz",
        "checksum": "https://example/bundle.sha256",
    }


def test_run_passes_prerelease_flag_for_beta_channel(tmp_path: Path) -> None:
    cfg = updater.UpdaterConfig(repo="pcvantol/djconnect-pi-releases", channel="beta", install_root=tmp_path)

    with patch("djconnect_pi.updater.github_latest_release", return_value=make_release()) as latest:
        updater.run(cfg, dry_run=True)

    latest.assert_called_once_with("pcvantol/djconnect-pi-releases", include_prerelease=True)


def test_run_stable_uses_public_manifest_instead_of_github_api(tmp_path: Path) -> None:
    cfg = updater.UpdaterConfig(repo="pcvantol/djconnect-pi-releases", install_root=tmp_path)

    with (
        patch("djconnect_pi.updater.public_latest_release", return_value=make_release()) as latest_manifest,
        patch("djconnect_pi.updater.github_latest_release") as github_latest,
    ):
        updater.run(cfg, dry_run=True)

    latest_manifest.assert_called_once_with("pcvantol/djconnect-pi-releases")
    github_latest.assert_not_called()


def test_config_from_file_uses_touchscreen_update_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    save_config(config_path, Config(update_repo="pcvantol/custom-pi", update_channel="beta"))

    cfg = updater.config_from_file(config_path, install_root=tmp_path)

    assert cfg.repo == "pcvantol/custom-pi"
    assert cfg.channel == "beta"
    assert cfg.install_root == tmp_path


def test_config_from_file_allows_cli_overrides(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    save_config(config_path, Config(update_repo="pcvantol/custom-pi", update_channel="beta"))

    cfg = updater.config_from_file(
        config_path,
        repo_override="pcvantol/djconnect-pi-releases",
        channel_override="stable",
        install_root=tmp_path,
    )

    assert cfg.repo == "pcvantol/djconnect-pi-releases"
    assert cfg.channel == "stable"


def test_run_skips_when_current_version_matches(tmp_path: Path) -> None:
    current = tmp_path / "current"
    current.mkdir()
    (current / "VERSION").write_text("0.2.0", encoding="utf-8")

    cfg = updater.UpdaterConfig(repo="pcvantol/djconnect-pi-releases", install_root=tmp_path)

    with (
        patch("djconnect_pi.updater.public_latest_release", return_value=make_release()),
        patch("djconnect_pi.updater.stop_services") as stop_services,
    ):
        assert updater.run(cfg) == "Already on 0.2.0"

    stop_services.assert_not_called()


def test_run_dry_run_does_not_stop_services(tmp_path: Path) -> None:
    cfg = updater.UpdaterConfig(repo="pcvantol/djconnect-pi-releases", install_root=tmp_path)

    with (
        patch("djconnect_pi.updater.public_latest_release", return_value=make_release()),
        patch("djconnect_pi.updater.stop_services") as stop_services,
    ):
        result = json.loads(updater.run(cfg, dry_run=True))

    assert result["version"] == "0.2.0"
    stop_services.assert_not_called()


def test_run_restarts_api_and_client_services_after_install(tmp_path: Path) -> None:
    cfg = updater.UpdaterConfig(repo="pcvantol/djconnect-pi-releases", install_root=tmp_path)
    download_calls = 0

    def fake_download(*_args: object) -> None:
        nonlocal download_calls
        download_calls += 1
        assert stop_services.called

    with (
        patch("djconnect_pi.updater.public_latest_release", return_value=make_release()),
        patch("djconnect_pi.updater.asset_url", side_effect=["bundle-url", "checksum-url"]),
        patch("djconnect_pi.updater.stop_services") as stop_services,
        patch("djconnect_pi.updater.start_service") as start_service,
        patch("djconnect_pi.updater.stop_service") as stop_service,
        patch("djconnect_pi.updater.download", side_effect=fake_download),
        patch("djconnect_pi.updater.verify_sha256"),
        patch("djconnect_pi.updater.install_release"),
        patch("djconnect_pi.updater.cleanup_old_releases") as cleanup_old_releases,
        patch("djconnect_pi.updater.restart_services") as restart_services,
    ):
        assert updater.run(cfg) == "Installed 0.2.0"

    stop_services.assert_called_once_with(
        (
            "djconnect-client.service",
            "djconnect-api.service",
            "djconnect-maintenance.service",
            "djconnect-watchdog.service",
        )
    )
    start_service.assert_called_once_with("djconnect-update-ui.service")
    stop_service.assert_called_once_with("djconnect-update-ui.service")
    assert download_calls == 2
    cleanup_old_releases.assert_called_once_with(tmp_path, 2)
    restart_services.assert_called_once_with(("djconnect-api.service", "djconnect-client.service"))


def test_run_writes_updater_status_file(tmp_path: Path) -> None:
    cfg = updater.UpdaterConfig(repo="pcvantol/djconnect-pi-releases", install_root=tmp_path, status_file=tmp_path / "status.json")

    with (
        patch("djconnect_pi.updater.public_latest_release", return_value=make_release()),
        patch("djconnect_pi.updater.asset_url", side_effect=["bundle-url", "checksum-url"]),
        patch("djconnect_pi.updater.stop_services"),
        patch("djconnect_pi.updater.start_service"),
        patch("djconnect_pi.updater.stop_service"),
        patch("djconnect_pi.updater.download"),
        patch("djconnect_pi.updater.verify_sha256"),
        patch("djconnect_pi.updater.install_release"),
        patch("djconnect_pi.updater.cleanup_old_releases"),
        patch("djconnect_pi.updater.restart_services"),
    ):
        assert updater.run(cfg) == "Installed 0.2.0"

    status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert status["state"] == "complete"
    assert status["progress"] == 100


def test_run_keeps_update_ui_visible_and_writes_failed_status_on_error(tmp_path: Path) -> None:
    cfg = updater.UpdaterConfig(repo="pcvantol/djconnect-pi-releases", install_root=tmp_path, status_file=tmp_path / "status.json")

    with (
        patch("djconnect_pi.updater.public_latest_release", return_value=make_release()),
        patch("djconnect_pi.updater.asset_url", side_effect=["bundle-url", "checksum-url"]),
        patch("djconnect_pi.updater.stop_services"),
        patch("djconnect_pi.updater.start_service") as start_service,
        patch("djconnect_pi.updater.stop_service") as stop_service,
        patch("djconnect_pi.updater.download", side_effect=RuntimeError("network down")),
        patch("djconnect_pi.updater.restart_services") as restart_services,
    ):
        with pytest.raises(RuntimeError, match="network down"):
            updater.run(cfg)

    start_service.assert_called_once_with("djconnect-update-ui.service")
    stop_service.assert_not_called()
    restart_services.assert_not_called()
    status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert status["state"] == "failed"
    assert "network down" in status["message"]


def test_stop_services_uses_best_effort_systemctl_stop() -> None:
    with patch("djconnect_pi.updater.subprocess.run") as run:
        updater.stop_services(("djconnect-client.service", "djconnect-api.service"))

    assert run.call_args_list[0].args[0] == ["systemctl", "stop", "djconnect-client.service"]
    assert run.call_args_list[0].kwargs["check"] is False
    assert run.call_args_list[1].args[0] == ["systemctl", "stop", "djconnect-api.service"]
    assert run.call_args_list[1].kwargs["check"] is False


def test_start_and_stop_service_are_best_effort() -> None:
    with patch("djconnect_pi.updater.subprocess.run") as run:
        updater.start_service("djconnect-update-ui.service")
        updater.stop_service("djconnect-update-ui.service")

    assert run.call_args_list[0].args[0] == ["systemctl", "start", "djconnect-update-ui.service"]
    assert run.call_args_list[0].kwargs["check"] is False
    assert run.call_args_list[1].args[0] == ["systemctl", "stop", "djconnect-update-ui.service"]
    assert run.call_args_list[1].kwargs["check"] is False
