from __future__ import annotations

import io
import json
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


def test_install_release_installs_dependencies_before_activation(tmp_path: Path) -> None:
    bundle = tmp_path / "release.tar.gz"
    root = tmp_path / "root"
    write_tar(bundle)

    with (
        patch("djconnect_pi.updater.install_python_dependencies") as install_python_dependencies,
        patch("djconnect_pi.updater.activate_release") as activate_release,
    ):
        target = updater.install_release(bundle, "0.2.0", root)

    install_python_dependencies.assert_called_once_with(target, "0.2.0")
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


def test_validate_release_entrypoints_rejects_missing_wrappers(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="missing executable"):
        updater.validate_release_entrypoints(tmp_path)


def test_run_dry_run_returns_selected_assets(tmp_path: Path) -> None:
    cfg = updater.UpdaterConfig(repo="pcvantol/djconnect-pi-releases", install_root=tmp_path)

    with patch("djconnect_pi.updater.github_latest_release", return_value=make_release()):
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

    latest.assert_called_once_with("pcvantol/djconnect-pi-releases", True)


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

    with patch("djconnect_pi.updater.github_latest_release", return_value=make_release()):
        assert updater.run(cfg) == "Already on 0.2.0"


def test_run_restarts_api_and_client_services_after_install(tmp_path: Path) -> None:
    cfg = updater.UpdaterConfig(repo="pcvantol/djconnect-pi-releases", install_root=tmp_path)

    with (
        patch("djconnect_pi.updater.github_latest_release", return_value=make_release()),
        patch("djconnect_pi.updater.asset_url", side_effect=["bundle-url", "checksum-url"]),
        patch("djconnect_pi.updater.download"),
        patch("djconnect_pi.updater.verify_sha256"),
        patch("djconnect_pi.updater.install_release"),
        patch("djconnect_pi.updater.restart_services") as restart_services,
    ):
        assert updater.run(cfg) == "Installed 0.2.0"

    restart_services.assert_called_once_with(("djconnect-api.service", "djconnect-client.service"))
