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

PIP_CACHE_DIR = Path("/var/cache/djconnect-pip")
UPGRADE_PIP_ENV = "DJCONNECT_UPGRADE_PIP"


@dataclass
class UpdaterConfig:
    repo: str
    channel: str = "stable"
    install_root: Path = Path("/opt/djconnect")
    service_names: Sequence[str] = ("djconnect-api.service", "djconnect-client.service")
    stop_service_names: Sequence[str] = (
        "djconnect-client.service",
        "djconnect-api.service",
        "djconnect-maintenance.service",
        "djconnect-watchdog.service",
    )
    keep_releases: int = 2


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


def public_latest_release(repo: str) -> dict:
    url = f"https://github.com/{repo}/releases/latest/download/djconnect-pi-latest.json"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    data = response.json()
    version = str(data.get("version") or data.get("tag_name") or "").removeprefix("v")
    if not version:
        raise RuntimeError("Latest release manifest has no version")
    bundle_url = str(data.get("bundle") or "").strip()
    checksum_url = str(data.get("checksum") or "").strip()
    if not bundle_url or not checksum_url:
        tag = f"v{version}"
        bundle_url = f"https://github.com/{repo}/releases/download/{tag}/djconnect-pi-{version}.tar.gz"
        checksum_url = f"https://github.com/{repo}/releases/download/{tag}/djconnect-pi-{version}.sha256"
    return {
        "tag_name": f"v{version}",
        "draft": False,
        "prerelease": bool(data.get("prerelease")),
        "assets": [
            {"name": f"djconnect-pi-{version}.tar.gz", "browser_download_url": bundle_url},
            {"name": f"djconnect-pi-{version}.sha256", "browser_download_url": checksum_url},
        ],
    }


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


def _safe_members_without_bundle_root(tar: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = tar.getmembers()
    if not members:
        raise RuntimeError("Release bundle is empty")

    first_parts = [Path(member.name).parts[0] for member in members if Path(member.name).parts]
    if not first_parts:
        raise RuntimeError("Release bundle contains no files")
    strip_root = first_parts[0] if all(part == first_parts[0] for part in first_parts) else ""

    stripped_members: list[tarfile.TarInfo] = []
    for member in members:
        parts = Path(member.name).parts
        if strip_root and parts and parts[0] == strip_root:
            parts = parts[1:]
        if not parts:
            continue
        member.name = str(Path(*parts))
        stripped_members.append(member)
    return stripped_members


def unpack_release(bundle: Path, version: str, root: Path) -> Path:
    releases = root / "releases"
    target = releases / version
    tmp_target = releases / f".{version}.tmp"
    releases.mkdir(parents=True, exist_ok=True)
    if tmp_target.exists():
        shutil.rmtree(tmp_target)
    tmp_target.mkdir()
    with tarfile.open(bundle, "r:gz") as tar:
        tar.extractall(tmp_target, members=_safe_members_without_bundle_root(tar), filter="data")
    if target.exists():
        shutil.rmtree(target)
    tmp_target.rename(target)
    return target


def wheel_for_release(release_dir: Path, version: str) -> Path:
    wheels_dir = release_dir / "wheels"
    matches = sorted(wheels_dir.glob(f"djconnect_pi-{version}-*.whl"))
    if not matches:
        raise RuntimeError(f"DJConnect Pi wheel not found in release bundle: {wheels_dir}")
    return matches[0]


def pip_environment(cache_dir: Path = PIP_CACHE_DIR) -> dict[str, str]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    pip_tmp = cache_dir / "tmp"
    pip_tmp.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PIP_CACHE_DIR"] = str(cache_dir)
    env["TMPDIR"] = str(pip_tmp)
    return env


def _mark_step_done(state_dir: Path, name: str) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / name).write_text("ok\n", encoding="utf-8")


def _step_done(state_dir: Path, name: str) -> bool:
    return (state_dir / name).exists()


def _run_once(state_dir: Path, name: str, command: list[str], env: dict[str, str] | None = None) -> None:
    if _step_done(state_dir, name):
        return
    kwargs = {"check": True}
    if env is not None:
        kwargs["env"] = env
    subprocess.run(command, **kwargs)
    _mark_step_done(state_dir, name)


def install_python_dependencies(release_dir: Path, version: str) -> None:
    wheel_path = wheel_for_release(release_dir, version)
    venv_dir = release_dir / ".venv"
    bin_link = release_dir / "bin"
    if bin_link.exists() or bin_link.is_symlink():
        if bin_link.is_dir() and not bin_link.is_symlink():
            shutil.rmtree(bin_link)
        else:
            bin_link.unlink()

    state_dir = release_dir / ".install-state"
    pip_env = pip_environment()
    if not _step_done(state_dir, "venv_created"):
        if venv_dir.exists():
            shutil.rmtree(venv_dir)
        subprocess.run(["python3", "-m", "venv", str(venv_dir)], check=True)
        _mark_step_done(state_dir, "venv_created")

    python = venv_dir / "bin" / "python"
    if os.environ.get(UPGRADE_PIP_ENV) == "1":
        _run_once(state_dir, "pip_upgraded", [str(python), "-m", "pip", "install", "--upgrade", "pip"], env=pip_env)
    else:
        _run_once(state_dir, "pip_checked", [str(python), "-m", "pip", "--version"], env=pip_env)
    _run_once(
        state_dir,
        "build_tools_installed",
        [str(python), "-m", "pip", "install", "--upgrade", "setuptools", "wheel"],
        env=pip_env,
    )
    for package_name, requirement in (
        ("pyside6_installed", "PySide6>=6.7"),
        ("requests_installed", "requests>=2.31"),
        ("zeroconf_installed", "zeroconf>=0.132"),
    ):
        _run_once(
            state_dir,
            package_name,
            [str(python), "-m", "pip", "install", "--upgrade", "--prefer-binary", requirement],
            env=pip_env,
        )
    _run_once(state_dir, "wheel_installed", [str(python), "-m", "pip", "install", "--prefer-binary", str(wheel_path)], env=pip_env)
    bin_link.symlink_to(".venv/bin")
    validate_release_entrypoints(release_dir)


