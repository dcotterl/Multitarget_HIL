"""Core base data model definitions for the Data Sharing Framework configuration API.

This module defines the foundational object-oriented schema used across all
supported protocols (e.g., RDMA, UDP):

    Configuration
      └── Plugin [1..n]
           └── Thread [1..n]
                └── TransferGroup [1..n]
                     └── Transfer [1..n]
                          └── Channel [1..n]

Each object level supports dictionary serialization (to_dict()), deserialization
(import_from_dict(), from_dict()), and protocol-specific ComponentSettings.
"""

from __future__ import annotations

import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

class Protocols(Enum):
    """Protocols supported by the Data Sharing Framework configuration."""

    RDMA = "RDMA"
    UDP = "UDP"

class Direction(Enum):
    """Direction of a data transfer group (TX = Transmit, RX = Receive)."""

    TX = 0
    RX = 1

def ensure_dict(data, context: str) -> dict:
    """Type guard ensuring that the given data is a dictionary.

    Args:
        data: Value to check.
        context: Description of where the check occurred (used in error messages).

    Returns:
        dict: The validated dictionary.

    Raises:
        TypeError: If data is not a dict.
    """
    if not isinstance(data, dict):
        raise TypeError(f"{context} must be a dictionary.")
    return data

def ensure_list(value, context: str) -> list:
    """Type guard ensuring that the given value is a list (or None converted to empty list).

    Args:
        value: Value to check.
        context: Description of where the check occurred (used in error messages).

    Returns:
        list: The validated list or empty list if None.

    Raises:
        TypeError: If value is neither list nor None.
    """
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"{context} must be a list.")
    return value

def validate_configuration_dict(data: dict) -> dict:
    """Validate that a dictionary matches the expected top-level configuration schema.

    This keeps malformed input from silently creating broken runtime objects and makes
    the contract explicit for future protocol additions.
    """
    data = ensure_dict(data, "Configuration")
    for version_key in ("dsfversion", "version"):
        if version_key in data and not isinstance(data[version_key], dict):
            raise ValueError(f"Configuration.{version_key} must be a dictionary.")
        if version_key in data:
            _validate_optional_scalars(data[version_key], ("major", "minor", "fix"), int, f"Configuration.{version_key}")
            _validate_optional_scalars(data[version_key], ("build",), str, f"Configuration.{version_key}")
    configuration = ensure_dict(data.get("configuration", {}), "Configuration.configuration")
    plugin_list = configuration.get("plugins", [])
    if not isinstance(plugin_list, list):
        raise ValueError("Configuration.configuration.plugins must be a list.")
    for index, plugin in enumerate(plugin_list):
        if not isinstance(plugin, dict):
            raise ValueError(f"Configuration.configuration.plugins[{index}] must be a dictionary.")
        core = ensure_dict(plugin.get("core", {}), f"Plugin[{index}].core")
        components = core.get("components", [])
        if not isinstance(components, list) or not all(isinstance(component, str) for component in components):
            raise ValueError(f"Plugin[{index}].core.components must be a list of strings.")
        cycle_timing = core.get("cycle timing", {})
        if not isinstance(cycle_timing, dict):
            raise ValueError(f"Plugin[{index}].core.cycle timing must be a dictionary.")
        _validate_optional_scalars(core, ("name",), str, f"Plugin[{index}].core")
        _validate_optional_scalars(cycle_timing, ("priority", "decimation", "offset"), int, f"Plugin[{index}].core.cycle timing")
        threads = plugin.get("threads", [])
        if not isinstance(threads, list):
            raise ValueError(f"Plugin[{index}].threads must be a list.")
        _validate_component_settings(plugin.get("component settings", []), f"Plugin[{index}].component settings")
        for thread_index, thread in enumerate(threads):
            _validate_thread_dict(thread, f"Plugin[{index}].threads[{thread_index}]")
    return data

def _validate_optional_scalars(data: dict, keys: tuple[str, ...], expected_type: type, context: str) -> None:
    for key in keys:
        if key in data and (type(data[key]) is not expected_type):
            raise ValueError(f"{context}.{key} must be a {expected_type.__name__}.")

