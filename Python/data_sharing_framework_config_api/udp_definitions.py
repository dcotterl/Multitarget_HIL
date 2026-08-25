from __future__ import annotations

import socket
import struct

import json
import logging
from enum import Enum
from typing import Iterable, TypeVar

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

T = TypeVar("T")

def ip_to_string(ip_address: str) -> str:
    """Convert an IPv4 address string (e.g. '127.0.0.1') into its integer
    representation as a string (e.g. '2130706433')."""
    packed = socket.inet_aton(ip_address)
    return str(struct.unpack("!L", packed)[0])


def string_to_ip(int_string: str) -> str:
    """Convert an integer string (e.g. '2130706433') back into its IPv4
    address representation (e.g. '127.0.0.1')."""
    packed = struct.pack("!L", int(int_string))
    return socket.inet_ntoa(packed)

class Direction(Enum):
    """Direction of an RDMA transfer."""

    TX = 0
    RX = 1


def _ensure_dict(data, context: str) -> dict:
    if not isinstance(data, dict):
        raise TypeError(f"{context} must be a dictionary.")
    return data


def _ensure_list(value, context: str) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"{context} must be a list.")
    return value


def _coerce_direction(value, context: str = "direction") -> Direction:
    if isinstance(value, Direction):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        if normalized in Direction.__members__:
            return Direction[normalized]
        if normalized.isdigit() or (normalized.startswith("-") and normalized[1:].isdigit()):
            value = int(normalized)
        else:
            raise ValueError(f"{context} must be one of {', '.join(Direction.__members__)}.")
    try:
        return Direction(value)
    except ValueError as error:
        raise ValueError(f"{context} must be one of {', '.join(Direction.__members__)}.") from error


def _validate_items(values: Iterable, expected_type: type[T], context: str) -> list[T]:
    validated = []
    for index, item in enumerate(values):
        if not isinstance(item, expected_type):
            raise TypeError(
                f"{context} item {index} must be {expected_type.__name__}, got {type(item).__name__}."
            )
        validated.append(item)
    return validated


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
        data = _ensure_dict(data, "Element")
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

    @property
    def elements(self) -> list[Element]:
        return self._elements

    @elements.setter
    def elements(self, values: list[Element]) -> None:
        self._elements = _validate_items(_ensure_list(values, "ComponentSettings.elements"), Element, "ComponentSettings.elements")

    def __str__(self) -> str:
        return json.dumps(self.getDict(), indent=4)

    def getDict(self) -> dict:
        return {"component": self.component, "values": [v.getDict() for v in self.elements]}

    def importFromDict(self, data: dict) -> None:
        data = _ensure_dict(data, "ComponentSettings")
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
    """An RDMA channel definition and its serialized settings."""

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
        self.component_settings = []

    @property
    def component_settings(self) -> list[ComponentSettings]:
        return self._component_settings

    @component_settings.setter
    def component_settings(self, values: list[ComponentSettings]) -> None:
        self._component_settings = _validate_items(
            _ensure_list(values, "Channel.component_settings"),
            ComponentSettings,
            "Channel.component_settings",
        )

    def __str__(self) -> str:
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
        data = _ensure_dict(data, "Channel")
        core = _ensure_dict(data.get("core", {}), "Channel.core")
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

    def addComponentSetting(self, component_setting: ComponentSettings) -> None:
        self.component_settings = [*self.component_settings, component_setting]


