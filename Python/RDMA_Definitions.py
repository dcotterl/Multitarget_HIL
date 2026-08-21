"""RDMA definition model and JSON serializer.

This module provides lightweight classes for constructing an RDMA
configuration in the same hierarchy used by the serialized definition:

# Hierarchy of templates:
#    config file
#        plugin [1..n]
#            thread [1..n]
#                transfer group [1..n]
#                    transfer [1..n]
#                        channel [1..n]

Each object stores its definition as a dictionary, exposes it through
``getDict()``, and can be rendered as formatted JSON with ``str()``.
``ComponentSettings`` stores component-specific settings used by channels,
transfers, transfer groups, threads, and plugins.  ``Direction`` identifies
transfers and transfer groups as transmit (TX) or receive (RX); a transfer
group rejects transfers with a different direction.

Deprecated aliases ``element``, ``component_settings``, ``channel``,
``transfer``, ``transferGroup``, ``thread``, ``plugin`` are provided for
backwards compatibility and will be removed in a future release.
"""

import json
from enum import Enum
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Direction(Enum):
    """Direction of an RDMA transfer."""
    TX = 0
    RX = 1


class Element:
    """A key-value pair used inside :class:`ComponentSettings`."""

    def __init__(self, key: str, value) -> None:
        """Create a key-value pair for component settings."""
        self.key = key
        self.value = value

    def getDict(self) -> dict:
        """Return the key-value pair as a dictionary."""
        return {"key": self.key, "value": self.value}

    def __str__(self) -> str:
        """Return the key-value pair as a formatted JSON string."""
        return json.dumps(self.getDict(), indent=4)

    def importFromDict(self, data: dict) -> None:
        """Import the key-value pair from a dictionary."""
        self.key = data.get("key")
        self.value = data.get("value")

    @classmethod
    def from_dict(cls, data: dict) -> "Element":
        """Construct an :class:`Element` from a serialized dictionary."""
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj


class ComponentSettings:
    """Component-specific settings stored as a list of :class:`Element` pairs."""

    def __init__(self, component: str = "", initial_elements: list[Element] = None) -> None:
        """Create settings for *component* with optional initial values."""
        self.component = component
        self.elements: list[Element] = initial_elements if initial_elements is not None else []

    def __str__(self) -> str:
        """Return the settings as formatted JSON."""
        return json.dumps(self.getDict(), indent=4)

    def getDict(self) -> dict:
        """Return the component settings dictionary."""
        return {"component": self.component, "values": [v.getDict() for v in self.elements]}

    def importFromDict(self, data: dict) -> None:
        """Import the component settings from a dictionary."""
        self.component = data.get("component", "")
        self.elements = [Element(v.get("key"), v.get("value")) for v in data.get("values", [])]

    @classmethod
    def from_dict(cls, data: dict) -> "ComponentSettings":
        """Construct a :class:`ComponentSettings` from a serialized dictionary."""
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

    def addElement(self, key: str, value) -> None:
        """Add a key-value pair to the settings."""
        self.elements.append(Element(key, value))


class Channel:
    """An RDMA channel definition and its serialized settings."""

    def __init__(
        self,
        name: str = "",
        unit: str = "",
        engine_data_type: int = 2,
        string_data_type: int = 2,
        string_offset: int = 0,
        protocol: str = "",
    ) -> None:
        """Initialize a channel.

        Args:
            name: Channel name.
            unit: Engineering unit string for the channel.
            engine_data_type: Numeric engine-side data type identifier.
            string_data_type: Numeric string-side data type identifier.
            string_offset: String table offset for this channel.
            protocol: Protocol name used for initial component settings.
        """
        self.name = name
        self.unit = unit
        self.engine_data_type = engine_data_type
        self.string_data_type = string_data_type
        self.string_offset = string_offset
        self.component_settings: list[ComponentSettings] = [ComponentSettings(protocol)]

    def __str__(self) -> str:
        """Return a formatted JSON string representation of the channel."""
        return json.dumps(self.getDict(), indent=4)

    def getDict(self) -> dict:
        """Return the channel as a dictionary for serialization or composition."""
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
        """Import the channel definition from a dictionary."""
        core = data.get("core", {})
        self.name = core.get("name", "")
        self.unit = core.get("units", "")
        self.engine_data_type = core.get("engine data type", 2)
        self.string_data_type = core.get("string data type", 2)
        self.string_offset = core.get("string offset", 0)
        self.component_settings = []
        for cs in data.get("component settings", []):
            self.component_settings.append(ComponentSettings.from_dict(cs))

    @classmethod
    def from_dict(cls, data: dict) -> "Channel":
        """Construct a :class:`Channel` from a serialized dictionary."""
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

    def addComponentSetting(self, component_setting: ComponentSettings) -> None:
        """Add a component setting to this channel's list."""
        self.component_settings.append(component_setting)


