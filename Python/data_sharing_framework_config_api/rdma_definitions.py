"""RDMA configuration definitions for the data-sharing framework.

This module defines the concrete objects used to represent an RDMA
configuration in the same hierarchy expected by the serialized framework
configuration:

    config
      plugin [1..n]
        thread [1..n]
          transfer group [1..n]
            transfer [1..n]
              channel [1..n]

The classes here are thin extensions of the base model types in
``definitions.py``. They maintain the framework's tree structure while
adding the RDMA-specific component settings needed for configuration
serialization.

The objects expose their data through the base ``getDict()`` interface and
can be rendered as formatted JSON via ``str()``. ``Direction`` marks a
transfer group as transmit (TX) or receive (RX), while each component stores
its own settings via ``ComponentSettings``.

This module intentionally focuses on the RDMA plugin model and does not
implement transport behavior itself; it only builds and serializes the
configuration metadata.
"""

from __future__ import annotations


import logging

from typing import TypeVar

try:
    from . import definitions as d
except ImportError:  # pragma: no cover
    import definitions as d 

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

T = TypeVar("T")

class Channel(d.Channel):
    """An RDMA channel configuration."""

    def __init__(self,
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
            self.component_settings = [d.ComponentSettings("RDMA")]

class Transfer(d.Transfer):
    """An RDMA data transfer configuration."""

    def __init__(
        self,
        name: str = "",
        channels: list[d.Channel] | None = None,
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

        # build component settings for the transfer based on the local and destination addresses and ports
        elements = [
            d.Element("local address", str(self.local_address)),
            d.Element("local port", str(self.local_port)),
        ]
        if self.destination_address != "" :
            elements.append(d.Element("destination address", str(self.destination_address)))
            elements.append(d.Element("destination port", str(self.destination_port)))
        self.component_settings = [d.ComponentSettings("RDMA", elements)]

class TransferGroup(d.TransferGroup):
    """A group of transfers sharing a common direction."""

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

        self.component_settings = [d.ComponentSettings("RDMA")]

class Thread(d.Thread):
    """A thread configuration for RDMA operations."""

    def __init__(
        self,
        processor: int = -2,
        priority_offset: int = 0,
        transfer_groups: list[TransferGroup] | None = None,
    ) -> None:
        super().__init__(
            processor=processor,
            priority_offset=priority_offset,
            transfer_groups=transfer_groups if transfer_groups is not None else [],
        )
        self.component_settings = [d.ComponentSettings("RDMA")]

class Plugin(d.Plugin):
    """An RDMA plugin containing one or more threads."""

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
        self.components = ["RDMA"]
        self.component_settings = [d.ComponentSettings("RDMA")]


if __name__ == "__main__":
    print(f"here is the module {__name__} for RDMA configuration definitions")
