from __future__ import annotations

import logging
from pathlib import Path

import pytest

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


@pytest.mark.parametrize("prefix", ["", "https://fixture.invalid"])
@pytest.mark.parametrize("media_route", ["forecast/art", "media/image"])
def test_managed_media_path_is_redacted_in_third_party_debug_logs(tmp_path, prefix, media_route):
    root = logging.getLogger()
    previous_handlers, previous_level = list(root.handlers), root.level
    route = prefix + "/api/djconnect/v1/session/" + media_route + "/s123/" + "A" * 32
    assert not any(word in route.lower() for word in ("token", "bearer", "secret"))
    log_file = tmp_path / "debug.log"
    try:
        setup_logging(str(log_file), "DEBUG")
        logger = logging.getLogger("urllib3.connectionpool")
        logger.debug('%s://%s:%s "%s %s %s" %s %s', "http", "fixture.invalid", 8123,
                     "GET", route, "HTTP/1.1", 200, 179)
        logger.debug('"GET /api/djconnect/v1/session/active HTTP/1.1" 200')
        text = log_file.read_text()
        assert "A" * 32 not in text and "s123" not in text
        assert "/session/" + media_route + "/" not in text
        assert "[redacted sensitive log message]" in text
        assert "/session/active" in text  # Ordinary diagnostics remain useful.
    finally:
        for handler in root.handlers:
            handler.close()
        root.handlers[:] = previous_handlers
        root.setLevel(previous_level)