class Transfer:
    """An RDMA data transfer configuration with direction-specific settings.

    Manages TX (transmit) or RX (receive) transfers with associated
    channels and network parameters.
    """

    def __init__(
        self,
        direction: Direction = Direction.TX,
        protocol: str = "",
        name: str = "",
        channels: list[Channel] = None,
        local_address: str = "",
        local_port: int = 0,
        destination_address: str = "",
        destination_port: int = 0,
    ) -> None:
        """Initialize a transfer with direction and network settings.

        Args:
            direction: Direction enum (TX or RX) specifying transfer direction.
            protocol: Protocol name used for initial component settings.
            name: String name identifier for this transfer.
            channels: List of :class:`Channel` objects to include.
            local_address: Local network address (IP or hostname).
            local_port: Local port number for the transfer.
            destination_address: Remote address for TX transfers (ignored for RX).
            destination_port: Remote port for TX transfers (ignored for RX).
        """
        self.direction = direction
        self.name = name
        self.channels: list[Channel] = channels if channels is not None else []
        elements = [
            Element("local address", str(local_address)),
            Element("local port", str(local_port)),
        ]
        self.component_settings: list[ComponentSettings] = [ComponentSettings(protocol, elements)]
        if self.direction == Direction.TX:
            self.component_settings[0].addElement("destination address", str(destination_address))
            self.component_settings[0].addElement("destination port", str(destination_port))

    def __str__(self) -> str:
        """Return a formatted JSON string representation of the transfer."""
        result = self.getDict()
        result["channels"] = "[EMPTY]" if not self.channels else f"[...{len(self.channels)} channels...]"
        return json.dumps(result, indent=4)

    def getDict(self) -> dict:
        """Return the transfer configuration as a dictionary for serialization."""
        return {
            "core": {"name": self.name},
            "component settings": [cs.getDict() for cs in self.component_settings],
            "channels": [ch.getDict() for ch in self.channels],
        }

    def importFromDict(self, data: dict) -> None:
        """Import the transfer configuration from a dictionary."""
        core = data.get("core", {})
        self.name = core.get("name", "")
        self.component_settings = []
        for cs in data.get("component settings", []):
            self.component_settings.append(ComponentSettings.from_dict(cs))
        self.channels = []
        for ch in data.get("channels", []):
            self.channels.append(Channel.from_dict(ch))
        elements = self.component_settings[0].elements if self.component_settings else []
        if "destination address" in [e.key for e in elements]:
            self.direction = Direction.TX
        else:
            self.direction = Direction.RX

    @classmethod
    def from_dict(cls, data: dict) -> "Transfer":
        """Construct a :class:`Transfer` from a serialized dictionary."""
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

    def addChannel(self, channel: Channel) -> None:
        """Add a channel to the transfer's channel list."""
        self.channels.append(channel)

    def addElement(self, key: str, value) -> None:
        """Add a key-value pair to the transfer's first component settings entry."""
        if self.component_settings:
            self.component_settings[0].elements.append(Element(key, value))
        else:
            logger.warning("No component settings available to add element.")

    def addComponentSetting(self, component_setting: ComponentSettings) -> None:
        """Add a component setting to the transfer's component settings list."""
        self.component_settings.append(component_setting)


