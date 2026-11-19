from __future__ import annotations

import hashlib
import io
import tarfile

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")
from Tools import pi_instance_artifact as wire

SOURCE = "a"*40


def package(profile="pi-zero-2w-arm64", *, source=SOURCE, extra=None, version=wire.VERSION, installer=True):
    prefix = "djconnect-pi-"+profile+"-"+wire.VERSION
    values = {"VERSION": version+"\n", "SOURCE_COMMIT": source+"\n", "RELEASE_PROFILE": profile+"\n",
        "scripts/install.sh": "--approved-artifact --artifact-sha256 --source-sha" if installer else "old unqualified installer",
        "requirements.lock": "synthetic==1", "wheels/djconnect_pi-4.0.0rc6-py3-none-any.whl": "synthetic wheel bytes"}
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w:gz") as archive:
        for name, body in values.items():
            data = body.encode();member = tarfile.TarInfo(prefix+"/"+name);member.size = len(data);archive.addfile(member, io.BytesIO(data))
        if extra:
            member = tarfile.TarInfo(extra)
            if "symlink" in extra:member.type = tarfile.SYMTYPE;member.linkname = "/etc/passwd"
            archive.addfile(member, io.BytesIO())
    return raw.getvalue()


@pytest.mark.parametrize("profile", ["pi-zero-2w-arm64", "pi5-arm64"])
def test_exact_profile_archive_metadata(profile):
    value = wire.inspect_artifact(package(profile), profile, SOURCE)
    assert value.wheel_sha256 == hashlib.sha256(b"synthetic wheel bytes").hexdigest()


@pytest.mark.parametrize("case", ["source", "version", "cross-profile", "installer", "traversal", "duplicate", "symlink", "normalized"])
def test_invalid_archive_never_qualifies_for_staging(case):
    profile = "pi5-arm64";kwargs = {}
    if case == "source":kwargs["source"] = "b"*40
    if case == "version":kwargs["version"] = "4.0.0-rc.4"
    if case == "installer":kwargs["installer"] = False
    if case == "traversal":kwargs["extra"] = "../escape"
    if case == "duplicate":kwargs["extra"] = "djconnect-pi-pi5-arm64-4.0.0-rc.6/SOURCE_COMMIT"
    if case == "symlink":kwargs["extra"] = "djconnect-pi-pi5-arm64-4.0.0-rc.6/symlink"
    if case == "normalized":kwargs["extra"] = "djconnect-pi-pi5-arm64-4.0.0-rc.6/./SOURCE_COMMIT"
    raw = package(profile, **kwargs)
    if case == "cross-profile":profile = "pi-zero-2w-arm64"
    with pytest.raises(wire.BindingError):wire.inspect_artifact(raw, profile, SOURCE)
