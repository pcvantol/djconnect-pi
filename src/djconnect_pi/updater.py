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
import time

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
    update_ui_service_name: str = "djconnect-update-ui.service"
    keep_releases: int = 2
    status_file: Path = Path("/opt/djconnect/config/updater-status.json")


class UpdateStatus:
    def __init__(self, path: Path, *, current_version: str = "", target_version: str = "") -> None:
        self.path = path
        self.current_version = current_version
        self.target_version = target_version
        self.logs: list[str] = []

    def write(self, state: str, message: str, progress: int, *, title: str = "Update bezig") -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "state": state,
            "title": title,
            "message": message,
            "progress": max(0, min(100, int(progress))),
            "current_version": self.current_version,
            "target_version": self.target_version,
            "logs": self.logs[-80:],
            "updated_at": time.time(),
        }
        tmp = self.path.with_name(f".{self.path.name}.tmp")
        tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def log(self, line: str, state: str, message: str, progress: int) -> None:
        clean = line.rstrip()
        if clean:
            self.logs.append(clean)
        print(line, end="" if line.endswith("\n") else "\n", flush=True)
        self.write(state, message, progress)


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
    if target.exists() and (target / "VERSION").exists() and (target / "wheels").exists():
        return target
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


def _run_once(
    state_dir: Path,
    name: str,
    command: list[str],
    env: dict[str, str] | None = None,
    status: UpdateStatus | None = None,
    message: str = "",
    progress: int = 0,
) -> None:
    if _step_done(state_dir, name):
        return
    if status is None:
        kwargs = {"check": True}
        if env is not None:
            kwargs["env"] = env
        subprocess.run(command, **kwargs)
    else:
        status.write("installing", message, progress)
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
        assert process.stdout is not None
        for line in process.stdout:
            status.log(line, "installing", message, progress)
        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, command)
    _mark_step_done(state_dir, name)


def install_python_dependencies(release_dir: Path, version: str, status: UpdateStatus | None = None) -> None:
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
        if status is not None:
            status.write("installing", "Python omgeving voorbereiden", 38)
        if venv_dir.exists():
            shutil.rmtree(venv_dir)
        subprocess.run(["python3", "-m", "venv", str(venv_dir)], check=True)
        _mark_step_done(state_dir, "venv_created")

    python = venv_dir / "bin" / "python"
    if os.environ.get(UPGRADE_PIP_ENV) == "1":
        _run_once(state_dir, "pip_upgraded", [str(python), "-m", "pip", "install", "--upgrade", "pip"], env=pip_env, status=status, message="pip bijwerken", progress=42)
    else:
        _run_once(state_dir, "pip_checked", [str(python), "-m", "pip", "--version"], env=pip_env, status=status, message="pip controleren", progress=42)
    _run_once(
        state_dir,
        "build_tools_installed",
        [str(python), "-m", "pip", "install", "--upgrade", "setuptools", "wheel"],
        env=pip_env,
        status=status,
        message="Build tools installeren",
        progress=48,
    )
    for package_name, message, requirement, progress in (
        ("shiboken6_installed", "shiboken6 installeren", "shiboken6>=6.7", 55),
        ("pyside6_essentials_installed", "PySide6 Essentials installeren", "PySide6_Essentials>=6.7", 64),
        ("pyside6_addons_installed", "PySide6 Addons installeren", "PySide6_Addons>=6.7", 74),
        ("pyside6_installed", "PySide6 afronden", "PySide6>=6.7", 82),
        ("requests_installed", "Requests installeren", "requests>=2.31", 88),
        ("zeroconf_installed", "Zeroconf installeren", "zeroconf>=0.132", 92),
    ):
        _run_once(
            state_dir,
            package_name,
            [str(python), "-m", "pip", "install", "--upgrade", "--only-binary=:all:", requirement],
            env=pip_env,
            status=status,
            message=message,
            progress=progress,
        )
    _run_once(state_dir, "wheel_installed", [str(python), "-m", "pip", "install", "--only-binary=:all:", str(wheel_path)], env=pip_env, status=status, message="DJConnect app installeren", progress=96)
    bin_link.symlink_to(".venv/bin")
    validate_release_entrypoints(release_dir)


def validate_release_entrypoints(release_dir: Path) -> None:
    required = (
        "djconnect-pi-client",
        "djconnect-pi-update-ui",
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


def install_release(bundle: Path, version: str, root: Path, status: UpdateStatus | None = None) -> Path:
    target = unpack_release(bundle, version, root)
    if status is not None:
        status.write("installing", f"Release {version} installeren", 34)
    install_python_dependencies(target, version, status=status)
    if status is not None:
        status.write("activating", f"Release {version} activeren", 98)
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


def start_service(service_name: str) -> None:
    subprocess.run(["systemctl", "start", service_name], check=False)


def stop_service(service_name: str) -> None:
    subprocess.run(["systemctl", "stop", service_name], check=False)


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
    installed_version = current_version(cfg.install_root)
    if version == installed_version:
        return f"Already on {version}"

    bundle_url = asset_url(release, ".tar.gz")
    checksum_url = asset_url(release, ".sha256")
    if dry_run:
        return json.dumps({"version": version, "bundle": bundle_url, "checksum": checksum_url}, indent=2)

    status_file = cfg.status_file
    if status_file == Path("/opt/djconnect/config/updater-status.json") and cfg.install_root != Path("/opt/djconnect"):
        status_file = cfg.install_root / "config" / "updater-status.json"
    status = UpdateStatus(status_file, current_version=installed_version, target_version=version)
    status.write("checking", f"Nieuwe versie {version} gevonden", 12)
    stop_services(cfg.stop_service_names)
    start_service(cfg.update_ui_service_name)
    try:
        with tempfile.TemporaryDirectory(prefix="djconnect-pi-update-") as tmp:
            bundle = Path(tmp) / "release.tar.gz"
            checksum = Path(tmp) / "release.sha256"
            status.write("downloading", f"Release {version} downloaden", 22)
            download(bundle_url, bundle)
            status.write("downloading", "Checksum downloaden", 28)
            download(checksum_url, checksum)
            status.write("verifying", "Release controleren", 32)
            verify_sha256(bundle, checksum)
            install_release(bundle, version, cfg.install_root, status=status)
        status.write("cleanup", "Oude releases opruimen", 99)
        cleanup_old_releases(cfg.install_root, cfg.keep_releases)
        status.write("restarting", "DJConnect herstarten", 100)
    except Exception as exc:
        status.write("failed", f"Update mislukt: {exc}", 100)
        raise
    stop_service(cfg.update_ui_service_name)
    restart_services(cfg.service_names)
    status.write("complete", f"Versie {version} geinstalleerd", 100)
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
    update_ui_service_name: str = "djconnect-update-ui.service",
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
        update_ui_service_name=update_ui_service_name,
        keep_releases=keep_releases,
        status_file=Path(app_cfg.updater_status_file),
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