def _validate_thread_dict(data: dict, context: str) -> None:
    data = ensure_dict(data, context)
    core = ensure_dict(data.get("core", {}), f"{context}.core")
    _validate_optional_scalars(core, ("processor", "priority offset"), int, f"{context}.core")
    _validate_component_settings(data.get("component settings", []), f"{context}.component settings")
    groups = data.get("transfer groups", [])
    if not isinstance(groups, list):
        raise ValueError(f"{context}.transfer groups must be a list.")
    for group_index, group in enumerate(groups):
        group_context = f"{context}.transfer groups[{group_index}]"
        group = ensure_dict(group, group_context)
        group_core = ensure_dict(group.get("core", {}), f"{group_context}.core")
        _validate_optional_scalars(group_core, ("name",), str, f"{group_context}.core")
        _validate_optional_scalars(group_core, ("direction", "timeout behavior"), int, f"{group_context}.core")
        if "direction" in group_core and group_core["direction"] not in (Direction.TX.value, Direction.RX.value):
            raise ValueError(f"{group_context}.core.direction must be 0 or 1.")
        timing = ensure_dict(group_core.get("cycle timing", {}), f"{group_context}.core.cycle timing")
        _validate_optional_scalars(timing, ("priority", "decimation", "offset"), int, f"{group_context}.core.cycle timing")
        _validate_optional_scalars(group_core, ("enable conversion",), bool, f"{group_context}.core")
        _validate_component_settings(group.get("component settings", []), f"{group_context}.component settings")
        transfers = group.get("transfers", [])
        if not isinstance(transfers, list):
            raise ValueError(f"{group_context}.transfers must be a list.")
        for transfer_index, transfer in enumerate(transfers):
            transfer_context = f"{group_context}.transfers[{transfer_index}]"
            transfer = ensure_dict(transfer, transfer_context)
            transfer_core = ensure_dict(transfer.get("core", {}), f"{transfer_context}.core")
            _validate_optional_scalars(transfer_core, ("name",), str, f"{transfer_context}.core")
            _validate_component_settings(transfer.get("component settings", []), f"{transfer_context}.component settings")
            channels = transfer.get("channels", [])
            if not isinstance(channels, list):
                raise ValueError(f"{transfer_context}.channels must be a list.")
            for channel_index, channel in enumerate(channels):
                channel_context = f"{transfer_context}.channels[{channel_index}]"
                channel = ensure_dict(channel, channel_context)
                channel_core = ensure_dict(channel.get("core", {}), f"{channel_context}.core")
                _validate_optional_scalars(channel_core, ("name", "units"), str, f"{channel_context}.core")
                _validate_optional_scalars(channel_core, ("engine data type", "string data type", "string offset"), int, f"{channel_context}.core")
                _validate_component_settings(channel.get("component settings", []), f"{channel_context}.component settings")

def _validate_component_settings(value, context: str) -> None:
    settings = ensure_list(value, context)
    for index, setting in enumerate(settings):
        setting_context = f"{context}[{index}]"
        setting = ensure_dict(setting, setting_context)
        _validate_optional_scalars(setting, ("component",), str, setting_context)
        values = ensure_list(setting.get("values", []), f"{setting_context}.values")
        for value_index, element in enumerate(values):
            element_context = f"{setting_context}.values[{value_index}]"
            element = ensure_dict(element, element_context)
            if "key" not in element or not isinstance(element["key"], str):
                raise ValueError(f"{element_context}.key must be a string.")

def _protocol_from_plugin_dict(plugin_data: dict) -> str:
    """Find a protocol marker in a plugin or its nested component settings."""
    core = ensure_dict(plugin_data.get("core", {}), "Plugin.core")
    components = ensure_list(core.get("components", []), "Plugin.core.components")
    if components:
        return str(components[0]).strip().upper()

    def nested_settings(value):
        if isinstance(value, dict):
            if value.get("component"):
                yield str(value["component"]).strip().upper()
            for child in value.values():
                yield from nested_settings(child)
        elif isinstance(value, list):
            for child in value:
                yield from nested_settings(child)

    candidates = list(nested_settings(plugin_data))
    return candidates[0] if candidates else ""

