"""Rotating structured logging with mandatory sensitive-data redaction."""

import json
import logging
from logging.handlers import RotatingFileHandler
import os
import re


class SensitiveDataFilter(logging.Filter):
    SENSITIVE_KEYS = frozenset({"password", "password_hash", "password_salt", "salt",
                                "token", "session_token", "authorization"})
    _PATTERN = re.compile(
        r'(?i)(password(?:_hash|_salt)?|salt|session_token|token|authorization)'
        r'(["\s:=]+)([^,}\s]+)'
    )

    @classmethod
    def redact(cls, value):
        if isinstance(value, dict):
            return {key: "[REDACTED]" if str(key).lower() in cls.SENSITIVE_KEYS else cls.redact(item)
                    for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls.redact(item) for item in value]
        if isinstance(value, str):
            return cls._PATTERN.sub(lambda match: f'{match.group(1)}{match.group(2)}[REDACTED]', value)
        return value

    def filter(self, record):
        record.msg = self.redact(record.msg)
        if record.args:
            record.args = tuple(self.redact(arg) for arg in record.args) if isinstance(record.args, tuple) else self.redact(record.args)
        return True


class LoggingService:
    def __init__(self, settings):
        self.settings = settings

    def create_logger(self, name: str, path: str) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, self.settings.level.upper(), logging.INFO))
        logger.propagate = False
        absolute_path = os.path.abspath(path)
        if any(getattr(handler, "baseFilename", None) == absolute_path for handler in logger.handlers):
            return logger
        directory = os.path.dirname(absolute_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        handler = RotatingFileHandler(absolute_path, maxBytes=self.settings.maximum_file_bytes,
                                      backupCount=self.settings.backup_count, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)
        return logger

    @staticmethod
    def event(logger: logging.Logger, level: int, event: str, **details) -> None:
        payload = {"event": event, **SensitiveDataFilter.redact(details)}
        logger.log(level, json.dumps(payload, ensure_ascii=False, default=str))