class Transfer:
    """An RDMA data transfer configuration."""

    def __init__(
        self,
        protocol: str = "",
        name: str = "",
        channels: list[Channel] | None = None,
        source_address: str = "",
        source_port: int = 0,
        destination_address: str = "",
        destination_port: int = 0,
    ) -> None:
        self.name = name
        self.channels = channels if channels is not None else []
        self.source_address = source_address
        self.source_port = source_port
        self.destination_address = destination_address
        self.destination_port = destination_port

        elements = [
            Element("source address" if self.source_address != "" else "destination address", 
                    ip_to_string(self.source_address) if self.source_address != "" else ip_to_string(self.destination_address)),
            Element("source port" if self.source_port != 0 else "destination port", 
                    str(self.source_port) if self.source_port != 0 else str(self.destination_port)),
        ]
        self.component_settings = [ComponentSettings(protocol, elements)]

    @property
    def source_address(self) -> str:
        return self._source_address

    @source_address.setter
    def source_address(self, value: str) -> None:
        self._source_address = value

    @property
    def source_port(self) -> int:
        return self._source_port

    @source_port.setter
    def source_port(self, value: int) -> None:
        self._source_port = value

    @property
    def destination_address(self) -> str:
        return self._destination_address

    @destination_address.setter
    def destination_address(self, value: str) -> None:
        self._destination_address = value

    @property
    def destination_port(self) -> int:
        return self._destination_port

    @destination_port.setter
    def destination_port(self, value: int) -> None:
        self._destination_port = value

    @property
    def channels(self) -> list[Channel]:
        return self._channels

    @channels.setter
    def channels(self, values: list[Channel]) -> None:
        self._channels = _validate_items(_ensure_list(values, "Transfer.channels"), Channel, "Transfer.channels")

    @property
    def component_settings(self) -> list[ComponentSettings]:
        return self._component_settings

    @component_settings.setter
    def component_settings(self, values: list[ComponentSettings]) -> None:
        self._component_settings = _validate_items(
            _ensure_list(values, "Transfer.component_settings"),
            ComponentSettings,
            "Transfer.component_settings",
        )

    def __str__(self) -> str:
        result = self.getDict()
        result["channels"] = "[EMPTY]" if not self.channels else f"[...{len(self.channels)} channels...]"
        return json.dumps(result, indent=4)

    def getDict(self) -> dict:
        return {
            "core": {"name": self.name},
            "component settings": [cs.getDict() for cs in self.component_settings],
            "channels": [ch.getDict() for ch in self.channels],
        }

    def importFromDict(self, data: dict) -> None:
        data = _ensure_dict(data, "Transfer")
        core = _ensure_dict(data.get("core", {}), "Transfer.core")
        self.name = core.get("name", "")
        self.component_settings = [
            ComponentSettings.from_dict(cs)
            for cs in _ensure_list(data.get("component settings", []), "Transfer.component settings")
        ]
        endpoint_values = {
            element.key: element.value
            for element in self.component_settings[0].elements
            if self.component_settings
            and element.key in {"local address", "local port", "destination address", "destination port"}
        }
        self.local_address = endpoint_values.get("local address", "")
        self.local_port = endpoint_values.get("local port", 0)
        self.destination_address = endpoint_values.get("destination address", "")
        self.destination_port = endpoint_values.get("destination port", 0)
        self.channels = [Channel.from_dict(ch) for ch in _ensure_list(data.get("channels", []), "Transfer.channels")]

    @classmethod
    def from_dict(cls, data: dict) -> "Transfer":
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

    def addChannel(self, channel: Channel) -> None:
        self.channels = [*self.channels, channel]

    def addElement(self, key: str, value) -> None:
        if self.component_settings:
            self.component_settings[0].elements = [*self.component_settings[0].elements, Element(key, value)]
        else:
            raise ValueError("Transfer requires component settings before adding elements.")

    def addComponentSetting(self, component_setting: ComponentSettings) -> None:
        self.component_settings = [*self.component_settings, component_setting]


class TransferGroup:
    """A group of transfers sharing a common direction."""

    def __init__(
        self,
        name: str = "",
        direction: Direction = Direction.TX,
        priority: int = 100,
        decimation: int = 1,
        offset: int = 0,
        timeout_behaviour: int = 0,
        enable_conversion: bool = False,
        protocol: str = "",
        transfers: list[Transfer] | None = None,
    ) -> None:
        self.name = name
        self.direction = direction
        self.priority = priority
        self.decimation = decimation
        self.offset = offset
        self.timeout_behaviour = timeout_behaviour
        self.enable_conversion = enable_conversion
        self.component_settings = []
        self.transfers = transfers if transfers is not None else []

    @property
    def direction(self) -> Direction:
        return self._direction

    @direction.setter
    def direction(self, value) -> None:
        direction = _coerce_direction(value, "TransferGroup.direction")
        self._direction = direction

    @property
    def component_settings(self) -> list[ComponentSettings]:
        return self._component_settings

    @component_settings.setter
    def component_settings(self, values: list[ComponentSettings]) -> None:
        self._component_settings = _validate_items(
            _ensure_list(values, "TransferGroup.component_settings"),
            ComponentSettings,
            "TransferGroup.component_settings",
        )

    @property
    def transfers(self) -> list[Transfer]:
        return self._transfers

    @transfers.setter
    def transfers(self, values: list[Transfer]) -> None:
        self._transfers = _validate_items(
            _ensure_list(values, "TransferGroup.transfers"), Transfer, "TransferGroup.transfers"
        )

    def __str__(self) -> str:
        result = self.getDict()
        result["core"]["direction"] = str(self.direction.name)
        result["transfers"] = "[EMPTY]" if not self.transfers else f"[...{len(self.transfers)} transfers...]"
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

    def importFromDict(self, data: dict) -> None:
        data = _ensure_dict(data, "TransferGroup")
        core = _ensure_dict(data.get("core", {}), "TransferGroup.core")
        self.name = core.get("name", "")
        self.direction = core.get("direction", 0)
        cycle_timing = _ensure_dict(core.get("cycle timing", {}), "TransferGroup.core.cycle timing")
        self.priority = cycle_timing.get("priority", 100)
        self.decimation = cycle_timing.get("decimation", 1)
        self.offset = cycle_timing.get("offset", 0)
        self.timeout_behaviour = core.get("timeout behavior", 0)
        self.enable_conversion = core.get("enable conversion", False)
        self.component_settings = [
            ComponentSettings.from_dict(cs)
            for cs in _ensure_list(data.get("component settings", []), "TransferGroup.component settings")
        ]
        self.transfers = [Transfer.from_dict(t) for t in _ensure_list(data.get("transfers", []), "TransferGroup.transfers")]

    @classmethod
    def from_dict(cls, data: dict) -> "TransferGroup":
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

    def addTransfer(self, transfer: Transfer) -> None:
        self.transfers = [*self.transfers, transfer]


