"""Protocol Factory and Registry for Data Sharing Framework objects.

This module decouples protocol-specific object creation from GUI code, allowing new protocols 
(e.g., Shared Memory, TCP, CAN) to be added easily by registering their definition modules.
"""

from __future__ import annotations

from typing import Any, Type

from data_sharing_framework_config_api import definitions, rdma_definitions, udp_definitions


class ProtocolHandler:
    """Encapsulates creation factory methods for a specific protocol."""

    def __init__(
        self,
        protocol_name: str,
        plugin_cls: Type[definitions.Plugin],
        thread_cls: Type[definitions.Thread],
        transfer_group_cls: Type[definitions.TransferGroup],
        transfer_cls: Type[definitions.Transfer],
        channel_cls: Type[definitions.Channel],
        default_rx_port: int = 0,
        default_tx_port: int = 5000,
    ) -> None:
        self.protocol_name = protocol_name
        self.plugin_cls = plugin_cls
        self.thread_cls = thread_cls
        self.transfer_group_cls = transfer_group_cls
        self.transfer_cls = transfer_cls
        self.channel_cls = channel_cls
        self.default_rx_port = default_rx_port
        self.default_tx_port = default_tx_port

    def create_plugin(self, name: str = "", threads: list[definitions.Thread] | None = None) -> definitions.Plugin:
        return self.plugin_cls(name=name, threads=threads if threads is not None else [])

    def create_thread(
        self, processor: int = -2, transfer_groups: list[definitions.TransferGroup] | None = None
    ) -> definitions.Thread:
        return self.thread_cls(processor=processor, transfer_groups=transfer_groups if transfer_groups is not None else [])

    def create_transfer_group(
        self,
        name: str = "",
        direction: definitions.Direction = definitions.Direction.TX,
        transfers: list[definitions.Transfer] | None = None,
    ) -> definitions.TransferGroup:
        return self.transfer_group_cls(
            name=name, direction=direction, transfers=transfers if transfers is not None else []
        )

    def create_transfer(
        self,
        name: str = "",
        direction: definitions.Direction = definitions.Direction.TX,
        channels: list[definitions.Channel] | None = None,
    ) -> definitions.Transfer:
        channels_list = channels if channels is not None else []

        if self.protocol_name == "UDP":
            if direction == definitions.Direction.RX:
                return self.transfer_cls(
                    name=name, channels=channels_list, local_address="127.0.0.1", local_port=self.default_tx_port
                )
            elif direction == definitions.Direction.TX:
                return self.transfer_cls(
                    name=name, channels=channels_list, destination_address="127.0.0.1", destination_port=self.default_tx_port
                )
            return self.transfer_cls(name=name, channels=channels_list)

        # Default / RDMA behavior
        if direction == definitions.Direction.RX:
            return self.transfer_cls(
                name=name, channels=channels_list, local_address="127.0.0.1", local_port=self.default_rx_port
            )
        elif direction == definitions.Direction.TX:
            return self.transfer_cls(
                name=name,
                channels=channels_list,
                local_address="127.0.0.1",
                local_port=self.default_rx_port,
                destination_address="127.0.0.1",
                destination_port=self.default_rx_port,
            )
        return self.transfer_cls(name=name, channels=channels_list)

    def create_channel(self, name: str = "", unit: str = "") -> definitions.Channel:
        return self.channel_cls(name=name, unit=unit)


class ProtocolFactory:
    """Registry managing available protocol handlers."""

    _registry: dict[str, ProtocolHandler] = {}

    @classmethod
    def register(cls, handler: ProtocolHandler) -> None:
        """Register a new protocol handler."""
        cls._registry[handler.protocol_name.upper()] = handler

    @classmethod
    def get_handler(cls, protocol_name: str) -> ProtocolHandler:
        """Retrieve the handler for a protocol name, falling back to RDMA."""
        name_upper = (protocol_name or "RDMA").upper()
        if name_upper in cls._registry:
            return cls._registry[name_upper]
        return cls._registry.get("RDMA", _DEFAULT_RDMA_HANDLER)

    @classmethod
    def get_available_protocols(cls) -> list[str]:
        """Return list of registered protocol names."""
        return list(cls._registry.keys())


# Pre-register built-in protocols
_DEFAULT_RDMA_HANDLER = ProtocolHandler(
    protocol_name="RDMA",
    plugin_cls=rdma_definitions.Plugin,
    thread_cls=rdma_definitions.Thread,
    transfer_group_cls=rdma_definitions.TransferGroup,
    transfer_cls=rdma_definitions.Transfer,
    channel_cls=rdma_definitions.Channel,
    default_rx_port=0,
)

_DEFAULT_UDP_HANDLER = ProtocolHandler(
    protocol_name="UDP",
    plugin_cls=udp_definitions.Plugin,
    thread_cls=udp_definitions.Thread,
    transfer_group_cls=udp_definitions.TransferGroup,
    transfer_cls=udp_definitions.Transfer,
    channel_cls=udp_definitions.Channel,
    default_tx_port=5000,
)

ProtocolFactory.register(_DEFAULT_RDMA_HANDLER)
ProtocolFactory.register(_DEFAULT_UDP_HANDLER)
