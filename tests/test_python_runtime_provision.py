"""Synthetic archive/transport/filesystem seams; no root or live download."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import stat
import tarfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("python_runtime_provision", ROOT / "scripts/provision_app_python.py")
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


def archive(tmp_path, extra=None):
    path = tmp_path / "fixture.tar.gz"
    with tarfile.open(path, "w:gz") as output:
        for name, data in [("python", None), ("python/bin", None), ("python/bin/python3.14", b"synthetic-interpreter")]:
            member = tarfile.TarInfo(name)
            if data is None:
                member.type = tarfile.DIRTYPE
                member.mode = 0o755
                output.addfile(member)
            else:
                member.size = len(data)
                member.mode = 0o755
                output.addfile(member, io.BytesIO(data))
        if extra is not None:
            output.addfile(extra, io.BytesIO(b""))
    return path


@pytest.mark.parametrize("machine,libc,accepted", [
    ("aarch64", "glibc 2.41", True), ("arm64", "glibc 2.39", True),
    ("aarch64", "glibc 2.36", False), ("x86_64", "glibc 2.41", False),
    ("armv7l", "glibc 2.41", False), ("aarch64", "musl 1.2", False),
])
def test_architecture_and_actual_qt_glibc_floor(machine, libc, accepted):
    if accepted:
        runtime.check_platform(machine, libc)
    else:
        with pytest.raises(runtime.RuntimePreparationError):
            runtime.check_platform(machine, libc)


@pytest.mark.parametrize("case", ["absolute", "traversal", "duplicate", "backslash", "control", "symlink-absolute", "symlink-escape", "symlink-cycle", "hardlink", "device"])
def test_rejects_archive_before_any_extraction(tmp_path, monkeypatch, case):
    name = {"absolute": "/escape", "traversal": "python/../escape", "duplicate": "python/bin", "backslash": "python/\\escape", "control": "python/\n"}.get(case, "python/link")
    member = tarfile.TarInfo(name)
    if case.startswith("symlink"):
        member.type = tarfile.SYMTYPE
        member.linkname = {"symlink-absolute": "/escape", "symlink-escape": "../../escape", "symlink-cycle": "link"}[case]
    elif case == "hardlink":
        member.type = tarfile.LNKTYPE
        member.linkname = "python/bin/python3.14"
    elif case == "device":
        member.type = tarfile.CHRTYPE
    source = archive(tmp_path, member)
    monkeypatch.setattr(runtime, "SHA256", hashlib.sha256(source.read_bytes()).hexdigest())
    stage = tmp_path / "stage"
    stage.mkdir()
    with pytest.raises(runtime.RuntimePreparationError):
        runtime.extract_archive(source, stage)
    assert list(stage.iterdir()) == []


def test_hash_mismatch_never_extracts(tmp_path):
    source = archive(tmp_path)
    stage = tmp_path / "stage"
    stage.mkdir()
    with pytest.raises(runtime.RuntimePreparationError, match="HASH_MISMATCH"):
        runtime.extract_archive(source, stage)
    assert not list(stage.iterdir())


@pytest.mark.parametrize("limit", ["MAX_MEMBERS", "MAX_EXPANDED"])
def test_bounded_archive_budgets(tmp_path, monkeypatch, limit):
    source = archive(tmp_path)
    monkeypatch.setattr(runtime, limit, 1)
    with tarfile.open(source) as opened, pytest.raises(runtime.RuntimePreparationError):
        runtime.archive_members(opened)


def cached_fixture(tmp_path, monkeypatch):
    source = archive(tmp_path)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(runtime, "SHA256", digest)
    stage = tmp_path / "stage"
    stage.mkdir()
    entries = runtime.extract_archive(source, stage)
    root = stage / "python"
    marker = root / runtime.MARKER
    marker.write_text(json.dumps({"archive_sha256": digest, "version": runtime.VERSION, "entries": entries}))
    marker.chmod(0o444)
    # Owner checks below remain real for payload; only root-ancestor policy is a separate seam.
    monkeypatch.setattr(runtime, "trusted_directory", Mock())
    return root, marker


def test_cache_roundtrip_and_actual_content_hashes(tmp_path, monkeypatch):
    root, _ = cached_fixture(tmp_path, monkeypatch)
    runtime.verify_installed(root, uid=os.getuid())
    (root / "bin/python3.14").write_bytes(b"changed")
    with pytest.raises(runtime.RuntimePreparationError, match="CACHE_CHANGED"):
        runtime.verify_installed(root, uid=os.getuid())


@pytest.mark.parametrize("change", ["empty", "version", "archive", "escape", "duplicate", "marker-link"])
def test_cache_receipt_is_original_and_closed(tmp_path, monkeypatch, change):
    root, marker = cached_fixture(tmp_path, monkeypatch)
    value = json.loads(marker.read_text())
    marker.chmod(0o644)
    if change == "marker-link":
        other = tmp_path / "other"
        other.write_text(marker.read_text())
        marker.unlink()
        marker.symlink_to(other)
    else:
        if change == "empty": value["entries"] = []
        if change == "version": value["version"] = "3.13.5"
        if change == "archive": value["archive_sha256"] = "f" * 64
        if change == "escape": value["entries"][0]["path"] = "python/../escape"
        if change == "duplicate": value["entries"].append(value["entries"][0])
        marker.write_text(json.dumps(value))
        marker.chmod(0o444)
    with pytest.raises(runtime.RuntimePreparationError):
        runtime.verify_installed(root, uid=os.getuid())


@pytest.mark.parametrize("url", ["http://release-assets.githubusercontent.com/a", "https://other.invalid/a", "https://user:secret@release-assets.githubusercontent.com/a", "https://release-assets.githubusercontent.com:444/a", "https://release-assets.githubusercontent.com/a#fragment"])
def test_redirects_never_admit_unbound_hosts_or_credentials(url):
    with pytest.raises(runtime.RuntimePreparationError):
        runtime.AssetRedirect().redirect_request(None, None, 302, "", {}, url)


def test_root_required_before_download_or_directory_changes(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime.os, "geteuid", lambda: 1000)
    download = Mock()
    monkeypatch.setattr(runtime, "download", download)
    with pytest.raises(runtime.RuntimePreparationError, match="ROOT_REQUIRED"):
        runtime.prepare(tmp_path / "never-created")
    assert not download.called and not (tmp_path / "never-created").exists()


@pytest.mark.parametrize("uid,mode", [(1000, stat.S_IFDIR | 0o755), (0, stat.S_IFDIR | 0o777), (0, stat.S_IFLNK | 0o755)])
def test_untrusted_root_path_is_rejected(monkeypatch, uid, mode):
    monkeypatch.setattr(runtime.Path, "lstat", lambda _: SimpleNamespace(st_uid=uid, st_mode=mode))
    with pytest.raises(runtime.RuntimePreparationError):
        runtime.trusted_directory(Path("/opt/djconnect-python"))


def test_installer_hash_pin_matches_exact_helper_and_published_bundle():
    source = ROOT / "scripts/provision_app_python.py"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    installer = (ROOT / "scripts/install.sh").read_text()
    assert digest in installer
    body = installer.split("main() {", 1)[1]
    assert body.index("verify_approved_release") < body.index("provision_application_python") < body.index("stop_running_updater_early")
    assert 'cp scripts/install.sh scripts/provision_app_python.py "${dist}/scripts/"' in (ROOT / ".github/workflows/publish-release.yml").read_text()


@pytest.mark.parametrize("case", ["success", "hash", "declared-size", "stream-size", "deadline"])
def test_download_is_single_bounded_anonymous_request(tmp_path, monkeypatch, case):
    payload = b"synthetic-provider-bytes"
    monkeypatch.setattr(runtime, "SHA256", hashlib.sha256(payload).hexdigest())
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.headers = {"Content-Length": str(len(payload))}
    response.read.side_effect = [payload, b""]
    if case == "hash": monkeypatch.setattr(runtime, "SHA256", "f" * 64)
    if case == "declared-size": response.headers = {"Content-Length": str(runtime.MAX_ARCHIVE + 1)}
    if case == "stream-size":
        monkeypatch.setattr(runtime, "MAX_ARCHIVE", 1)
        response.headers = {}
    if case == "deadline":
        monkeypatch.setattr(runtime.time, "monotonic", Mock(side_effect=[0, 181]))
    opener = Mock()
    opener.open.return_value = response
    factory = Mock(return_value=opener)
    monkeypatch.setattr(runtime, "build_opener", factory)
    if case == "success":
        runtime.download(tmp_path / "download")
        assert (tmp_path / "download").read_bytes() == payload
    else:
        with pytest.raises(runtime.RuntimePreparationError):
            runtime.download(tmp_path / "download")
    assert factory.call_count == 1 and opener.open.call_count == 1
    request = opener.open.call_args.args[0]
    assert request.full_url == runtime.URL
    assert request.get_header("Authorization") is None and request.get_header("Cookie") is None
    assert factory.call_args.args[0].proxies == {}
