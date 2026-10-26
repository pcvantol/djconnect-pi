"""Hash-pinned, side-by-side application Python; never replaces OS Python.

Bootstrap-compatible with OS Python 3.11+. The installed application uses3.14.9.
Only the reviewed installer invokes main as root; there are no caller-selected
URLs, hashes, destinations, commands, or environment overrides.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

VERSION = "3.14.9"
SHA256 = "6f77731d85a14ed848dd4041478cd3ed511523caa3d896b84b436a7edf13cf62"
URL = "https://github.com/astral-sh/python-build-standalone/releases/download/20261021/cpython-3.14.9%2B20261021-aarch64-unknown-linux-gnu-install_only_stripped.tar.gz"
BASE = Path("/opt/djconnect-python")
NAME = "cpython-" + VERSION
MARKER = ".djconnect-runtime.json"
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_EXPANDED = 256 * 1024 * 1024
MAX_MEMBERS = 10000


class RuntimePreparationError(RuntimeError):
    pass


def require(value, code):
    if not value:
        raise RuntimePreparationError(code)


def check_platform(machine, libc):
    require(machine in {"aarch64", "arm64"}, "PYTHON_RUNTIME_ARCH_UNSUPPORTED")
    match = re.fullmatch(r"glibc (\d+)\.(\d+)", libc)
    require(match and tuple(map(int, match.groups())) >= (2, 39), "QT_RUNTIME_GLIBC_UNSUPPORTED")


def trusted_directory(path, uid=0):
    for parent in reversed((path, *path.parents)):
        info = parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == uid
                and not info.st_mode & 0o022, "PYTHON_RUNTIME_DIRECTORY_UNTRUSTED")


class AssetRedirect(HTTPRedirectHandler):
    max_redirections = 3

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        require(parsed.scheme == "https" and parsed.hostname in {
            "github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"
        } and parsed.username is None and parsed.password is None
                and parsed.port in {None, 443} and not parsed.fragment,
                "PYTHON_RUNTIME_REDIRECT_REJECTED")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(destination):
    opener = build_opener(ProxyHandler({}), AssetRedirect())
    request = Request(URL, headers={"User-Agent": "DJConnect-Python-Runtime"})
    digest = hashlib.sha256()
    total = 0
    deadline = time.monotonic() + 180
    with opener.open(request, timeout=30) as response, destination.open("xb") as output:
        length = response.headers.get("Content-Length")
        require(length is None or (length.isascii() and length.isdecimal()
                and len(length) < 20 and int(length) <= MAX_ARCHIVE), "PYTHON_RUNTIME_DOWNLOAD_TOO_LARGE")
        while True:
            require(time.monotonic() <= deadline, "PYTHON_RUNTIME_DOWNLOAD_TIMEOUT")
            chunk = response.read(65536)
            if not chunk:
                break
            total += len(chunk)
            require(total <= MAX_ARCHIVE, "PYTHON_RUNTIME_DOWNLOAD_TOO_LARGE")
            digest.update(chunk)
            output.write(chunk)
        output.flush()
        os.fsync(output.fileno())
    require(digest.hexdigest() == SHA256, "PYTHON_RUNTIME_HASH_MISMATCH")


def archive_members(archive):
    result = {}
    expanded = 0
    for member in archive:
        path = PurePosixPath(member.name)
        key = path.as_posix()
        require(path.parts and path.parts[0] == "python" and not path.is_absolute()
                and ".." not in path.parts and "\\" not in member.name
                and all(ord(c) >= 32 for c in member.name) and len(member.name.encode()) <= 4096
                and (member.name == key or (member.isdir() and member.name == key + "/"))
                and key not in result and member.size >= 0 and (member.isfile() or member.isdir() or member.issym()),
                "PYTHON_RUNTIME_ARCHIVE_REJECTED")
        expanded += member.size
        result[key] = member
        require(expanded <= MAX_EXPANDED and len(result) <= MAX_MEMBERS,
                "PYTHON_RUNTIME_ARCHIVE_TOO_LARGE")
    for key in result:
        todo = list(PurePosixPath(key).parts)
        stack = []
        visited = set()
        while todo:
            part = todo.pop(0)
            if part in {"", "."}:
                continue
            if part == "..":
                require(len(stack) > 1, "PYTHON_RUNTIME_LINK_REJECTED")
                stack.pop()
                continue
            stack.append(part)
            name = "/".join(stack)
            member = result.get(name)
            if member and member.issym():
                require(name not in visited and len(visited) < 64
                        and not PurePosixPath(member.linkname).is_absolute()
                        and "\\" not in member.linkname and len(member.linkname.encode()) <= 4096
                        and all(ord(c) >= 32 for c in member.linkname),
                        "PYTHON_RUNTIME_LINK_REJECTED")
                visited.add(name)
                stack.pop()
                todo = list(PurePosixPath(member.linkname).parts) + todo
        require("/".join(stack) in result and stack[0] == "python", "PYTHON_RUNTIME_LINK_REJECTED")
        for parent in PurePosixPath(key).parents:
            require(parent.as_posix() not in result or not result[parent.as_posix()].issym(),
                    "PYTHON_RUNTIME_LINK_PARENT_REJECTED")
    return result


def extract_archive(source, stage):
    require(source.stat().st_size <= MAX_ARCHIVE, "PYTHON_RUNTIME_DOWNLOAD_TOO_LARGE")
    with source.open("rb") as stream:
        require(hashlib.file_digest(stream, "sha256").hexdigest() == SHA256,
                "PYTHON_RUNTIME_HASH_MISMATCH")
    entries = []
    with tarfile.open(source, "r:gz") as archive:
        members = archive_members(archive)
        for key, member in members.items():
            if member.issym():
                continue
            target = stage / key
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            if member.isdir():
                target.mkdir(exist_ok=True, mode=0o755)
                target.chmod(0o755)
                entries.append({"path": key, "kind": "dir"})
            else:
                digest = hashlib.sha256()
                with archive.extractfile(member) as input_file, target.open("xb") as output:
                    for chunk in iter(lambda: input_file.read(65536), b""):
                        output.write(chunk)
                        digest.update(chunk)
                    output.flush()
                    os.fchmod(output.fileno(), member.mode & 0o755)
                    os.fsync(output.fileno())
                entries.append({"path": key, "kind": "file", "sha256": digest.hexdigest()})
        for key, member in members.items():
            if member.issym():
                target = stage / key
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
                target.symlink_to(member.linkname)
                entries.append({"path": key, "kind": "link", "target": member.linkname})
    require((stage / "python/bin/python3.14").is_file(), "PYTHON_RUNTIME_BINARY_MISSING")
    return entries


def verify_installed(destination, uid=0):
    trusted_directory(destination, uid)
    marker = destination / MARKER
    info = marker.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == uid and not info.st_mode & 0o022
            and info.st_size <= 2 * 1024 * 1024, "PYTHON_RUNTIME_RECEIPT_INVALID")
    receipt = json.loads(marker.read_text())
    require(isinstance(receipt, dict) and set(receipt) == {"archive_sha256", "version", "entries"}
            and receipt.get("archive_sha256") == SHA256 and receipt.get("version") == VERSION
            and isinstance(receipt.get("entries"), list) and 1 <= len(receipt["entries"]) <= MAX_MEMBERS,
            "PYTHON_RUNTIME_RECEIPT_INVALID")
    seen = set()
    for entry in receipt["entries"]:
        require(isinstance(entry, dict) and isinstance(entry.get("path"), str), "PYTHON_RUNTIME_RECEIPT_INVALID")
        kind = entry.get("kind")
        fields = {"path", "kind"} | ({"sha256"} if kind == "file" else {"target"} if kind == "link" else set())
        require(kind in {"file", "dir", "link"} and set(entry) == fields,
                "PYTHON_RUNTIME_RECEIPT_INVALID")
        path = PurePosixPath(entry["path"])
        require(path.parts and path.parts[0] == "python" and ".." not in path.parts and path.as_posix() == entry["path"]
                and path.as_posix() not in seen, "PYTHON_RUNTIME_RECEIPT_INVALID")
        seen.add(path.as_posix())
        target = destination.joinpath(*path.parts[1:])
        trusted_directory(target.parent, uid)
        node = target.lstat()
        require(node.st_uid == uid, "PYTHON_RUNTIME_CACHE_CHANGED")
        if entry["kind"] == "link":
            require(stat.S_ISLNK(node.st_mode) and os.readlink(target) == entry["target"],
                    "PYTHON_RUNTIME_CACHE_CHANGED")
        else:
            require(not node.st_mode & 0o022, "PYTHON_RUNTIME_CACHE_CHANGED")
            if entry["kind"] == "dir":
                require(stat.S_ISDIR(node.st_mode), "PYTHON_RUNTIME_CACHE_CHANGED")
            else:
                require(entry["kind"] == "file" and stat.S_ISREG(node.st_mode),
                        "PYTHON_RUNTIME_CACHE_CHANGED")
                with target.open("rb") as stream:
                    require(hashlib.file_digest(stream, "sha256").hexdigest() == entry["sha256"],
                            "PYTHON_RUNTIME_CACHE_CHANGED")

    require("python/bin/python3.14" in seen, "PYTHON_RUNTIME_RECEIPT_INVALID")


def fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def prepare(base=BASE):
    require(os.geteuid() == 0, "PYTHON_RUNTIME_ROOT_REQUIRED")
    check_platform(platform.machine(), os.confstr("CS_GNU_LIBC_VERSION"))
    trusted_directory(base.parent)
    base.mkdir(mode=0o755, exist_ok=True)
    trusted_directory(base)
    descriptor = os.open(base / ".prepare.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "a+b") as lock:
        info = os.fstat(lock.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022,
                "PYTHON_RUNTIME_LOCK_UNTRUSTED")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimePreparationError("PYTHON_RUNTIME_BUSY") from None
        destination = base / NAME
        if destination.exists() or destination.is_symlink():
            verify_installed(destination)
            return
        require(shutil.disk_usage(base).free >= MAX_ARCHIVE + MAX_EXPANDED + 67108864,
                "PYTHON_RUNTIME_SPACE_REQUIRED")
        stage = Path(tempfile.mkdtemp(prefix=".python3149-", dir=base))
        try:
            source = stage / "runtime.tar.gz"
            download(source)
            entries = extract_archive(source, stage)
            binary = stage / "python/bin/python3.14"
            command = "import sys,sysconfig;assert sys.version_info[:3]==(3,14,9);assert not sysconfig.get_config_var('Py_GIL_DISABLED')"
            result = subprocess.run([str(binary), "-I", "-B", "-c", command],
                                    env={"PATH": "/usr/bin:/bin"}, capture_output=True,
                                    timeout=30, check=False)
            require(result.returncode == 0, "PYTHON_RUNTIME_PROBE_FAILED")
            marker = stage / "python" / MARKER
            with marker.open("x") as output:
                json.dump({"version": VERSION, "archive_sha256": SHA256, "entries": entries}, output)
                output.flush()
                os.fchmod(output.fileno(), 0o444)
                os.fsync(output.fileno())
            for directory in sorted((p for p in (stage / "python").rglob("*")
                                     if p.is_dir() and not p.is_symlink()),
                                    key=lambda p: len(p.parts), reverse=True):
                fsync_directory(directory)
            fsync_directory(stage / "python")
            os.rename(stage / "python", destination)
            fsync_directory(base)
        finally:
            shutil.rmtree(stage)


def main():
    try:
        prepare()
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError, RuntimePreparationError,
            subprocess.TimeoutExpired) as error:
        code = str(error) if isinstance(error, RuntimePreparationError) else "PYTHON_RUNTIME_PREPARATION_FAILED"
        raise SystemExit(code) from None


if __name__ == "__main__":
    main()
