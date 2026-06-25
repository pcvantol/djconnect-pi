from __future__ import annotations

import subprocess
from importlib.resources import files

from djconnect_pi import update_ui


def test_update_ui_reads_versions_from_status_file(tmp_path) -> None:
    status_file = tmp_path / "status.json"
    status_file.write_text(
        '{"current_version":"3.1.85","target_version":"3.1.87","progress":25}',
        encoding="utf-8",
    )

    backend = update_ui.UpdateUiBackend(status_file=status_file, local_url="")

    assert backend.currentVersion == "3.1.85"
    assert backend.targetVersion == "3.1.87"
    assert backend.progress == 25


def test_update_ui_uses_configured_local_url_for_remote_access() -> None:
    backend = update_ui.UpdateUiBackend(
        status_file=update_ui.Path("/tmp/does-not-exist"),
        local_url="http://192.168.1.115:18080",
    )

    assert backend.deviceAddress == "192.168.1.115"
    assert backend.sshCommand == "ssh pi@192.168.1.115"


def test_update_progress_uses_app_banner() -> None:
    update_qml = files("djconnect_pi.qml").joinpath("UpdateProgress.qml").read_text(encoding="utf-8")

    assert "component AppBanner" in update_qml
    assert "AppBanner {}" in update_qml
    assert 'GradientStop { position: 0.72; color: "#37145a" }' in update_qml
    assert 'text: "DJConnect"' in update_qml
    assert "Layout.preferredWidth: 128" not in update_qml


def test_update_ui_wakes_display_with_xset(monkeypatch) -> None:
    commands: list[list[str]] = []

    def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(update_ui.subprocess, "run", fake_run)

    update_ui.wake_display()

    assert ["xset", "dpms", "force", "on"] in commands
    assert ["xset", "s", "reset"] in commands
