"""Configuration/session helpers for the configuration GUI."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from data_sharing_framework_config_api import (
    definitions,
    rdma_definitions as rdma,
    udp_definitions as udp,
)


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


def detect_protocol(configuration: definitions.Configuration) -> Literal["RDMA", "UDP"]:
    """Detect the protocol used in a configuration based on plugin components."""
    if not configuration.plugins:
        return "RDMA"  # Default to RDMA
    
    first_plugin = configuration.plugins[0]
    if hasattr(first_plugin, 'components') and first_plugin.components:
        protocol = first_plugin.components[0]
        if protocol in ("RDMA", "UDP"):
            return protocol
    
    return "RDMA"  # Default to RDMA


def create_configuration_for_protocol(protocol: Literal["RDMA", "UDP"]) -> definitions.Configuration:
    """Create a new configuration object for the specified protocol."""
    if protocol == "UDP":
        return udp.UDP_Configuration()
    return rdma.RDMA_Configuration()


@dataclass
class ConfigurationSession:
    """Mutable application session for the GUI."""

    configuration: definitions.Configuration = None
    current_path: Path | None = None
    protocol: Literal["RDMA", "UDP"] = "RDMA"

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
        suffix = path.suffix.lower()
        if suffix not in {".json", ".dsf"}:
            raise ValueError("Unsupported file type. Expected .json or .dsf.")
        with path.open("r", encoding="utf-8") as handle:
            file_content = json.load(handle)
        if not isinstance(file_content, dict):
            raise ValueError("Selected file content is not a dictionary.")
        
        # Detect protocol from file content
        detected_protocol = detect_protocol(definitions.Configuration.from_dict(file_content))
        self.protocol = detected_protocol
        
        # Create appropriate configuration object for the protocol
        if detected_protocol == "UDP":
            self.configuration = udp.UDP_Configuration.from_dict(file_content)
        else:
            self.configuration = rdma.RDMA_Configuration.from_dict(file_content)
        
        self.current_path = path.resolve()

    def save_file(self, file_path: str | Path) -> Path:
        output_path = Path(file_path)
        if output_path.suffix.lower() not in {".dsf", ".json"}:
            output_path = output_path.with_suffix(".dsf")
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(self.configuration.getDict(), handle, indent=4)
        self.current_path = output_path.resolve()
        return self.current_path

    def new_configuration(self) -> None:
        """Create a new empty configuration."""
        self.configuration = definitions.Configuration(plugins=[])
        self.current_path = None

    def label_text(self) -> str:
        return str(self.current_path) if self.current_path is not None else "New configuration"

