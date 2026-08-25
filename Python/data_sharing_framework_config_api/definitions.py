from __future__ import annotations

import json
import logging
from enum import Enum
from typing import Iterable, TypeVar

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

T = TypeVar("T")

class Protocols(Enum):
    """Protocols supported by the RDMA configuration."""

    RDMA = "RDMA"
    UDP = "UDP"

class Direction(Enum):
    """Direction of an RDMA transfer."""

    TX = 0
    RX = 1

def ensure_dict(data, context: str) -> dict:
    if not isinstance(data, dict):
        raise TypeError(f"{context} must be a dictionary.")
    return data

def ensure_list(value, context: str) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"{context} must be a list.")
    return value


class Element:
    """A key-value pair used inside :class:`ComponentSettings`."""

    def __init__(self, key: str, value) -> None:
        self.key = key
        self.value = value

    def getDict(self) -> dict:
        return {"key": self.key, "value": self.value}

    def __str__(self) -> str:
        return json.dumps(self.getDict(), indent=4)

    def importFromDict(self, data: dict) -> None:
        data = ensure_dict(data, "Element")
        if "key" not in data:
            raise ValueError("Element is missing required field 'key'.")
        self.key = data.get("key")
        self.value = data.get("value")

    @classmethod
    def from_dict(cls, data: dict) -> "Element":
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

class ComponentSettings:
    """Component-specific settings stored as a list of :class:`Element` pairs."""

    def __init__(self, component: str = "", initial_elements: list[Element] | None = None) -> None:
        self.component = component
        self.elements = initial_elements if initial_elements is not None else []

    def __str__(self) -> str:
        result = self.getDict()
        result["values"] = "[EMPTY]" if not self.elements else f"[{len(self.elements)} elements]"
        return json.dumps(result, indent=4)

    def getDict(self) -> dict:
        return {"component": self.component, "values": [v.getDict() for v in self.elements]}

    def importFromDict(self, data: dict) -> None:
        data = ensure_dict(data, "ComponentSettings")
        self.component = data.get("component", "")
        self.elements = [Element.from_dict(v) for v in _ensure_list(data.get("values", []), "ComponentSettings.values")]

    @classmethod
    def from_dict(cls, data: dict) -> "ComponentSettings":
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

    def addElement(self, key: str, value) -> None:
        self.elements = [*self.elements, Element(key, value)]

class Channel:
    """A channel definition and its serialized settings."""

    def __init__(
        self,
        name: str = "",
        unit: str = "",
        engine_data_type: int = 2,
        string_data_type: int = 2,
        string_offset: int = 0,
    ) -> None:
        self.name = name
        self.unit = unit
        self.engine_data_type = engine_data_type
        self.string_data_type = string_data_type
        self.string_offset = string_offset
        self.component_settings = [ComponentSettings()]

    def __str__(self) -> str:
        result = self.getDict()
        result["component settings"] = "[EMPTY]" if not self.component_settings else f"[{len(self.component_settings)} component settings]"
        return json.dumps(self.getDict(), indent=4)

    def getDict(self) -> dict:
        return {
            "core": {
                "name": self.name,
                "units": self.unit,
                "engine data type": self.engine_data_type,
                "string data type": self.string_data_type,
                "string offset": self.string_offset,
            },
            "component settings": [cs.getDict() for cs in self.component_settings],
        }

    def importFromDict(self, data: dict) -> None:
        data = ensure_dict(data, "Channel")
        core = ensure_dict(data.get("core", {}), "Channel.core")
        self.name = core.get("name", "")
        self.unit = core.get("units", "")
        self.engine_data_type = core.get("engine data type", 2)
        self.string_data_type = core.get("string data type", 2)
        self.string_offset = core.get("string offset", 0)
        self.component_settings = [
            ComponentSettings.from_dict(cs)
            for cs in _ensure_list(data.get("component settings", []), "Channel.component settings")
        ]

    @classmethod
    def from_dict(cls, data: dict) -> "Channel":
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

