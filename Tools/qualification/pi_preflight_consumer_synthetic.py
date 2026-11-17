"""Exercise Pi prepare/checkout interaction with synthetic authority only.

No network, token, host SSH configuration or production endpoint is used.
The actual manifest/authority resolver is intentionally mocked; this is not a
claim that a Pi, its credentials, or a deployment has been authorized.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# The authority resolver is mocked. Fail closed if schema validation is invoked.
jsonschema = types.ModuleType("jsonschema")
class UnavailableSchema:
    def __init__(self, *args, **kwargs):
        raise AssertionError("Synthetic prepare must not invoke schema validation")
jsonschema.Draft202012Validator = UnavailableSchema
exceptions = types.ModuleType("jsonschema.exceptions")
exceptions.ValidationError = type("ValidationError", (Exception,), {})
sys.modules["jsonschema"] = jsonschema
sys.modules["jsonschema.exceptions"] = exceptions

from Tools import pi_instance_release as ordinary
from Tools import pi_wall4_recovery_release as recovery


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("expected a fresh, job-owned scratch directory")
    scratch = Path(sys.argv[1]).resolve(strict=True)
    if not scratch.is_dir() or any(scratch.iterdir()):
        raise SystemExit("synthetic scratch must be a fresh empty directory")
    source = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    if source != os.environ["GITHUB_SHA"] or os.environ["GITHUB_REPOSITORY_ID"] != "1267248532":
        raise SystemExit("consumer repository or checkout identity mismatch")
    fakehome = scratch / "fake-home"
    fakeconfig = fakehome / ".ssh" / "config"
    fakeconfig.parent.mkdir(parents=True)
    fakeconfig.write_text("# synthetic: no host or endpoint\n", encoding="utf-8")
    request = {
        "action": "deployment", "execution_mode": "execute",
        "candidate_sha": "a" * 40, "manifest_id": "release-synthetic",
        "artifact_id": "synthetic-artifact", "artifact_sha256": "b" * 64,
        "target": "rbpi-djconnect", "platform_version": "4.0",
        "release_profile": "INTERNAL_RELEASE", "deployment_instance": "wall-4inch",
        "device_profile": "pi-zero-2w-arm64", "inventory_sha256": "c" * 64,
    }
    assert set(request) == ordinary.FIELDS
    operations = [(ordinary, "readiness"), (ordinary, "deploy"), (ordinary, "smoke"),
                  (recovery, "recover"), (recovery, "smoke")]
    original_popen = subprocess.Popen
    def local_git_only(arguments, *args, **kwargs):
        if arguments != ["git", "rev-parse", "HEAD"] or kwargs.get("shell"):
            raise AssertionError("external command forbidden during synthetic prepare")
        return original_popen(["/usr/bin/git", "rev-parse", "HEAD"], *args, **kwargs)
    for index, (module, operation) in enumerate(operations, 1):
        run_id = str(100 + index)
        selected = dict(request)
        if module is ordinary and operation == "smoke":
            selected.update(action="deployment_smoke", deployment_workflow_run="321")
        if module is recovery and operation == "smoke":
            selected["recovery_workflow_run"] = "321"
        folder = scratch / f"case-{index}"
        folder.mkdir()
        envfile = folder / "synthetic-env"
        envfile.touch()
        run = {"id": int(run_id), "head_sha": source, "head_branch": "main",
               "path": module.WORKFLOWS[operation], "event": "workflow_dispatch",
               "status": "in_progress", "run_attempt": 1, "actor": {"login": "pcvantol"},
               "repository": {"full_name": "djconnect-music-dj/djconnect-pi", "id": 1267248532}}
        class FakeClient:
            def json(self, resource):
                assert resource == "repos/" + ordinary.PI + "/actions/runs/" + run_id
                return run
        authority = SimpleNamespace(binding=SimpleNamespace(inventory_row={"endpoint_config_ref": "SYNTHETIC_ENDPOINT"}),
                                    receipt=lambda: {"synthetic": True, "operation": operation})
        env = {"PATH": os.environ["PATH"], "GITHUB_ACTIONS": "true",
               "GITHUB_REPOSITORY": "djconnect-music-dj/djconnect-pi", "GITHUB_REPOSITORY_ID": "1267248532",
               "GITHUB_SHA": source, "GITHUB_RUN_ID": run_id, "GITHUB_RUN_ATTEMPT": "1",
               "RUNNER_TEMP": str(folder), "GITHUB_ENV": str(envfile),
               "GH_TOKEN": "synthetic-not-a-token", "PI_INPUTS_JSON": json.dumps(selected)}
        # Block all sockets and replace external authority resolution before entering main.
        with patch.dict(os.environ, env, clear=True), patch.object(Path, "home", return_value=fakehome), \
             patch.object(module, "GitHubRead", return_value=FakeClient()) as factory, \
             patch.object(socket, "socket", side_effect=AssertionError("network forbidden")), \
             patch.object(subprocess, "Popen", side_effect=local_git_only), \
             patch.object(os, "system", side_effect=AssertionError("shell forbidden")), \
             patch.object(sys, "argv", ["synthetic", "--operation", operation, "--prepare"]):
            try:
                subprocess.run(["curl", "https://invalid.example"], check=True)
            except AssertionError:
                pass
            else:
                raise AssertionError("synthetic prepare allowed an external command")
            try:
                socket.socket()
            except AssertionError:
                pass
            else:
                raise AssertionError("synthetic prepare allowed a socket")
            if module is ordinary:
                with patch.object(module, "resolve", return_value=authority):
                    module.main()
            else:
                with patch.object(module.authority_module, "resolve", return_value=authority), \
                     patch.object(module.component, "original_failure"), \
                     patch.object(module, "previous_failure"), patch.object(module, "latest_failure"), \
                     patch.object(module, "current_intent"):
                    module.main()
            factory.assert_called_once_with("synthetic-not-a-token")
        expected = (folder / (f"pi-qualified-instance-{run_id}-1" if module is ordinary
                              else f"pi-qualified-wall4-recovery-{run_id}-1") / "prepared.json")
        assert json.loads(expected.read_text(encoding="utf-8")) == {"synthetic": True, "operation": operation}
        assert envfile.read_text(encoding="utf-8") == (
            "PI_INSTANCE_ENDPOINT_REF=SYNTHETIC_ENDPOINT\nPI_INSTANCE_SSH_CONFIG=" + str(fakeconfig) + "\n")
    print("Five actual prepare entrypoints completed with synthetic authority, fake run metadata and network disabled.")


if __name__ == "__main__":
    main()
