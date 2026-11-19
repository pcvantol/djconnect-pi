from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import DEFAULT_LOG_LEVEL, normalize_log_level

SENSITIVE_MARKERS = ("token", "authorization", "bearer", "password", "secret")
# This managed URL is itself a bearer capability, including in urllib3 DEBUG logs.
SENSITIVE_PATHS = ("/api/djconnect/v1/session/forecast/art/", "/api/djconnect/v1/session/media/image/")


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if any(marker in message.lower() for marker in (*SENSITIVE_MARKERS, *SENSITIVE_PATHS)):
            record.msg = "[redacted sensitive log message]"
            record.args = ()
        return True


LOG_BACKUP_COUNT = 3


def setup_logging(log_file: str, level: str = DEFAULT_LOG_LEVEL) -> Path:
    path = Path(log_file).expanduser()
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        if isinstance(handler, RotatingFileHandler):
            handler.close()
    level = normalize_log_level(level)
    logging.disable(sys.maxsize if level == DEFAULT_LOG_LEVEL else logging.NOTSET)
    if level == DEFAULT_LOG_LEVEL:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    root.setLevel(getattr(logging, level))

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    redactor = RedactingFilter()

    file_handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=LOG_BACKUP_COUNT, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.addFilter(redactor)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(redactor)
    root.addHandler(stream_handler)

    return path


def clear_log_files(path: Path) -> None:
    path.unlink(missing_ok=True)
    for index in range(1, LOG_BACKUP_COUNT + 1):
        path.with_name(f"{path.name}.{index}").unlink(missing_ok=True)