def _format_udp_ip_value(key: str, val):
    if key in ("source address", "destination address", "local address"):
        try:
            val_str = str(val)
            if val_str.isdigit() or (val_str.startswith("-") and val_str[1:].isdigit()):
                import socket, struct
                packed = struct.pack("!L", int(val_str))
                return socket.inet_ntoa(packed)
        except Exception:
            pass
    return val

def _format_dict_for_str(d):
    """Recursively copy dict d and convert UDP integer IP strings to IP format for human-readable display."""
    if isinstance(d, dict):
        new_d = {}
        component = d.get("component")
        for k, v in d.items():
            if k == "values" and component == "UDP" and isinstance(v, list):
                new_values = []
                for item in v:
                    if isinstance(item, dict) and item.get("key") in ("source address", "destination address", "local address"):
                        item_copy = dict(item)
                        item_copy["value"] = _format_udp_ip_value(item.get("key"), item.get("value"))
                        new_values.append(item_copy)
                    else:
                        new_values.append(_format_dict_for_str(item))
                new_d[k] = new_values
            else:
                new_d[k] = _format_dict_for_str(v)
        return new_d
    elif isinstance(d, list):
        return [_format_dict_for_str(item) for item in d]
    return d

class Element:
    """A key-value pair used inside :class:`ComponentSettings`."""

    def __init__(self, key: str, value) -> None:
        self.key = key
        self.value = value
        logger.debug("Initialized Element key='%s', value='%s'", self.key, self.value)

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value}

    def __str__(self) -> str:
        d = self.to_dict()
        if self.key in ("source address", "destination address", "local address"):
            d["value"] = _format_udp_ip_value(self.key, self.value)
        return json.dumps(d, indent=4)

    def import_from_dict(self, data: dict) -> None:
        data = ensure_dict(data, "Element")
        if "key" not in data:
            raise ValueError("Element is missing required field 'key'.")
        self.key = data.get("key")
        self.value = data.get("value")

    @classmethod
    def from_dict(cls, data: dict) -> "Element":
        obj = cls.__new__(cls)
        obj.import_from_dict(data)
        return obj

class ComponentSettings:
    """Component-specific settings stored as a list of :class:`Element` pairs."""

    def __init__(self, component: str = "", initial_elements: list[Element] | None = None) -> None:
        self.component = component
        self.elements = list(initial_elements) if initial_elements is not None else []
        logger.debug("Initialized ComponentSettings component='%s' (%d elements)", self.component, len(self.elements))

    def __str__(self) -> str:
        result = _format_dict_for_str(self.to_dict())
        return json.dumps(result, indent=4)

    def to_dict(self) -> dict:
        return {"component": self.component, "values": [v.to_dict() for v in self.elements]}

    def import_from_dict(self, data: dict) -> None:
        data = ensure_dict(data, "ComponentSettings")
        self.component = data.get("component", "")
        self.elements = [Element.from_dict(v) for v in ensure_list(data.get("values", []), "ComponentSettings.values")]

    @classmethod
    def from_dict(cls, data: dict) -> "ComponentSettings":
        obj = cls.__new__(cls)
        obj.import_from_dict(data)
        return obj

    def add_element(self, key: str, value) -> None:
        self.elements = [*self.elements, Element(key, value)]
        logger.info("Added Element key='%s', value='%s' to ComponentSettings('%s')", key, value, self.component)

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
        logger.debug("Initialized Channel name='%s', unit='%s'", self.name, self.unit)

    def __str__(self) -> str:
        result = _format_dict_for_str(self.to_dict())
        return json.dumps(result, indent=4)

    def to_dict(self) -> dict:
        return {
            "core": {
                "name": self.name,
                "units": self.unit,
                "engine data type": self.engine_data_type,
                "string data type": self.string_data_type,
                "string offset": self.string_offset,
            },
            "component settings": [cs.to_dict() for cs in self.component_settings],
        }

    def import_from_dict(self, data: dict) -> None:
        data = ensure_dict(data, "Channel")
        core = ensure_dict(data.get("core", {}), "Channel.core")
        self.name = core.get("name", "")
        self.unit = core.get("units", "")
        self.engine_data_type = core.get("engine data type", 2)
        self.string_data_type = core.get("string data type", 2)
        self.string_offset = core.get("string offset", 0)
        self.component_settings = [
            ComponentSettings.from_dict(cs)
            for cs in ensure_list(data.get("component settings", []), "Channel.component settings")
        ]

    @classmethod
    def from_dict(cls, data: dict) -> "Channel":
        obj = cls.__new__(cls)
        obj.import_from_dict(data)
        return obj

