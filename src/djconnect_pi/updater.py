from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile

import requests

from .config import DEFAULT_CONFIG_PATH, load_config


@dataclass
class UpdaterConfig:
    repo: str
    channel: str = "stable"
    install_root: Path = Path("/opt/djconnect")
    service_names: Sequence[str] = ("djconnect-api.service", "djconnect-client.service")


def include_prerelease(channel: str) -> bool:
    return channel == "beta"


def github_latest_release(repo: str, include_prerelease: bool) -> dict:
    response = requests.get(f"https://api.github.com/repos/{repo}/releases", timeout=20)
    response.raise_for_status()
    releases = response.json()
    for release in releases:
        if release.get("draft"):
            continue
        if release.get("prerelease") and not include_prerelease:
            continue
        return release
    raise RuntimeError("No suitable GitHub release found")


def asset_url(release: dict, suffix: str) -> str:
    for asset in release.get("assets", []):
        name = str(asset.get("name") or "")
        if name.endswith(suffix):
            return str(asset["browser_download_url"])
    raise RuntimeError(f"No release asset ending in {suffix}")


def download(url: str, target: Path) -> None:
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    handle.write(chunk)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256(bundle: Path, checksum_file: Path) -> None:
    expected = checksum_file.read_text(encoding="utf-8").split()[0].strip().lower()
    actual = sha256(bundle)
    if actual != expected:
        raise RuntimeError(f"SHA256 mismatch for {bundle.name}")


def install_release(bundle: Path, version: str, root: Path) -> Path:
    releases = root / "releases"
    target = releases / version
    tmp_target = releases / f".{version}.tmp"
    releases.mkdir(parents=True, exist_ok=True)
    if tmp_target.exists():
        shutil.rmtree(tmp_target)
    tmp_target.mkdir()
    with tarfile.open(bundle, "r:gz") as tar:
        tar.extractall(tmp_target, filter="data")
    if target.exists():
        shutil.rmtree(target)
    tmp_target.rename(target)
    current = root / "current"
    new_link = root / ".current.new"
    if new_link.exists() or new_link.is_symlink():
        new_link.unlink()
    new_link.symlink_to(target)
    os.replace(new_link, current)
    return target


def restart_services(service_names: Sequence[str]) -> None:
    for service_name in service_names:
        subprocess.run(["systemctl", "restart", service_name], check=True)


def current_version(root: Path) -> str:
    version_file = root / "current" / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"


def run(cfg: UpdaterConfig, dry_run: bool = False) -> str:
    release = github_latest_release(cfg.repo, include_prerelease(cfg.channel))
    version = str(release.get("tag_name") or "").removeprefix("v")
    if not version:
        raise RuntimeError("Release has no tag name")
    if version == current_version(cfg.install_root):
        return f"Already on {version}"

    bundle_url = asset_url(release, ".tar.gz")
    checksum_url = asset_url(release, ".sha256")
    if dry_run:
        return json.dumps({"version": version, "bundle": bundle_url, "checksum": checksum_url}, indent=2)

    with tempfile.TemporaryDirectory(prefix="djconnect-pi-update-") as tmp:
        bundle = Path(tmp) / "release.tar.gz"
        checksum = Path(tmp) / "release.sha256"
        download(bundle_url, bundle)
        download(checksum_url, checksum)
        verify_sha256(bundle, checksum)
        install_release(bundle, version, cfg.install_root)
    restart_services(cfg.service_names)
    return f"Installed {version}"


def config_from_file(
    config_path: Path,
    *,
    repo_override: str = "",
    channel_override: str = "",
    install_root: Path = Path("/opt/djconnect"),
    service_names: Sequence[str] = ("djconnect-api.service", "djconnect-client.service"),
) -> UpdaterConfig:
    app_cfg = load_config(config_path)
    repo = repo_override or app_cfg.update_repo
    channel = channel_override or app_cfg.update_channel
    return UpdaterConfig(repo=repo, channel=channel, install_root=install_root, service_names=service_names)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--repo", default="")
    parser.add_argument("--channel", choices=["stable", "beta"], default="")
    parser.add_argument("--install-root", type=Path, default=Path("/opt/djconnect"))
    parser.add_argument(
        "--service-name",
        action="append",
        dest="service_names",
        help="systemd service to restart after install. May be supplied more than once.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    service_names = tuple(args.service_names or ("djconnect-api.service", "djconnect-client.service"))
    cfg = config_from_file(
        args.config,
        repo_override=args.repo,
        channel_override=args.channel,
        install_root=args.install_root,
        service_names=service_names,
    )
    print(run(cfg, args.dry_run))


if __name__ == "__main__":
    main()
