# Architecture & Developer Maintainability Guide

This document describes the design architecture, directory layout, and extension guidelines for developers maintaining or expanding the **Data Sharing Framework Config API** codebase.

> 📖 **Looking for method/class documentation and code examples?** Check out the **[API & Codebase Reference Guide](API_DOCUMENTATION.md)**.

---

## 1. Directory & Package Structure

```
data_sharing_framework_config_api/
├── __init__.py           # Package root exports
├── definitions.py        # Core base data model (Configuration, Plugin, Thread, TransferGroup, Transfer, Channel, ComponentSettings, Element)
├── rdma_definitions.py   # RDMA-specific subclasses & default ComponentSettings
├── udp_definitions.py    # UDP-specific subclasses & IP address conversion utilities
├── protocol_factory.py   # Protocol Registry & Factory pattern for extensible object creation
└── gui/
    ├── __init__.py
    ├── app.py            # GUI Entry point, window layout & Tkinter mainloop
    ├── dialogs.py        # Modal dialogs (Protocol selection picker, unsaved changes prompts)
    ├── editor_panel.py   # Details text view, form field generation, IP formatting, & direction adaptation
    ├── mutations.py      # Tree mutation actions (add/remove plugins, threads, groups, transfers, channels)
    ├── session.py        # Session file loading/saving state
    ├── state.py          # Shared inline editor state container
    └── tree.py           # Treeview population and lookup helpers
```

---

## 2. Core Data Model Architecture

The data sharing framework uses a hierarchical tree structure serialized into `.dsf` (JSON) configuration files:

```
Configuration
  └── Plugin [1..n]
       └── Thread [1..n]
            └── TransferGroup [1..n]  (TX or RX direction)
                 └── Transfer [1..n]
                      └── Channel [1..n]
```

- Base definitions reside in [definitions.py](data_sharing_framework_config_api/definitions.py).
- Protocol extensions (`rdma_definitions.py`, `udp_definitions.py`) inherit from base classes (`d.Transfer`, `d.Plugin`, etc.) to attach protocol-specific `ComponentSettings` (such as `"local address"`, `"destination port"`, or `"source address"`).

---

## 3. Extensibility: Adding a New Protocol

To add support for a new protocol (e.g. `TCP`, `CAN`, or `SharedMemory`):

1. **Add Enum Entry**: Add the protocol name to `Protocols` enum in [definitions.py](data_sharing_framework_config_api/definitions.py):
   ```python
   class Protocols(Enum):
       RDMA = "RDMA"
       UDP = "UDP"
       TCP = "TCP"  # New protocol
   ```

2. **Create Protocol Module**: Create `data_sharing_framework_config_api/tcp_definitions.py` with subclasses of `Channel`, `Transfer`, `TransferGroup`, `Thread`, `Plugin`.

3. **Register in Protocol Factory**: Register a `ProtocolHandler` in [protocol_factory.py](data_sharing_framework_config_api/protocol_factory.py):
   ```python
   ProtocolFactory.register(ProtocolHandler(
       protocol_name="TCP",
       plugin_cls=tcp_definitions.Plugin,
       thread_cls=tcp_definitions.Thread,
       transfer_group_cls=tcp_definitions.TransferGroup,
       transfer_cls=tcp_definitions.Transfer,
       channel_cls=tcp_definitions.Channel,
   ))
   ```

*(The GUI will automatically include the new protocol in selection dialogs and inherit its protocol types when adding child elements!)*
