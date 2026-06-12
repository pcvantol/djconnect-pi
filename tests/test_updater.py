from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from djconnect_pi import updater


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
    info = tarfile.TarInfo("VERSION")
    info.size = len(data)
    with tarfile.open(path, "w:gz") as tar:
        tar.addfile(info, io.BytesIO(data))


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


def test_install_release_extracts_and_switches_current_symlink(tmp_path: Path) -> None:
    bundle = tmp_path / "release.tar.gz"
    root = tmp_path / "root"
    write_tar(bundle)

    target = updater.install_release(bundle, "0.2.0", root)

    assert target == root / "releases" / "0.2.0"
    assert (target / "VERSION").read_text(encoding="utf-8") == "0.2.0"
    assert (root / "current").is_symlink()
    assert (root / "current" / "VERSION").read_text(encoding="utf-8") == "0.2.0"


def test_run_dry_run_returns_selected_assets(tmp_path: Path) -> None:
    cfg = updater.UpdaterConfig(repo="pcvantol/djconnect-pi", install_root=tmp_path)

    with patch("djconnect_pi.updater.github_latest_release", return_value=make_release()):
        result = json.loads(updater.run(cfg, dry_run=True))

    assert result == {
        "version": "0.2.0",
        "bundle": "https://example/bundle.tar.gz",
        "checksum": "https://example/bundle.sha256",
    }


def test_run_passes_prerelease_flag_for_beta_channel(tmp_path: Path) -> None:
    cfg = updater.UpdaterConfig(repo="pcvantol/djconnect-pi", channel="beta", install_root=tmp_path)

    with patch("djconnect_pi.updater.github_latest_release", return_value=make_release()) as latest:
        updater.run(cfg, dry_run=True)

    latest.assert_called_once_with("pcvantol/djconnect-pi", True)


def test_run_skips_when_current_version_matches(tmp_path: Path) -> None:
    current = tmp_path / "current"
    current.mkdir()
    (current / "VERSION").write_text("0.2.0", encoding="utf-8")

    cfg = updater.UpdaterConfig(repo="pcvantol/djconnect-pi", install_root=tmp_path)

    with patch("djconnect_pi.updater.github_latest_release", return_value=make_release()):
        assert updater.run(cfg) == "Already on 0.2.0"


def test_run_restarts_api_and_client_services_after_install(tmp_path: Path) -> None:
    cfg = updater.UpdaterConfig(repo="pcvantol/djconnect-pi", install_root=tmp_path)

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