class Transfer:
    """A data transfer definition representing a packet payload.

    Contains local/destination address and port settings as well as a collection of Channel objects.
    """

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
        self.channels = list(channels) if channels is not None else []
        self.local_address = local_address
        self.local_port = local_port
        self.destination_address = destination_address
        self.destination_port = destination_port
        self.component_settings = [ComponentSettings()]

    def __str__(self, collapse: bool = True) -> str:
        result = self.to_dict()
        if collapse:
            result["channels"] = "[EMPTY]" if not self.channels else f"[...{len(self.channels)} channels...]"
        else:
            result["channels"] = [ch.to_dict() for ch in self.channels]
        result = _format_dict_for_str(result)
        return json.dumps(result, indent=4)

    def to_dict(self) -> dict:
        return {
            "core": {"name": self.name},
            "component settings": [cs.to_dict() for cs in self.component_settings],
            "channels": [ch.to_dict() for ch in self.channels],
        }

    def import_from_dict(self, data: dict) -> None:
        data = ensure_dict(data, "Transfer")
        core = ensure_dict(data.get("core", {}), "Transfer.core")
        self.name = core.get("name", "")
        self.local_address = ""
        self.local_port = 0
        self.destination_address = ""
        self.destination_port = 0
        self.component_settings = [
            ComponentSettings.from_dict(cs)
            for cs in ensure_list(data.get("component settings", []), "Transfer.component settings")
        ]
        for settings in self.component_settings:
            for element in settings.elements:
                if element.key in ("local address", "source address"):
                    self.local_address = str(element.value)
                elif element.key == "local port" or element.key == "source port":
                    self.local_port = int(element.value)
                elif element.key == "destination address":
                    self.destination_address = str(element.value)
                elif element.key == "destination port":
                    self.destination_port = int(element.value)
        channel_type = getattr(self, "_channel_type", Channel)
        self.channels = [channel_type.from_dict(ch) for ch in ensure_list(data.get("channels", []), "Transfer.channels")]

    @classmethod
    def from_dict(cls, data: dict) -> "Transfer":
        obj = cls.__new__(cls)
        obj.import_from_dict(data)
        return obj

    def add_channel(self, channel: Channel) -> None:
        """Add a channel to this transfer."""
        self.channels = [*self.channels, channel]
        logger.info("Added Channel('%s') to Transfer('%s')", channel.name, self.name)

