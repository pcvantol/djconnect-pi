from __future__ import annotations

import logging
from pathlib import Path

from djconnect_pi.logging_config import setup_logging


def test_setup_logging_writes_to_file(tmp_path: Path) -> None:
    log_file = tmp_path / "client.log"

    setup_logging(str(log_file), "INFO")
    logging.getLogger("test").info("client started")

    assert "client started" in log_file.read_text(encoding="utf-8")


def test_setup_logging_redacts_sensitive_messages(tmp_path: Path) -> None:
    log_file = tmp_path / "client.log"

    setup_logging(str(log_file), "INFO")
    logging.getLogger("test").info("device_token=secret")
    text = log_file.read_text(encoding="utf-8")

    assert "secret" not in text
    assert "[redacted sensitive log message]" in text
