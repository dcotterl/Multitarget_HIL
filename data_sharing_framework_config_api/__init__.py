"""Repository-root compatibility package for local, non-installed usage."""

import sys
from pathlib import Path

_PYTHON_ROOT = Path(__file__).resolve().parent.parent / "Python"
if str(_PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(_PYTHON_ROOT))

_PACKAGE_DIR = _PYTHON_ROOT / "data_sharing_framework_config_api"
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