class TransferGroup:
    """A group of transfers sharing execution timing parameters and a common direction (TX/RX)."""

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
        self.transfers = list(transfers) if transfers is not None else []
        self.component_settings = [ComponentSettings()]

    def __str__(self, collapse: bool = True) -> str:
        result = self.to_dict()
        result["core"]["direction"] = str(self.direction.name)
        if collapse:
            result["transfers"] = "[EMPTY]" if not self.transfers else f"[...{len(self.transfers)} transfers...]"
        else:
            result["transfers"] = [tr.to_dict() for tr in self.transfers]
        result = _format_dict_for_str(result)
        return json.dumps(result, indent=4)

    def to_dict(self) -> dict:
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
                "component settings": [cs.to_dict() for cs in self.component_settings],
                "transfers": [t.to_dict() for t in self.transfers],
                }

    @classmethod
    def from_dict(cls, data: dict) -> "TransferGroup":
        obj = cls.__new__(cls)
        obj.import_from_dict(data)
        return obj

    def import_from_dict(self, data: dict) -> None:
        data = ensure_dict(data, "TransferGroup")
        core = ensure_dict(data.get("core", {}), "TransferGroup.core")
        self.name = core.get("name", "")
        direction_value = core.get("direction", 0)
        try:
            self.direction = Direction(direction_value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"TransferGroup.core.direction must be 0 or 1, got {direction_value!r}.") from error
        
        cycle_timing = ensure_dict(core.get("cycle timing", {}), "TransferGroup.core.cycle timing")
        self.priority = cycle_timing.get("priority", 100)
        self.decimation = cycle_timing.get("decimation", 1)
        self.offset = cycle_timing.get("offset", 0)
        self.timeout_behaviour = core.get("timeout behavior", 0)
        self.enable_conversion = core.get("enable conversion", False)
        self.component_settings = [
            ComponentSettings.from_dict(cs)
            for cs in ensure_list(data.get("component settings", []), "TransferGroup.component settings")
        ]
        transfer_type = getattr(self, "_transfer_type", Transfer)
        self.transfers = [transfer_type.from_dict(t) for t in ensure_list(data.get("transfers", []), "TransferGroup.transfers")]

    def add_transfer(self, transfer: Transfer) -> None:
        """Add a transfer to this transfer group."""
        self.transfers = [*self.transfers, transfer]
        logger.info("Added Transfer('%s') to TransferGroup('%s')", transfer.name, self.name)

class Thread:
    """An execution thread definition binding transfer groups to a target CPU core/processor."""

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
        result = self.to_dict()
        if collapse:
            result["transfer groups"] = "[EMPTY]" if not self.transfer_groups else f"[...{len(self.transfer_groups)} transfer groups...]"
        else:
            result["transfer groups"] = [tg.to_dict() for tg in self.transfer_groups]
        result = _format_dict_for_str(result)
        return json.dumps(result, indent=4)

    def to_dict(self) -> dict:
        return {
            "core": {
                "processor": self.processor,
                "priority offset": self.priority_offset,
            },
            "component settings": [cs.to_dict() for cs in self.component_settings],
            "transfer groups": [tg.to_dict() for tg in self.transfer_groups],
        }

    def import_from_dict(self, data: dict) -> None:
            data = ensure_dict(data, "Thread")
            core = ensure_dict(data.get("core", {}), "Thread.core")
            self.processor = core.get("processor", -2)
            self.priority_offset = core.get("priority offset", 0)
            self.component_settings = [
                ComponentSettings.from_dict(cs)
                for cs in ensure_list(data.get("component settings", []), "Thread.component settings")
            ]
            transfer_group_type = getattr(self, "_transfer_group_type", TransferGroup)
            self.transfer_groups = [
                transfer_group_type.from_dict(tg)
                for tg in ensure_list(data.get("transfer groups", []), "Thread.transfer groups")
            ]

    @classmethod
    def from_dict(cls, data: dict) -> "Thread":
        obj = cls.__new__(cls)
        obj.import_from_dict(data)
        return obj

    def add_transfer_group(self, transfer_group: TransferGroup) -> None:
        """Add a transfer group to this thread."""
        self.transfer_groups = [*self.transfer_groups, transfer_group]
        logger.info("Added TransferGroup('%s') to Thread(processor=%d)", transfer_group.name, self.processor)

