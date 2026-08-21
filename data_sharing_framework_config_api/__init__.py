"""Repository-root compatibility package for local, non-installed usage."""

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent.parent / "Python" / "data_sharing_framework_config_api"
__path__ = [str(_PACKAGE_DIR)]

from .rdma_definitions import (  # noqa: E402
    Channel,
    ComponentSettings,
    Direction,
    Element,
    Plugin,
    RDMA_Configuration,
    Thread,
    Transfer,
    TransferGroup,
    channel,
    component_settings,
    element,
    get_version,
    plugin,
    thread,
    transfer,
    transferGroup,
)

__all__ = [
    "Channel",
    "ComponentSettings",
    "Direction",
    "Element",
    "Plugin",
    "RDMA_Configuration",
    "Thread",
    "Transfer",
    "TransferGroup",
    "channel",
    "component_settings",
    "element",
    "get_version",
    "plugin",
    "thread",
    "transfer",
    "transferGroup",
]
