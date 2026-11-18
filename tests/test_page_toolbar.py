from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("width", [720, 1200])
def test_actual_page_toolbar_geometry_click_and_popup_withdrawal(width):
    probe = Path(__file__).parent / "probes/page_toolbar_readback.py"
    result = subprocess.run(
        [sys.executable, str(probe), str(width)], capture_output=True, text=True, check=False,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen", "QT_QUICK_BACKEND": "software"}, timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS:" in result.stdout