class Thread:
    """A thread configuration for RDMA operations."""

    def __init__(
        self,
        processor: int = -2,
        priority_offset: int = 0,
        protocol: str = "",
        transfer_groups: list[TransferGroup] | None = None,
        local_address: str = "",
        local_port: int = 0,
    ) -> None:
        self.processor = processor
        self.priority_offset = priority_offset
        self.component_settings = [ComponentSettings(protocol, 
                                                     [Element("local port", str(local_port)),
                                                      Element("local address", ip_to_string(local_address)),
                                                      ])]
        self.local_address = local_address
        self.local_port = local_port
        self.transfer_groups = transfer_groups if transfer_groups is not None else []

    @property
    def component_settings(self) -> list[ComponentSettings]:
        return self._component_settings

    @component_settings.setter
    def component_settings(self, values: list[ComponentSettings]) -> None:
        self._component_settings = _validate_items(
            _ensure_list(values, "Thread.component_settings"),
            ComponentSettings,
            "Thread.component_settings",
        )

    @property
    def transfer_groups(self) -> list[TransferGroup]:
        return self._transfer_groups

    @transfer_groups.setter
    def transfer_groups(self, values: list[TransferGroup]) -> None:
        self._transfer_groups = _validate_items(
            _ensure_list(values, "Thread.transfer_groups"),
            TransferGroup,
            "Thread.transfer_groups",
        )

    def __str__(self) -> str:
        result = self.getDict()
        result["transfer groups"] = (
            "[EMPTY]" if not self.transfer_groups else f"[...{len(self.transfer_groups)} transfer groups...]"
        )
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
        data = _ensure_dict(data, "Thread")
        core = _ensure_dict(data.get("core", {}), "Thread.core")
        self.processor = core.get("processor", -2)
        self.priority_offset = core.get("priority offset", 0)
        self.component_settings = [
            ComponentSettings.from_dict(cs)
            for cs in _ensure_list(data.get("component settings", []), "Thread.component settings")
        ]
        self.transfer_groups = [
            TransferGroup.from_dict(tg)
            for tg in _ensure_list(data.get("transfer groups", []), "Thread.transfer groups")
        ]
        self.local_address = self.component_settings[0].elements[0].value
        self.local_port = self.component_settings[0].elements[1].value

    @classmethod
    def from_dict(cls, data: dict) -> "Thread":
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

    def addTransferGroup(self, transfer_group: TransferGroup) -> None:
        self.transfer_groups = [*self.transfer_groups, transfer_group]


