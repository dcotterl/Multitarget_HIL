# Architecture & Developer Maintainability Guide

This document describes the design architecture, directory layout, and extension guidelines for developers maintaining or expanding the **Data Sharing Framework Config API** codebase.

> 📖 **Looking for method/class documentation and code examples?** Check out the **[API & Codebase Reference Guide](API_DOCUMENTATION.md)**.

---

## 1. Directory & Package Structure

```
logging_config.json      # Configurable logging settings (created beside the executable for packaged runs; otherwise auto-generated if missing)
data_sharing_framework_config_api/
├── __init__.py           # Package root exports
├── definitions.py        # Core base data model (Configuration, Plugin, Thread, TransferGroup, Transfer, Channel, ComponentSettings, Element)
├── rdma_definitions.py   # RDMA-specific subclasses & default ComponentSettings
├── udp_definitions.py    # UDP-specific subclasses & IP address conversion utilities
├── protocol_factory.py   # Protocol Registry & Factory pattern for extensible object creation
├── logger_config.py      # Logging setup manager (prefers executable-directory config for frozen apps and auto-creates defaults if missing)
└── gui/
    ├── __init__.py
    ├── app.py            # GUI Entry point, window layout, menu bar & Tkinter mainloop
    ├── dialogs.py        # Modal dialogs (Protocol picker, unsaved changes, auto-refreshing Debug Log viewer, Configure Logger window)
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
- Deserialization uses the protocol registry and overridable nested model types, preserving RDMA/UDP behavior throughout a loaded configuration.
- Session saves use a same-directory temporary file followed by atomic replacement, protecting existing files from interrupted or failed writes.
- Inline GUI edits are parsed before assignment and rolled back if a field or direction adaptation fails.
- Logging configuration is intentionally environment-aware: when packaged as a frozen executable, the app prefers `logging_config.json` next to the executable, uses the bundled file as a read-only fallback, and repairs malformed or invalid persisted settings with defaults. The installer uses a per-user writable location so executable-local configuration can persist. The Debug Log window auto-refreshes to show the latest in-memory records without manual re-opening.

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

*(The GUI selects protocols when adding plugins and inherits each plugin's protocol for child elements. New configurations remain protocol-neutral, and unknown protocols are rejected instead of silently falling back to RDMA.)*
