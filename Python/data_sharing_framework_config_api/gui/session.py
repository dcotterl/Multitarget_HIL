"""Configuration/session helpers for the configuration GUI."""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from data_sharing_framework_config_api import definitions
from data_sharing_framework_config_api.protocol_factory import ProtocolFactory

logger = logging.getLogger(__name__)


def _runtime_package_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[2]


PACKAGE_ROOT = _runtime_package_root()


@dataclass
class ConfigurationSession:
    """Mutable application session for the GUI."""

    configuration: definitions.Configuration = None
    current_path: Path | None = None
    protocol: str = "RDMA"

    def __post_init__(self):
        if self.configuration is None:
            self.configuration = definitions.Configuration(plugins=[])
        self.protocol = self.protocol.strip().upper()
        if self.configuration.plugins:
            self.protocol = self._configuration_protocol()
        if self.protocol != "MIXED":
            ProtocolFactory.get_handler(self.protocol)

    def file_dialog_directory(self) -> Path:
        """Return the last-used directory or the executable directory."""
        if self.current_path is not None:
            return self.current_path.parent
        return Path(sys.executable).resolve().parent

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
        self.protocol = self._configuration_protocol()
        self.current_path = path.resolve()
        logger.info("Successfully loaded configuration '%s' (%d plugins)", self.current_path, len(self.configuration.plugins))

    def save_file(self, file_path: str | Path) -> Path:
        output_path = Path(file_path)
        logger.info("Saving configuration to file: %s", output_path)
        if output_path.suffix.lower() not in {".dsf", ".json"}:
            output_path = output_path.with_suffix(".dsf")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=output_path.parent,
                prefix=f".{output_path.name}.", suffix=".tmp", delete=False
            ) as handle:
                temporary_path = Path(handle.name)
                json.dump(self.configuration.to_dict(), handle, indent=4)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, output_path)
        except Exception:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise
        self.current_path = output_path.resolve()
        logger.info("Successfully saved configuration to '%s'", self.current_path)
        return self.current_path

    def new_configuration(self) -> None:
        """Create a new empty configuration without assigning a protocol."""
        logger.info("Creating new protocol-neutral configuration session")
        self.configuration = definitions.Configuration(plugins=[])
        self.current_path = None
        self.protocol = "RDMA"

    def _configuration_protocol(self) -> str:
        protocols = {
            str(plugin.components[0]).strip().upper()
            for plugin in self.configuration.plugins
            if getattr(plugin, "components", None)
        }
        if len(protocols) > 1:
            return "MIXED"
        if protocols:
            return protocols.pop()
        return self.protocol

    def label_text(self) -> str:
        return str(self.current_path) if self.current_path is not None else "New configuration"

