"""Actual isolated Qt delivery probes; no HA, device or provider interaction."""
import json
import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize("lifecycle", ["running", "shutdown", "destroyed"])
def test_initial_backend_reads_obey_native_owner_lifetime(lifecycle):
    # Isolate the native event dispatcher from other tests' application objects.
    # All timers are real; only their network-facing recipients are intercepted.
    code = r'''
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,sys
from PySide6.QtCore import QCoreApplication
from PySide6.QtTest import QTest
from shiboken6 import delete
from djconnect_pi.app import DJConnectBackend
app = QCoreApplication([])
with TemporaryDirectory(prefix="pi-timer-owner-") as temp:
    with patch.object(DJConnectBackend, "refresh") as refresh, patch.object(DJConnectBackend, "pollSharedSettings") as settings:
        backend = DJConnectBackend(Path(temp) / "config.json")
        pools = (backend._executor, backend._session_executor, backend._question_executor)
        mode = sys.argv[1]
        if mode == "shutdown": backend.shutdown()
        elif mode == "destroyed": delete(backend)
        QTest.qWait(450)
        result = {"refresh": refresh.call_count, "settings": settings.call_count}
        if mode != "destroyed": backend.shutdown(); delete(backend)
        for pool in pools: pool.shutdown(wait=True, cancel_futures=True)
        print(json.dumps(result))
'''
    result = subprocess.run([sys.executable, "-c", code, lifecycle], env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
                            capture_output=True, text=True, timeout=15, check=False)
    assert result.returncode == 0, result.stderr
    assert not result.stderr, result.stderr
    assert json.loads(result.stdout) == ({"refresh": 1, "settings": 1} if lifecycle == "running" else {"refresh": 0, "settings": 0})