class Plugin:
    """An UDP plugin containing one or more threads."""

    def __init__(
        self,
        name: str = "",
        protocol: str = "",
        priority: int = 10000,
        decimation: int = 1,
        offset: int = 0,
        threads: list[Thread] | None = None,
    ) -> None:
        self.name = name
        self.components = [protocol] if protocol else []
        self.priority = priority
        self.decimation = decimation
        self.offset = offset
        self.threads = threads if threads is not None else []
        self.component_settings = []

    @property
    def components(self) -> list[str]:
        return self._components

    @components.setter
    def components(self, values: list[str]) -> None:
        values = _ensure_list(values, "Plugin.components")
        for index, item in enumerate(values):
            if not isinstance(item, str):
                raise TypeError(f"Plugin.components item {index} must be str, got {type(item).__name__}.")
        self._components = list(values)

    @property
    def threads(self) -> list[Thread]:
        return self._threads

    @threads.setter
    def threads(self, values: list[Thread]) -> None:
        self._threads = _validate_items(_ensure_list(values, "Plugin.threads"), Thread, "Plugin.threads")

    @property
    def component_settings(self) -> list[ComponentSettings]:
        return self._component_settings

    @component_settings.setter
    def component_settings(self, values: list[ComponentSettings]) -> None:
        self._component_settings = _validate_items(
            _ensure_list(values, "Plugin.component_settings"),
            ComponentSettings,
            "Plugin.component_settings",
        )

    def __str__(self) -> str:
        result = self.getDict()
        result["threads"] = "[EMPTY]" if not self.threads else f"[...{len(self.threads)} threads...]"
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
        data = _ensure_dict(data, "Plugin")
        core = _ensure_dict(data.get("core", {}), "Plugin.core")
        self.name = core.get("name", "")
        self.components = core.get("components", [])
        cycle_timing = _ensure_dict(core.get("cycle timing", {}), "Plugin.core.cycle timing")
        self.priority = cycle_timing.get("priority", 10000)
        self.decimation = cycle_timing.get("decimation", 1)
        self.offset = cycle_timing.get("offset", 0)
        self.component_settings = [
            ComponentSettings.from_dict(cs)
            for cs in _ensure_list(data.get("component settings", []), "Plugin.component settings")
        ]
        self.threads = [Thread.from_dict(th) for th in _ensure_list(data.get("threads", []), "Plugin.threads")]

    @classmethod
    def from_dict(cls, data: dict) -> "Plugin":
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

    def addThread(self, thread: Thread) -> None:
        self.threads = [*self.threads, thread]


class UDP_Configuration:
    """Top-level RDMA configuration containing one or more plugins."""

    def __init__(
        self,
        plugins: list[Plugin] | None = None,
        dsfversion: dict | None = None,
        version: dict | None = None,
    ) -> None:
        self.dsfversion = dsfversion if dsfversion is not None else {"major": 1, "minor": 4, "fix": 0, "build": ""}
        self.version = version if version is not None else {"major": 1, "minor": 0, "fix": 0, "build": ""}
        self.plugins = plugins if plugins is not None else []

    @property
    def plugins(self) -> list[Plugin]:
        return self._plugins

    @plugins.setter
    def plugins(self, values: list[Plugin]) -> None:
        self._plugins = _validate_items(_ensure_list(values, "UDP_Configuration.plugins"), Plugin, "UDP_Configuration.plugins")

    def getDict(self) -> dict:
        return {
            "dsfversion": self.dsfversion,
            "version": self.version,
            "configuration": {
                "plugins": [pl.getDict() for pl in self.plugins],
            },
        }

    def importFromDict(self, data: dict) -> None:
        data = _ensure_dict(data, "UDP_Configuration")
        self.dsfversion = data.get("dsfversion", {"major": 1, "minor": 4, "fix": 0, "build": ""})
        self.version = data.get("version", {"major": 1, "minor": 0, "fix": 0, "build": ""})
        configuration = _ensure_dict(data.get("configuration", {}), "UDP_Configuration.configuration")
        self.plugins = [Plugin.from_dict(pl) for pl in _ensure_list(configuration.get("plugins", []), "UDP_Configuration.plugins")]

    @classmethod
    def from_dict(cls, data: dict) -> "UDP_Configuration":
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

    def addPlugin(self, plugin: Plugin) -> None:
        self.plugins = [*self.plugins, plugin]

    def __str__(self) -> str:
        result = self.getDict()
        result["configuration"]["plugins"] = "[EMPTY]" if not self.plugins else f"[...{len(self.plugins)} plugins...]"
        return json.dumps(result, indent=4)







if __name__ == "__main__":
    # Example usage
    ip = "127.0.0.2"
    int_str = ip_to_string(ip)
    print(f"IP address {ip} as integer string: {int_str}")
    ip_converted_back = string_to_ip(int_str)
    print(f"Integer string {int_str} converted back to IP address: {ip_converted_back}")