class TransferGroup:
    """A group of transfers sharing a common direction.

    Groups multiple :class:`Transfer` objects that share the same direction
    (TX or RX) and manages their configuration including cycle timing and
    component settings.
    """

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
        transfers: list[Transfer] = None,
    ) -> None:
        """Initialize a transfer group.

        Args:
            name: Human-readable name for the transfer group.
            direction: Transfer direction for all grouped transfers.
            priority: Scheduling priority used in the group cycle timing.
            decimation: Sample decimation factor for the group.
            offset: Time offset for the group cycle timing.
            timeout_behaviour: Timeout handling behavior configuration.
            enable_conversion: Whether data conversion is enabled.
            protocol: Protocol name used for initial component settings.
            transfers: List of :class:`Transfer` instances assigned to the group.
        """
        self.name = name
        self.direction = direction
        self.priority = priority
        self.decimation = decimation
        self.offset = offset
        self.timeout_behaviour = timeout_behaviour
        self.enable_conversion = enable_conversion
        self.component_settings: list[ComponentSettings] = [ComponentSettings(protocol)]
        self.transfers: list[Transfer] = transfers if transfers is not None else []

    def __str__(self) -> str:
        """Return a formatted JSON string representation of the transfer group."""
        result = self.getDict()
        result["transfers"] = "[EMPTY]" if not self.transfers else f"[...{len(self.transfers)} transfers...]"
        return json.dumps(result, indent=4)

    def getDict(self) -> dict:
        """Return the transfer group configuration dictionary."""
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
        """Import the transfer group configuration from a dictionary."""
        core = data.get("core", {})
        self.name = core.get("name", "")
        self.direction = Direction(core.get("direction", 0))
        cycle_timing = core.get("cycle timing", {})
        self.priority = cycle_timing.get("priority", 100)
        self.decimation = cycle_timing.get("decimation", 1)
        self.offset = cycle_timing.get("offset", 0)
        self.timeout_behaviour = core.get("timeout behavior", 0)
        self.enable_conversion = core.get("enable conversion", False)
        self.component_settings = []
        for cs in data.get("component settings", []):
            self.component_settings.append(ComponentSettings.from_dict(cs))
        self.transfers = []
        for t in data.get("transfers", []):
            self.transfers.append(Transfer.from_dict(t))

    @classmethod
    def from_dict(cls, data: dict) -> "TransferGroup":
        """Construct a :class:`TransferGroup` from a serialized dictionary."""
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

    def addTransfer(self, transfer: Transfer) -> None:
        """Add a transfer to the group."""
        self.transfers.append(transfer)


class Thread:
    """A thread configuration for RDMA operations.

    Encapsulates thread settings including core configuration,
    component settings, and associated transfer groups.
    """

    def __init__(
        self,
        processor: int = -2,
        priority_offset: int = 0,
        protocol: str = "",
        transfer_groups: list[TransferGroup] = None,
    ) -> None:
        self.processor = processor
        self.priority_offset = priority_offset
        self.component_settings: list[ComponentSettings] = [ComponentSettings(protocol)]
        self.transfer_groups: list[TransferGroup] = transfer_groups if transfer_groups is not None else []

    def __str__(self) -> str:
        """Return a JSON string representation of this thread."""
        result = self.getDict()
        result["transfer groups"] = (
            "[EMPTY]" if not self.transfer_groups
            else f"[...{len(self.transfer_groups)} transfer groups...]"
        )
        return json.dumps(result, indent=4)

    def getDict(self) -> dict:
        """Return the thread configuration dictionary."""
        return {
            "core": {
                "processor": self.processor,
                "priority offset": self.priority_offset,
            },
            "component settings": [cs.getDict() for cs in self.component_settings],
            "transfer groups": [tg.getDict() for tg in self.transfer_groups],
        }

    def importFromDict(self, data: dict) -> None:
        """Import the thread configuration from a dictionary."""
        core = data.get("core", {})
        self.processor = core.get("processor", -2)
        self.priority_offset = core.get("priority offset", 0)
        self.component_settings = []
        for cs in data.get("component settings", []):
            self.component_settings.append(ComponentSettings.from_dict(cs))
        self.transfer_groups = []
        for tg in data.get("transfer groups", []):
            self.transfer_groups.append(TransferGroup.from_dict(tg))

    @classmethod
    def from_dict(cls, data: dict) -> "Thread":
        """Construct a :class:`Thread` from a serialized dictionary."""
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

    def addTransferGroup(self, transfer_group: TransferGroup) -> None:
        """Add a transfer group to the thread's list."""
        self.transfer_groups.append(transfer_group)