class Transfer:
    def __init__(
        self,
        name: str = "",
        channels: list[Channel] | None = None,
        local_address: str = "",
        local_port: int = 0,
        destination_address: str = "",
        destination_port: int = 0,
    ) -> None:
        self.name = name
        self.channels = channels if channels is not None else []
        self.local_address = local_address
        self.local_port = local_port
        self.destination_address = destination_address
        self.destination_port = destination_port
        self.component_settings = [ComponentSettings()]

    def __str__(self, collapse: bool = True) -> str:
        result = self.getDict()
        if collapse:
            result["channels"] = "[EMPTY]" if not self.channels else f"[...{len(self.channels)} channels...]"
        else:
            result["channels"] = [ch.getDict() for ch in self.channels]
        return json.dumps(result, indent=4)

    def getDict(self) -> dict:
        return {
            "core": {"name": self.name},
            "component settings": [cs.getDict() for cs in self.component_settings],
            "channels": [ch.getDict() for ch in self.channels],
        }

    def importFromDict(self, data: dict) -> None:
        data = ensure_dict(data, "Transfer")
        core = ensure_dict(data.get("core", {}), "Transfer.core")
        self.name = core.get("name", "")
        self.component_settings = [
            ComponentSettings.from_dict(cs)
            for cs in _ensure_list(data.get("component settings", []), "Transfer.component settings")
        ]
        self.channels = [Channel.from_dict(ch) for ch in _ensure_list(data.get("channels", []), "Transfer.channels")]

    @classmethod
    def from_dict(cls, data: dict) -> "Transfer":
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

class TransferGroup:

    def __init__(
        self,name: str = "",
        direction: Direction = Direction.TX,
        priority: int = 100,
        decimation: int = 1,
        offset: int = 0,
        timeout_behaviour: int = 0,
        enable_conversion: bool = False,
        transfers: list[Transfer] | None = None,
    ) -> None:
        self.name = name
        self.direction = direction
        self.priority = priority
        self.decimation = decimation
        self.offset = offset
        self.timeout_behaviour = timeout_behaviour
        self.enable_conversion = enable_conversion
        self.transfers = transfers if transfers is not None else []
        self.component_settings = [ComponentSettings()]

    def __str__(self, collapse: bool = True) -> str:
        result = self.getDict()
        result["core"]["direction"] = str(self.direction.name)
        if collapse:
            result["transfers"] = "[EMPTY]" if not self.transfers else f"[...{len(self.transfers)} transfers...]"
        else:
            result["transfers"] = [tr.getDict() for tr in self.transfers]
        return json.dumps(result, indent=4)

    def getDict(self) -> dict:
        return {
                "core": {
                    "name": self.name,
                    "direction": self.direction.value,
                    "cycle timing": {
                        "priority": self.priority,
                        "decimation": self.decimation,
                        "offset": self.offset,
                    },
                    "timeout behavior": self.timeout_behaviour,
                    "enable conversion": self.enable_conversion,
                },
                "component settings": [cs.getDict() for cs in self.component_settings],
                "transfers": [t.getDict() for t in self.transfers],
                }

    @classmethod
    def from_dict(cls, data: dict) -> "TransferGroup":
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

class Thread:
    def __init__(
            self,
            processor: int = -2,
            priority_offset: int = 0,
            transfer_groups: list[TransferGroup] | None = None
    ) -> None:
        self.processor = processor
        self.priority_offset = priority_offset
        self.transfer_groups = transfer_groups if transfer_groups is not None else []
        self.component_settings = [ComponentSettings()]

    def __str__(self, collapse: bool = True) -> str:
        result = self.getDict()
        if collapse:
            result["transfer groups"] = "[EMPTY]" if not self.transfer_groups else f"[...{len(self.transfer_groups)} transfer groups...]"
        else:
            result["transfer groups"] = [tg.getDict() for tg in self.transfer_groups]
        return json.dumps(result, indent=4)

    def getDict(self) -> dict:
        return {
            "core": {
                "processor": self.processor,
                "priority offset": self.priority_offset,
            },
            "component settings": [cs.getDict() for cs in self.component_settings],
            "transfer groups": [tg.getDict() for tg in self.transfer_groups],
        }

    def importFromDict(self, data: dict) -> None:
            data = ensure_dict(data, "Thread")
            core = ensure_dict(data.get("core", {}), "Thread.core")
            self.processor = core.get("processor", -2)
            self.priority_offset = core.get("priority offset", 0)
            self.component_settings = [
                ComponentSettings.from_dict(cs)
                for cs in ensure_list(data.get("component settings", []), "Thread.component settings")
            ]
            self.transfer_groups = [
                TransferGroup.from_dict(tg)
                for tg in ensure_list(data.get("transfer groups", []), "Thread.transfer groups")
            ]
    
    @classmethod
    def from_dict(cls, data: dict) -> "Thread":
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

