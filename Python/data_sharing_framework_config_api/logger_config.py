"""Logging configuration manager for Data Sharing Framework API and GUI.

Loads configuration settings from logging_config.json, sets up console,
file, and in-memory logging handlers, and allows runtime inspection of logs.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from collections import deque
from pathlib import Path
from typing import Any, List, Tuple


class InMemoryLogHandler(logging.Handler):
    """Logging handler that buffers formatted log records in memory for GUI display."""

    def __init__(self, capacity: int = 1000) -> None:
        super().__init__()
        self.records: deque[str] = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.records.append(msg)
        except Exception:
            self.handleError(record)

    def get_logs(self) -> List[str]:
        return list(self.records)

    def clear(self) -> None:
        self.records.clear()


# Global singleton instance of in-memory handler
in_memory_handler = InMemoryLogHandler()

DEFAULT_CONFIG: dict[str, Any] = {
    "level": "INFO",
    "log_to_file": True,
    "log_file_path": "app.log",
    "format": "%(asctime)s [%(levelname)s] [%(module)s.%(funcName)s:%(lineno)d] %(message)s",
}


def find_logging_config_path() -> Path:
    """Find the preferred location for logging_config.json.

    In a frozen executable, the config should live next to the executable so it is
    reused across future launches without depending on the working directory.
    """
    if getattr(sys, "frozen", False):
        exe_config = Path(sys.executable).resolve().parent / "logging_config.json"
        if exe_config.exists():
            return exe_config
        return exe_config

    candidates = [
        Path.cwd() / "logging_config.json",
        Path(__file__).resolve().parent / "logging_config.json",
        Path(__file__).resolve().parent.parent / "logging_config.json",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return Path.cwd() / "logging_config.json"


def load_logging_config() -> Tuple[dict[str, Any], Path]:
    """Load logging config from logging_config.json or create default file if missing."""
    config_path = find_logging_config_path()
    config = dict(DEFAULT_CONFIG)

    if config_path.exists():
        try:
            with config_path.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    config.update(loaded)
        except Exception as err:
            print(f"[Logging] Error reading {config_path}: {err}", file=sys.stderr)
    else:
        try:
            with config_path.open("w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as err:
            print(f"[Logging] Could not create default config at {config_path}: {err}", file=sys.stderr)

    return config, config_path


def save_logging_config(config: dict[str, Any]) -> Path:
    """Save configuration dictionary to logging_config.json and re-apply logging settings."""
    config_path = find_logging_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=config_path.parent,
            prefix=f".{config_path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(config, handle, indent=4)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, config_path)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    setup_logging()
    return config_path


def _resolve_log_file_path(config_path: Path, configured_path: Any) -> Path:
    """Resolve a log path and prevent writes outside the application directory."""
    if not isinstance(configured_path, str) or not configured_path.strip():
        raise ValueError("log_file_path must be a non-empty string.")
    base_path = config_path.parent.resolve()
    candidate = Path(configured_path)
    resolved = (candidate if candidate.is_absolute() else base_path / candidate).resolve()
    if resolved != base_path and base_path not in resolved.parents:
        raise ValueError("log_file_path must remain inside the application directory.")
    return resolved


def setup_logging() -> Tuple[dict[str, Any], Path]:
    """Configure python logging according to logging_config.json settings."""
    config, config_path = load_logging_config()

    level_name = str(config.get("level", "INFO")).upper()
    if level_name not in logging._nameToLevel:
        raise ValueError(f"Unknown logging level '{level_name}'.")
    level = logging._nameToLevel[level_name]
    fmt_str = config.get(
        "format",
        "%(asctime)s [%(levelname)s] [%(module)s.%(funcName)s:%(lineno)d] %(message)s",
    )
    if not isinstance(fmt_str, str):
        raise ValueError("format must be a string.")
    formatter = logging.Formatter(fmt_str)

    # Root logger for data_sharing_framework_config_api
    package_logger = logging.getLogger("data_sharing_framework_config_api")
    package_logger.setLevel(level)
    for handler in package_logger.handlers[:]:
        package_logger.removeHandler(handler)
        if handler is not in_memory_handler:
            handler.close()

    # Stream Handler (console)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    package_logger.addHandler(console_handler)

    # In-Memory Handler (GUI window)
    in_memory_handler.setLevel(level)
    in_memory_handler.setFormatter(formatter)
    package_logger.addHandler(in_memory_handler)

    # File Handler (optional)
    if config.get("log_to_file", True):
        log_file = config.get("log_file_path", "app.log")
        try:
            file_path = _resolve_log_file_path(config_path, log_file)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(file_path, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            package_logger.addHandler(file_handler)
        except Exception as err:
            print(f"[Logging] Failed to attach file handler for {log_file}: {err}", file=sys.stderr)

    package_logger.info("Logging initialized from '%s' (Level: %s, File logging: %s)", config_path, level_name, config.get("log_to_file"))

    return config, config_path