class Plugin:
    """A transport plugin container holding execution threads for a specific protocol."""

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
        self.threads = list(threads) if threads is not None else []
        self.components = []
        self.component_settings = [ComponentSettings()]

    def __str__(self, collapse: bool = True) -> str:
        result = self.to_dict()
        if collapse:
            result["threads"] = "[EMPTY]" if not self.threads else f"[...{len(self.threads)} threads...]"
        else:
            result["threads"] = [th.to_dict() for th in self.threads]
        result = _format_dict_for_str(result)
        return json.dumps(result, indent=4)

    def to_dict(self) -> dict:
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
            "component settings": [cs.to_dict() for cs in self.component_settings],
            "threads": [th.to_dict() for th in self.threads],
        }

    def import_from_dict(self, data: dict) -> None:
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
        thread_type = getattr(self, "_thread_type", Thread)
        self.threads = [thread_type.from_dict(th) for th in ensure_list(data.get("threads", []), "Plugin.threads")]

    @classmethod
    def from_dict(cls, data: dict) -> "Plugin":
        obj = cls.__new__(cls)
        obj.import_from_dict(data)
        return obj

    def add_thread(self, thread: Thread) -> None:
        """Add a thread to this plugin."""
        self.threads = [*self.threads, thread]
        logger.info("Added Thread(processor=%d) to Plugin('%s')", thread.processor, self.name)

class Configuration:
    """The root configuration object representing a complete .dsf configuration file."""

    def __init__(self,
                 plugins: list[Plugin] | None = None,
                 dsfversion: dict | None = None,
                 version: dict | None = None,
        ) -> None:
            self.dsfversion = dsfversion if dsfversion is not None else {"major": 1, "minor": 4, "fix": 0, "build": ""}
            self.version = version if version is not None else {"major": 1, "minor": 0, "fix": 0, "build": ""}
            self.plugins = plugins if plugins is not None else []

    def __str__(self, collapse: bool = True) -> str:
            result = self.to_dict()
            if collapse:
                result["configuration"]["plugins"] = "[EMPTY]" if not self.plugins else f"[...{len(self.plugins)} plugins...]"
            else:
                result["configuration"]["plugins"] = [pl.to_dict() for pl in self.plugins]
            result = _format_dict_for_str(result)
            return json.dumps(result, indent=4)

    def to_dict(self) -> dict:
        return {
            "dsfversion": self.dsfversion,
            "version": self.version,
            "configuration": {
                "plugins": [pl.to_dict() for pl in self.plugins],
            },
        }

    def import_from_dict(self, data: dict) -> None:
        data = validate_configuration_dict(data)
        self.dsfversion = data.get("dsfversion", {"major": 1, "minor": 4, "fix": 0, "build": ""})
        self.version = data.get("version", {"major": 1, "minor": 0, "fix": 0, "build": ""})
        configuration = ensure_dict(data.get("configuration", {}), "Configuration.configuration")
        plugin_type = getattr(self, "_plugin_type", Plugin)
        plugin_data_list = ensure_list(configuration.get("plugins", []), "Configuration.plugins")
        self.plugins = []
        if plugin_type is not Plugin:
            self.plugins = [plugin_type.from_dict(plugin_data) for plugin_data in plugin_data_list]
        else:
            from data_sharing_framework_config_api.protocol_factory import ProtocolFactory

            for index, plugin_data in enumerate(plugin_data_list):
                protocol = _protocol_from_plugin_dict(plugin_data)
                if not protocol:
                    self.plugins.append(Plugin.from_dict(plugin_data))
                    continue
                try:
                    handler = ProtocolFactory.get_handler(protocol)
                except ValueError as error:
                    raise ValueError(f"Unsupported protocol '{protocol}' in plugin {index}.") from error
                plugin = handler.plugin_cls.from_dict(plugin_data)
                if not getattr(plugin, "components", None):
                    plugin.components = [protocol]
                self.plugins.append(plugin)
        logger.info("Imported Configuration from dict containing %d plugins", len(self.plugins))

    @classmethod
    def from_dict(cls, data: dict) -> "Configuration":
        obj = cls.__new__(cls)
        obj.import_from_dict(data)
        return obj

    def add_plugin(self, plugin: Plugin) -> None:
        """Add a plugin to this configuration."""
        self.plugins = [*self.plugins, plugin]
        logger.info("Added Plugin('%s') to Configuration", plugin.name)

def get_version() -> dict:
    """Return the current RDMA definition format version."""
    return {"major": 3, "minor": 0, "fix": 0, "build": ""}


if __name__ == "__main__":
    print(json.dumps(get_version(), indent=4))