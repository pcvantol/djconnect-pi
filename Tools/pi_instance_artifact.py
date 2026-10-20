"""Inspect approved profile archives before any target-side staging."""
from __future__ import annotations

import hashlib
import io
import tarfile
from dataclasses import dataclass
from pathlib import PurePosixPath

from Tools.pi_instance_contract import VERSION, BindingError, require


@dataclass(frozen=True)
class Package:
    prefix: str
    wheel_name: str
    wheel_sha256: str


def inspect_artifact(raw: bytes, profile: str, source: str) -> Package:
    require(isinstance(raw, bytes) and len(raw) <= 33554432 and profile in {"pi-zero-2w-arm64", "pi5-arm64"}, "ARTIFACT_LAYOUT_INVALID")
    prefix = "djconnect-pi-"+profile+"-"+VERSION
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
            seen = set();size = 0
            for member in archive:
                path = PurePosixPath(member.name)
                require(bool(path.parts) and path.parts[0] == prefix and not path.is_absolute()
                        and ".." not in path.parts and "\\" not in member.name
                        and len(member.name.encode()) <= 4096 and all(ord(c) >= 32 for c in member.name)
                        and (member.name == path.as_posix() or (member.isdir() and member.name == path.as_posix()+"/"))
                        and path.as_posix() not in seen and (member.isfile() or member.isdir()), "ARTIFACT_LAYOUT_INVALID")
                seen.add(path.as_posix());size += member.size
                require(size <= 67108864 and len(seen) <= 4096, "ARTIFACT_EXPANSION_INVALID")
            def read(name: str, maximum: int) -> bytes:
                member = archive.getmember(prefix+"/"+name)
                require(member.isfile() and member.size <= maximum, "ARTIFACT_MEMBER_INVALID")
                return archive.extractfile(member).read(maximum+1)
            for name, expected in (("VERSION", VERSION), ("SOURCE_COMMIT", source), ("RELEASE_PROFILE", profile)):
                require(read(name, 128) == (expected+"\n").encode(), "ARTIFACT_IDENTITY_INVALID")
            installer = read("scripts/install.sh", 131072)
            require(all(flag in installer for flag in (b"--approved-artifact", b"--artifact-sha256", b"--source-sha")), "QUALIFIED_INSTALLER_REQUIRED")
            require(bool(read("requirements.lock", 131072)), "DEPENDENCY_LOCK_REQUIRED")
            wheel_name = "djconnect_pi-4.0.0rc5-py3-none-any.whl"
            wheels = [name for name in seen if name.startswith(prefix+"/wheels/") and name.endswith(".whl")]
            require(wheels == [prefix+"/wheels/"+wheel_name], "WHEEL_SET_INVALID")
            wheel = read("wheels/"+wheel_name, 8388608)
            return Package(prefix, wheel_name, hashlib.sha256(wheel).hexdigest())
    except (tarfile.TarError, OSError, KeyError, EOFError, ValueError):
        raise BindingError("ARTIFACT_LAYOUT_INVALID") from None
