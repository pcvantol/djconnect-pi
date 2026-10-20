from __future__ import annotations

import hashlib
import io
import os
import re
import subprocess
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "a"*40


def bundle(path, profile, *, source=SOURCE, version="4.0.0-rc.5", bad_member=None):
    prefix = "djconnect-pi-"+profile+"-4.0.0-rc.5"
    with tarfile.open(path, "w:gz") as archive:
        for name, value in (("VERSION", version), ("SOURCE_COMMIT", source), ("RELEASE_PROFILE", profile)):
            data = (value+"\n").encode();member = tarfile.TarInfo(prefix+"/"+name);member.size = len(data);archive.addfile(member, io.BytesIO(data))
        if bad_member:
            member = tarfile.TarInfo(bad_member)
            if "symlink" in bad_member:member.type = tarfile.SYMTYPE;member.linkname = "/etc/passwd"
            archive.addfile(member, io.BytesIO())
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(tmp_path, artifact, digest, profile, *, source=SOURCE, extra=(), existing=False):
    text = (ROOT/"scripts/install.sh").read_text()
    functions = []
    for name in ("parse_approved_input", "verify_approved_release", "version", "release_profile", "release_id", "release_asset", "state_dir"):
        match = re.search(r"(?ms)^"+name+r"\(\) \{\n.*?^\}", text);assert match
        functions.append(match.group())
    stage = tmp_path/"scratch";stage.mkdir(exist_ok=True)
    python_bin = tmp_path/"bin";python_bin.mkdir(exist_ok=True)
    (python_bin/"python3").symlink_to(os.environ.get("PYTHON_FOR_APPROVED_INSTALLER_TESTS", __import__("sys").executable))
    install_root = tmp_path/"opt";install_root.mkdir(exist_ok=True)
    (install_root/"config").mkdir();(install_root/"config/client.json").write_text('{"synthetic":true}')
    if existing:(install_root/"releases"/("4.0.0-rc.5-"+profile)).mkdir(parents=True)
    effect = tmp_path/"SERVICE_EFFECT"
    script = tmp_path/"fixture.sh"
    script.write_text('set -euo pipefail\nDJCONNECT_VERSION=4.0.0-rc.5\nDJCONNECT_RELEASE_PROFILE="'+profile+'"\nDJCONNECT_ROOT="'+str(install_root)+'"\nDJCONNECT_INSTALL_STATE="'+str(install_root/"state")+'"\nAPPROVED_ARTIFACT=""\nAPPROVED_ARTIFACT_SHA256=""\nAPPROVED_SOURCE_SHA=""\nAPPROVED_SEAL_DIR=""\n'+"\n".join(functions)+'\nparse_approved_input "$@"\nverify_approved_release\nprintf approved > "'+str(effect)+'"\n')
    args = ["bash", str(script), "--approved-artifact", str(artifact), "--artifact-sha256", digest, "--source-sha", source, *extra]
    result = subprocess.run(args, check=False, env={**os.environ, "PATH": str(python_bin)+":"+os.environ["PATH"], "TMPDIR": str(stage)}, capture_output=True, text=True)
    assert list(stage.iterdir()) == []  # Only own root-private scratch is cleaned.
    return result, effect.exists()


@pytest.mark.parametrize("profile", ["pi-zero-2w-arm64", "pi5-arm64"])
def test_exact_staged_profile_artifact_before_effects(tmp_path, profile):
    path = tmp_path/"artifact.tar.gz";digest = bundle(path, profile)
    result, effects = invoke(tmp_path, path, digest, profile)
    assert result.returncode == 0 and effects, result.stderr


@pytest.mark.parametrize("case", ["hash", "source", "version", "cross-profile", "missing-sha", "newline-sha", "extra-option", "existing-unbound", "traversal", "symlink", "normalized-duplicate"])
def test_rejection_never_reaches_service_effects(tmp_path, case):
    profile = "pi5-arm64";path = tmp_path/"artifact.tar.gz";extra = ();source = SOURCE
    values = {"source": "b"*40 if case == "source" else SOURCE, "version": "4.0.0-rc.4" if case == "version" else "4.0.0-rc.5"}
    if case == "traversal":values["bad_member"] = "../escape"
    if case == "symlink":values["bad_member"] = "djconnect-pi-pi5-arm64-4.0.0-rc.5/symlink"
    if case == "normalized-duplicate":values["bad_member"] = "djconnect-pi-pi5-arm64-4.0.0-rc.5/./SOURCE_COMMIT"
    digest = bundle(path, profile, **values)
    if case == "hash":digest = "f"*64
    if case == "cross-profile":profile = "pi-zero-2w-arm64"
    if case == "missing-sha":source = ""
    if case == "newline-sha":source += "\n"
    if case == "extra-option":extra = ("--host", "forbidden.invalid")
    result, effects = invoke(tmp_path, path, digest, profile, source=source, extra=extra, existing=case == "existing-unbound")
    assert result.returncode != 0 and not effects


def test_approved_checks_precede_both_original_service_stops():
    script = (ROOT/"scripts/install.sh").read_text();body = script.split("main() {", 1)[1]
    assert body.index("parse_approved_input") < body.index("verify_approved_release") < body.index("stop_running_updater_early") < body.index("stop_running_client_early")
    assert 'cp -- "$APPROVED_ARTIFACT" "${tmp}/release.tar.gz"' in script


def config_digest(tmp_path, value):
    root = tmp_path / "root"
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config/client.json").write_text(value)
    text = (ROOT / "scripts/install.sh").read_text()
    function = re.search(r"(?ms)^approved_config_digest\(\) \{\n.*?^\}", text).group()
    return subprocess.run(["bash", "-c", 'DJCONNECT_ROOT="$1"\n' + function + '\napproved_config_digest', "fixture", str(root)], capture_output=True, text=True, check=False)


def test_config_digest_preserves_every_field_except_release_profile(tmp_path):
    import json
    original = {"device_id": "synthetic", "token": "synthetic-token", "profile_id": "synthetic-profile", "unknown": {"nested": [1, True]}, "release_profile": "old"}
    first = config_digest(tmp_path, json.dumps(original))
    original["release_profile"] = "pi5-arm64"
    assert config_digest(tmp_path, json.dumps(original)).stdout == first.stdout
    for key in ("device_id", "token", "profile_id", "unknown"):
        changed = dict(original); changed[key] = "changed"
        assert config_digest(tmp_path, json.dumps(changed)).stdout != first.stdout
    assert first.returncode == 0 and len(first.stdout.strip()) == 64
    assert "synthetic" not in first.stdout + first.stderr


@pytest.mark.parametrize("value", ['{"duplicate":1,"duplicate":2}', '{"bad":NaN}', '[]', '{', '{"big":"' + 'x' * 2097152 + '"}'], ids=['duplicate', 'nonfinite', 'nonobject', 'malformed', 'oversize'])
def test_config_digest_invalid_fails_without_private_output(tmp_path, value):
    result = config_digest(tmp_path, value)
    assert result.returncode != 0 and result.stdout == ""
    assert "APPROVED_CONFIG_INVALID" in result.stderr