class Plugin:
    def __init__(
        self,
            name: str = "",
            priority: int = 10000,
            decimation: int = 1,
            offset: int = 0,
            threads: list[Thread] | None = None,
    ) -> None:
        self.name = name
        self.priority = priority
        self.decimation = decimation
        self.offset = offset
        self.threads = threads if threads is not None else []
        self.components = []
        self.component_settings = [ComponentSettings()]

    def __str__(self, collapse: bool = True) -> str:
        result = self.getDict()
        if collapse:
            result["threads"] = "[EMPTY]" if not self.threads else f"[...{len(self.threads)} threads...]"
        else:
            result["threads"] = [th.getDict() for th in self.threads]
        return json.dumps(result, indent=4)

    def getDict(self) -> dict:
        return {
            "core": {
                "name": self.name,
                "components": self.components,
                "cycle timing": {
                    "priority": self.priority,
                    "decimation": self.decimation,
                    "offset": self.offset,
                },
            },
            "component settings": [cs.getDict() for cs in self.component_settings],
            "threads": [th.getDict() for th in self.threads],
        }
    
    def importFromDict(self, data: dict) -> None:
        data = ensure_dict(data, "Plugin")
        core = ensure_dict(data.get("core", {}), "Plugin.core")
        self.name = core.get("name", "")
        self.components = core.get("components", [])
        cycle_timing = ensure_dict(core.get("cycle timing", {}), "Plugin.core.cycle timing")
        self.priority = cycle_timing.get("priority", 10000)
        self.decimation = cycle_timing.get("decimation", 1)
        self.offset = cycle_timing.get("offset", 0)
        self.component_settings = [
            ComponentSettings.from_dict(cs)
            for cs in ensure_list(data.get("component settings", []), "Plugin.component settings")
        ]
        self.threads = [Thread.from_dict(th) for th in ensure_list(data.get("threads", []), "Plugin.threads")]

    @classmethod
    def from_dict(cls, data: dict) -> "Plugin":
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

class Configuration:
    def __init__(self,
                 plugins: list[Plugin] | None = None,
                 dsfversion: dict | None = None,
                 version: dict | None = None,
        ) -> None:
            self.dsfversion = dsfversion if dsfversion is not None else {"major": 1, "minor": 4, "fix": 0, "build": ""}
            self.version = version if version is not None else {"major": 1, "minor": 0, "fix": 0, "build": ""}
            self.plugins = plugins if plugins is not None else []

    def __str__(self, collapse: bool = True) -> str:
            result = self.getDict()
            if collapse:
                result["configuration"]["plugins"] = "[EMPTY]" if not self.plugins else f"[...{len(self.plugins)} plugins...]"
            else:
                result["configuration"]["plugins"] = [pl.getDict() for pl in self.plugins]
            return json.dumps(result, indent=4)

    def getDict(self) -> dict:
        return {
            "dsfversion": self.dsfversion,
            "version": self.version,
            "configuration": {
                "plugins": [pl.getDict() for pl in self.plugins],
            },
        }
    
    def importFromDict(self, data: dict) -> None:
        data = ensure_dict(data, "Configuration")
        self.dsfversion = data.get("dsfversion", {"major": 1, "minor": 4, "fix": 0, "build": ""})
        self.version = data.get("version", {"major": 1, "minor": 0, "fix": 0, "build": ""})
        configuration = ensure_dict(data.get("configuration", {}), "Configuration.configuration")
        self.plugins = [Plugin.from_dict(pl) for pl in ensure_list(configuration.get("plugins", []), "Configuration.plugins")]

    @classmethod
    def from_dict(cls, data: dict) -> "Configuration":
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

def get_version() -> dict:
    """Return the current RDMA definition format version."""
    return {"major": 3, "minor": 0, "fix": 0, "build": ""}
