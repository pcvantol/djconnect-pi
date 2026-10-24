"""Actual QML admission/withdrawal, isolated from the shared Qt test process."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("width", [720, 1200])
def test_native_visit_is_pi10_only_and_context_bound(width):
    probe = Path(__file__).parent / "probes/vibescape_readback.py"
    result = subprocess.run(
        [sys.executable, str(probe), str(width)],
        capture_output=True,
        text=True,
        timeout=35,
        check=False,
        env={
            **os.environ,
            "QT_QPA_PLATFORM": "offscreen",
            "QT_QUICK_BACKEND": "software",
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS:" in result.stdout
