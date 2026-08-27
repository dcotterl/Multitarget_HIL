"""UDP configuration definitions for the data-sharing framework.

This module defines the concrete objects used to represent a UDP configuration
in the same tree hierarchy expected by the serialized framework configuration:

    Configuration
      └── Plugin [1..n]
           └── Thread [1..n]
                └── TransferGroup [1..n]
                     └── Transfer [1..n]
                          └── Channel [1..n]

The classes here inherit from the base model types in ``definitions.py`` and
provide UDP-specific component settings and IP address serialization utilities
(converting dotted IPv4 strings to/from 32-bit integer representations).
"""

from __future__ import annotations

import socket
import struct

import json
import logging
from enum import Enum
from typing import Iterable, TypeVar

try:
    from . import definitions as d
except ImportError:  # pragma: no cover
    import definitions as d 


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

T = TypeVar("T")

def ip_to_string(ip_address: str) -> str:
    """Convert an IPv4 address string (e.g. '127.0.0.1') into its integer
    representation as a string (e.g. '2130706433')."""
    if ip_address == "":
        ip_address = "127.0.0.1"
    packed = socket.inet_aton(ip_address)
    return str(struct.unpack("!L", packed)[0])


def string_to_ip(int_string: str) -> str:
    """Convert an integer string (e.g. '2130706433') back into its IPv4
    address representation (e.g. '127.0.0.1')."""
    packed = struct.pack("!L", int(int_string))
    return socket.inet_ntoa(packed)

class Channel(d.Channel):
    """A UDP channel definition and its serialized settings."""

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

class Transfer(d.Transfer):
    """A UDP data transfer configuration."""

    def __init__(
        self,
        name: str = "",
        channels: list[Channel] | None = None,
        local_address: str = "",
        local_port: int = 0,
        destination_address: str = "",
        destination_port: int = 0,
    ) -> None:
        super().__init__(
            name=name,
            channels=channels if channels is not None else [],
            local_address=local_address,
            local_port=local_port,
            destination_address=destination_address,
            destination_port=destination_port,
        )
        elements = [
            d.Element("source address" if self.local_address != "" else "destination address", 
                    ip_to_string(self.local_address) if self.local_address != "" else ip_to_string(self.destination_address)),
            d.Element("source port" if self.local_port != 0 else "destination port", 
                    str(self.local_port) if self.local_port != 0 else str(self.destination_port)),
        ]
        self.component_settings = [d.ComponentSettings("UDP", elements)]

    def __str__(self, collapse: bool = True) -> str:
        result = self.getDict()
        for setting in result.get("component settings", []):
            if setting.get("component") == "UDP":
                for val in setting.get("values", []):
                    if val.get("key") in ("source address", "destination address", "local address"):
                        try:
                            val["value"] = string_to_ip(val["value"])
                        except Exception:
                            pass
        if collapse:
            result["channels"] = "[EMPTY]" if not self.channels else f"[...{len(self.channels)} channels...]"
        else:
            result["channels"] = [ch.getDict() for ch in self.channels]
        return json.dumps(result, indent=4)

class TransferGroup(d.TransferGroup):
    """A group of UDP transfers sharing a common direction (TX/RX)."""

    def __init__(
        self,
        name: str = "",
        direction: d.Direction = d.Direction.TX,
        priority: int = 100,
        decimation: int = 1,
        offset: int = 0,
        timeout_behaviour: int = 0,
        enable_conversion: bool = False,
        transfers: list[Transfer] | None = None,
    ) -> None:
        super().__init__(
            name=name,
            direction=direction,
            priority=priority,
            decimation=decimation,
            offset=offset, 
            timeout_behaviour=timeout_behaviour,
            enable_conversion=enable_conversion,
            transfers=transfers,
        )
        self.component_settings = []

class Thread(d.Thread):
    """A thread configuration for UDP operations."""

    def __init__(
        self,
        processor: int = -2,
        priority_offset: int = 0,
        transfer_groups: list[TransferGroup] | None = None,
        local_address: str = "127.0.0.1",
        local_port: int = 0,
    ) -> None:
        super().__init__(
            processor=processor,
            priority_offset=priority_offset,
        )
        self.component_settings = [d.ComponentSettings("UDP", 
                                                     [d.Element("local port", str(local_port)),
                                                      d.Element("local address", ip_to_string(local_address)),
                                                      ])]
        self.local_address = local_address
        self.local_port = local_port
        self.transfer_groups = transfer_groups if transfer_groups is not None else []

    def __str__(self, collapse: bool = True) -> str:
        result = self.getDict()
        for setting in result.get("component settings", []):
            if setting.get("component") == "UDP":
                for val in setting.get("values", []):
                    if val.get("key") in ("local address", "source address", "destination address"):
                        try:
                            val["value"] = string_to_ip(val["value"])
                        except Exception:
                            pass
        if collapse:
            result["transfer groups"] = "[EMPTY]" if not self.transfer_groups else f"[...{len(self.transfer_groups)} transfer groups...]"
        else:
            result["transfer groups"] = [tg.getDict() for tg in self.transfer_groups]
        return json.dumps(result, indent=4)

    @classmethod
    def from_dict(cls, data: dict) -> Thread:
        """Populate the Thread object from a dictionary."""
        instance = super().from_dict(data)  # Note: This should ideally be cls.from_dict(data) if the superclass method is also a classmethod.
        for setting in instance.component_settings:
            if setting.component == "UDP":
                for element in setting.elements:
                    if element.key == "local port":
                        instance.local_port = int(element.value)
                    elif element.key == "local address":
                        instance.local_address = string_to_ip(element.value)
        return instance

class Plugin(d.Plugin):
    """A UDP plugin containing one or more threads."""

    def __init__(
        self,
        name: str = "",
        priority: int = 10000,
        decimation: int = 1,
        offset: int = 0,
        threads: list[Thread] | None = None,
    ) -> None:
        super().__init__(
            name=name,
            priority=priority,
            decimation=decimation,
            offset=offset,
            threads=threads if threads is not None else [],
        )
        self.components = ["UDP"]
        self.component_settings = []


if __name__ == "__main__":
    # Example usage
    ip = "127.0.0.2"
    int_str = ip_to_string(ip)
    print(f"IP address {ip} as integer string: {int_str}")
    ip_converted_back = string_to_ip(int_str)
    print(f"Integer string {int_str} converted back to IP address: {ip_converted_back}")