class Plugin:
    """An RDMA plugin containing one or more threads."""

    def __init__(
        self,
        name: str = "",
        protocol: str = "",
        priority: int = 10000,
        decimation: int = 1,
        offset: int = 0,
        threads: list[Thread] = None,
    ) -> None:
        self.name = name
        self.components: list[str] = [protocol]
        self.priority = priority
        self.decimation = decimation
        self.offset = offset
        self.threads: list[Thread] = threads if threads is not None else []
        self.component_settings: list[ComponentSettings] = [ComponentSettings(protocol)]

    def __str__(self) -> str:
        result = self.getDict()
        result["threads"] = "[EMPTY]" if not self.threads else f"[...{len(self.threads)} threads...]"
        return json.dumps(result, indent=4)

    def getDict(self) -> dict:
        """Return the plugin configuration dictionary."""
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
        """Import the plugin configuration from a dictionary."""
        core = data.get("core", {})
        self.name = core.get("name", "")
        self.components = core.get("components", [])
        cycle_timing = core.get("cycle timing", {})
        self.priority = cycle_timing.get("priority", 10000)
        self.decimation = cycle_timing.get("decimation", 1)
        self.offset = cycle_timing.get("offset", 0)
        self.component_settings = []
        for cs in data.get("component settings", []):
            self.component_settings.append(ComponentSettings.from_dict(cs))
        self.threads = []
        for th in data.get("threads", []):
            self.threads.append(Thread.from_dict(th))

    @classmethod
    def from_dict(cls, data: dict) -> "Plugin":
        """Construct a :class:`Plugin` from a serialized dictionary."""
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

    def addThread(self, thread: Thread) -> None:
        """Add a thread to the plugin's list."""
        self.threads.append(thread)


class RDMA_Configuration:
    """Top-level RDMA configuration containing one or more plugins."""

    def __init__(
        self,
        plugins: list[Plugin] = None,
        dsfversion: dict = None,
        version: dict = None,
    ) -> None:
        """Initialize the RDMA Configuration.

        Args:
            plugins: List of :class:`Plugin` objects. Defaults to empty list.
            dsfversion: DSF format version metadata dict with keys
                ``major``, ``minor``, ``fix``, and ``build``.
                Defaults to version 1.4.0.
            version: RDMA specification version metadata dict with keys
                ``major``, ``minor``, ``fix``, and ``build``.
                Defaults to version 1.0.0.
        """
        self.dsfversion = dsfversion if dsfversion is not None else {"major": 1, "minor": 4, "fix": 0, "build": ""}
        self.version = version if version is not None else {"major": 1, "minor": 0, "fix": 0, "build": ""}
        self.plugins: list[Plugin] = plugins if plugins is not None else []

    def getDict(self) -> dict:
        """Return the RDMA configuration as a dictionary suitable for JSON export."""
        return {
            "dsfversion": self.dsfversion,
            "version": self.version,
            "configuration": {
                "plugins": [pl.getDict() for pl in self.plugins],
            },
        }

    def importFromDict(self, data: dict) -> None:
        """Populate this instance from a serialized configuration dictionary."""
        self.dsfversion = data.get("dsfversion", {"major": 1, "minor": 4, "fix": 0, "build": ""})
        self.version = data.get("version", {"major": 1, "minor": 0, "fix": 0, "build": ""})
        configuration = data.get("configuration", {})
        self.plugins = []
        for pl in configuration.get("plugins", []):
            self.plugins.append(Plugin.from_dict(pl))

    @classmethod
    def from_dict(cls, data: dict) -> "RDMA_Configuration":
        """Construct an :class:`RDMA_Configuration` from a serialized dictionary."""
        obj = cls.__new__(cls)
        obj.importFromDict(data)
        return obj

    def addPlugin(self, plugin: Plugin) -> None:
        """Add a plugin to the configuration."""
        self.plugins.append(plugin)

    def __str__(self) -> str:
        """Return the configuration as an indented JSON string."""
        result = self.getDict()
        result["configuration"]["plugins"] = (
            "[EMPTY]" if not self.plugins
            else f"[...{len(self.plugins)} plugins...]"
        )
        return json.dumps(result, indent=4)


def get_version() -> dict:
    """Return the current RDMA definition format version."""
    return {"major": 2, "minor": 0, "fix": 0, "build": ""}


# ---------------------------------------------------------------------------
# Backwards-compatibility aliases (deprecated — use PascalCase names above)
# ---------------------------------------------------------------------------
element = Element
component_settings = ComponentSettings
channel = Channel
transfer = Transfer
transferGroup = TransferGroup
thread = Thread
plugin = Plugin


if __name__ == "__main__":
    print(f"RDMA definition format version: {get_version()}")
