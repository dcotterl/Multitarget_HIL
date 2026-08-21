"""Configuration/session helpers for the RDMA GUI."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from data_sharing_framework_config_api import rdma_definitions as rdma


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

    configuration: rdma.RDMA_Configuration = field(default_factory=rdma.RDMA_Configuration)
    current_path: Path | None = None

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
        self.configuration.importFromDict(file_content)
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
        new_configuration = rdma.RDMA_Configuration(plugins=[])
        new_plugin = rdma.Plugin(name="Plugin 1", protocol="RDMA", threads=[])
        new_thread = rdma.Thread(processor=-2, protocol="RDMA", transfer_groups=[])
        new_group = rdma.TransferGroup(
            name="Transfer Group 1",
            direction=rdma.Direction.TX,
            protocol="RDMA",
            transfers=[],
        )
        new_transfer = rdma.Transfer(
            protocol="RDMA",
            name="Transfer 1",
            channels=[],
            local_address="local address",
            local_port=0,
            destination_address="destination address",
            destination_port=0,
        )
        new_transfer.addChannel(rdma.Channel(name="Channel 1", protocol="RDMA"))
        new_group.addTransfer(new_transfer)
        new_thread.addTransferGroup(new_group)
        new_plugin.addThread(new_thread)
        new_configuration.addPlugin(new_plugin)
        self.configuration = rdma.RDMA_Configuration.from_dict(new_configuration.getDict())
        self.current_path = None

    def label_text(self) -> str:
        return str(self.current_path) if self.current_path is not None else "New configuration"
