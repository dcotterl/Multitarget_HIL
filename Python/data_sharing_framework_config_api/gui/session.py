"""Configuration/session helpers for the configuration GUI."""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from data_sharing_framework_config_api import definitions

logger = logging.getLogger(__name__)


def _runtime_package_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[2]


PACKAGE_ROOT = _runtime_package_root()
REPOSITORY_ROOT = PACKAGE_ROOT.parent
DEFAULT_CONFIG_CANDIDATES = (
    PACKAGE_ROOT / "data" / "Simple_c1.dsf",
    REPOSITORY_ROOT / "VeriStand" / "rdma configs" / "Simple_c1.dsf",
)


@dataclass
class ConfigurationSession:
    """Mutable application session for the GUI."""

    configuration: definitions.Configuration = None
    current_path: Path | None = None

    def __post_init__(self):
        if self.configuration is None:
            self.configuration = definitions.Configuration(plugins=[])

    def default_config_path(self) -> Path | None:
        for candidate in DEFAULT_CONFIG_CANDIDATES:
            if candidate.exists():
                return candidate
        return None

    def load_file(self, file_path: str | Path) -> None:
        path = Path(file_path)
        logger.info("Loading configuration file from path: %s", path)
        suffix = path.suffix.lower()
        if suffix not in {".json", ".dsf"}:
            logger.error("Failed to load file '%s': unsupported extension '%s'", path, suffix)
            raise ValueError("Unsupported file type. Expected .json or .dsf.")
        with path.open("r", encoding="utf-8") as handle:
            file_content = json.load(handle)
        if not isinstance(file_content, dict):
            logger.error("Failed to load file '%s': content is not a dictionary", path)
            raise ValueError("Selected file content is not a dictionary.")
        
        self.configuration = definitions.Configuration.from_dict(file_content)
        self.current_path = path.resolve()
        logger.info("Successfully loaded configuration '%s' (%d plugins)", self.current_path, len(self.configuration.plugins))

    def save_file(self, file_path: str | Path) -> Path:
        output_path = Path(file_path)
        logger.info("Saving configuration to file: %s", output_path)
        if output_path.suffix.lower() not in {".dsf", ".json"}:
            output_path = output_path.with_suffix(".dsf")
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(self.configuration.getDict(), handle, indent=4)
        self.current_path = output_path.resolve()
        logger.info("Successfully saved configuration to '%s'", self.current_path)
        return self.current_path

    def new_configuration(self) -> None:
        """Create a new empty configuration."""
        logger.info("Creating new empty configuration session")
        self.configuration = definitions.Configuration(plugins=[])
        self.current_path = None

    def label_text(self) -> str:
        return str(self.current_path) if self.current_path is not None else "New configuration"