def validate_release_entrypoints(release_dir: Path) -> None:
    required = (
        "djconnect-pi-client",
        "djconnect-pi-api",
        "djconnect-pi-updater",
        "djconnect-pi-maintenance",
    )
    missing = [name for name in required if not os.access(release_dir / "bin" / name, os.X_OK)]
    if missing:
        raise RuntimeError(f"Release is missing executable entrypoint(s): {', '.join(missing)}")


def activate_release(release_dir: Path, root: Path) -> None:
    current = root / "current"
    new_link = root / ".current.new"
    if new_link.exists() or new_link.is_symlink():
        new_link.unlink()
    new_link.symlink_to(release_dir)
    os.replace(new_link, current)


def install_release(bundle: Path, version: str, root: Path) -> Path:
    target = unpack_release(bundle, version, root)
    install_python_dependencies(target, version)
    activate_release(target, root)
    return target


def cleanup_old_releases(root: Path, keep: int = 2) -> list[Path]:
    releases = root / "releases"
    if not releases.exists():
        return []
    current = (root / "current").resolve() if (root / "current").exists() else None
    candidates = [
        path
        for path in releases.iterdir()
        if path.is_dir() and not path.name.startswith(".") and path.resolve() != current
    ]
    keep_previous = max(0, keep - 1)
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    removed: list[Path] = []
    for path in candidates[keep_previous:]:
        shutil.rmtree(path)
        removed.append(path)
    for path in releases.glob(".*.tmp"):
        if path.is_dir():
            shutil.rmtree(path)
            removed.append(path)
    return removed


def restart_services(service_names: Sequence[str]) -> None:
    for service_name in service_names:
        subprocess.run(["systemctl", "restart", service_name], check=True)


def stop_services(service_names: Sequence[str]) -> None:
    for service_name in service_names:
        subprocess.run(["systemctl", "stop", service_name], check=False)


def current_version(root: Path) -> str:
    version_file = root / "current" / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"


def run(cfg: UpdaterConfig, dry_run: bool = False) -> str:
    release = (
        github_latest_release(cfg.repo, include_prerelease=True)
        if include_prerelease(cfg.channel)
        else public_latest_release(cfg.repo)
    )
    version = str(release.get("tag_name") or "").removeprefix("v")
    if not version:
        raise RuntimeError("Release has no tag name")
    if version == current_version(cfg.install_root):
        return f"Already on {version}"

    bundle_url = asset_url(release, ".tar.gz")
    checksum_url = asset_url(release, ".sha256")
    if dry_run:
        return json.dumps({"version": version, "bundle": bundle_url, "checksum": checksum_url}, indent=2)

    stop_services(cfg.stop_service_names)
    with tempfile.TemporaryDirectory(prefix="djconnect-pi-update-") as tmp:
        bundle = Path(tmp) / "release.tar.gz"
        checksum = Path(tmp) / "release.sha256"
        download(bundle_url, bundle)
        download(checksum_url, checksum)
        verify_sha256(bundle, checksum)
        install_release(bundle, version, cfg.install_root)
    cleanup_old_releases(cfg.install_root, cfg.keep_releases)
    restart_services(cfg.service_names)
    return f"Installed {version}"


def config_from_file(
    config_path: Path,
    *,
    repo_override: str = "",
    channel_override: str = "",
    install_root: Path = Path("/opt/djconnect"),
    service_names: Sequence[str] = ("djconnect-api.service", "djconnect-client.service"),
    stop_service_names: Sequence[str] = (
        "djconnect-client.service",
        "djconnect-api.service",
        "djconnect-maintenance.service",
        "djconnect-watchdog.service",
    ),
    keep_releases: int = 2,
) -> UpdaterConfig:
    app_cfg = load_config(config_path)
    repo = repo_override or app_cfg.update_repo
    channel = channel_override or app_cfg.update_channel
    return UpdaterConfig(
        repo=repo,
        channel=channel,
        install_root=install_root,
        service_names=service_names,
        stop_service_names=stop_service_names,
        keep_releases=keep_releases,
    )


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
    parser.add_argument(
        "--stop-service-name",
        action="append",
        dest="stop_service_names",
        help="systemd service to stop before installing a detected update. May be supplied more than once.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-releases", type=int, default=2)
    args = parser.parse_args()
    service_names = tuple(args.service_names or ("djconnect-api.service", "djconnect-client.service"))
    stop_service_names = tuple(
        args.stop_service_names
        or (
            "djconnect-client.service",
            "djconnect-api.service",
            "djconnect-maintenance.service",
            "djconnect-watchdog.service",
        )
    )
    cfg = config_from_file(
        args.config,
        repo_override=args.repo,
        channel_override=args.channel,
        install_root=args.install_root,
        service_names=service_names,
        stop_service_names=stop_service_names,
        keep_releases=max(1, args.keep_releases),
    )
    print(run(cfg, args.dry_run))


if __name__ == "__main__":
    main()
