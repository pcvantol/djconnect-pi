from __future__ import annotations

from logging.handlers import RotatingFileHandler
from pathlib import Path
import logging
import sys

SENSITIVE_MARKERS = ("token", "authorization", "bearer", "password", "secret")


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if any(marker in message.lower() for marker in SENSITIVE_MARKERS):
            record.msg = "[redacted sensitive log message]"
            record.args = ()
        return True


def setup_logging(log_file: str, level: str = "INFO") -> Path:
    path = Path(log_file).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    redactor = RedactingFilter()

    file_handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.addFilter(redactor)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(redactor)
    root.addHandler(stream_handler)

    return path
