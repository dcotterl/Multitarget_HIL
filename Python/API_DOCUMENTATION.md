# API & Codebase Reference Guide

Welcome! This guide is designed to help developers—especially junior developers or newcomers—understand the architecture of the **Data Sharing Framework Config API**, who does what in the codebase, and how to use every module, class, and function.

---

## 📌 Table of Contents

1. [High-Level Overview](#1-high-level-overview)
2. [Module Map ("Who Does What")](#2-module-map-who-does-what)
3. [Core Data Model (`definitions.py`)](#3-core-data-model-definitionspy)
4. [Protocol Definitions (`rdma_definitions.py` & `udp_definitions.py`)](#4-protocol-definitions)
5. [Protocol Extensibility & Registry (`protocol_factory.py`)](#5-protocol-extensibility--registry-protocol_factorypy)
6. [GUI Architecture (`gui/` package)](#6-gui-architecture-gui-package)
7. [Common How-To Code Examples](#7-common-how-to-code-examples)

---

## 1. High-Level Overview

The Data Sharing Framework configuration tool manages configurations for high-speed hardware-in-the-loop (HIL) communication plugins (such as **RDMA** and **UDP**).

Configurations are stored on disk as **`.dsf`** (JSON) files using a strict nested hierarchy:

```
Configuration (Root schema version metadata & plugins)
  └── Plugin [1..n] (Transport plugin, e.g. RDMA or UDP)
       └── Thread [1..n] (CPU core binding & execution thread)
            └── TransferGroup [1..n] (Direction: TX or RX)
                 └── Transfer [1..n] (Address & port settings)
                      └── Channel [1..n] (Signal channel metadata: units, data types)
```

Each level in the tree can also contain **`ComponentSettings`**, which hold protocol-specific key-value pairs (e.g. `local address`, `destination port`, `source port`).

---

## 2. Module Map ("Who Does What")

| Module | Location | Primary Responsibility |
| :--- | :--- | :--- |
| **`definitions.py`** | Root Package | Core data model classes (`Configuration`, `Plugin`, `Thread`, `TransferGroup`, `Transfer`, `Channel`, `ComponentSettings`, `Element`) and basic serialization methods (`getDict()`, `importFromDict()`, `from_dict()`). |
| **`rdma_definitions.py`** | Root Package | RDMA-specific subclasses extending base definitions with RDMA default `ComponentSettings`. |
| **`udp_definitions.py`** | Root Package | UDP-specific subclasses, IP address conversion utilities (`ip_to_string`, `string_to_ip`), and UDP default `ComponentSettings`. |
| **`protocol_factory.py`** | Root Package | Protocol Registry & Factory pattern (`ProtocolFactory`, `ProtocolHandler`) for decoupled creation of protocol objects. |
| **`logger_config.py`** | Root Package | Configures system logging from `logging_config.json` (console, file output, in-memory log buffer for GUI). In frozen executable builds it prefers a config next to the executable, and if missing it creates one there. It also auto-generates default settings (`INFO`, `log_to_file: true`, `app.log`) for regular Python runs. |
| **`gui/session.py`** | `gui/` Package | Handles loading `.dsf` / `.json` files from disk, saving files, and maintaining active application state (`ConfigurationSession`). |
| **`gui/tree.py`** | `gui/` Package | Populates, selects, and looks up nodes in the Tkinter `Treeview` control. |
| **`gui/state.py`** | `gui/` Package | Shared inline editor state container (`EditorState`) tracking dirty/modified form fields. |
| **`gui/dialogs.py`** | `gui/` Package | Modal dialog windows (Protocol selection picker, unsaved changes prompts, auto-refreshing Debug Log viewer, Configure Logger window). |
| **`gui/editor_panel.py`** | `gui/` Package | Generates form fields for selected tree nodes, formats values (including IP address conversion), and applies direction adaptation. |
| **`gui/mutations.py`** | `gui/` Package | Tree node mutation functions (add/remove plugins, threads, groups, transfers, channels) and right-click context menu wiring. |
| **`gui/app.py`** | `gui/` Package | Main application window, menu bar, and entry point execution (`main()`). |

---

## 3. Core Data Model (`definitions.py`)

### Enums

#### `Protocols(Enum)`
- **`RDMA`** = `"RDMA"`
- **`UDP`** = `"UDP"`

#### `Direction(Enum)`
- **`TX`** = `0` (Transmit)
- **`RX`** = `1` (Receive)

---

### Key Model Classes & Methods

All data model classes inherit the standard framework pattern for serialization:
- **`getDict() -> dict`**: Serializes the object and its children into a JSON-compatible dictionary.
- **`importFromDict(data: dict) -> None`**: Deserializes a dictionary to populate object properties.
- **`from_dict(data: dict) -> ClassInstance`** (Classmethod): Factory constructor creating a new instance from a dictionary.

#### `Element`
*Represents a single key-value setting pair.*
- `__init__(key: str = "", value: Any = None)`
- Properties: `.key`, `.value`

#### `ComponentSettings`
*Container for protocol-specific setting pairs (`Element` objects).*
- `__init__(component: str = "", initial_elements: list[Element] | None = None)`
- `addElement(key: str, value: Any) -> None`: Appends a new key-value `Element`.

#### `Channel`
*Metadata for a signal channel (e.g. voltage, temperature).*
- `__init__(name: str, unit: str, engine_data_type: int, string_data_type: int, string_offset: int)`

#### `Transfer`
*Data transfer unit representing a single packet payload.*
- `__init__(name: str, channels: list[Channel], local_address: str, local_port: int, destination_address: str, destination_port: int)`
- `addChannel(channel: Channel) -> None`: Appends a channel to this transfer.

#### `TransferGroup`
*Group of transfers sharing execution timing and direction.*
- `__init__(name: str, direction: Direction, priority: int, decimation: int, offset: int, timeout_behaviour: int, enable_conversion: bool, transfers: list[Transfer])`
- `addTransfer(transfer: Transfer) -> None`: Appends a transfer to this group.

#### `Thread`
*Binds transfer groups to a target CPU core.*
- `__init__(processor: int, priority_offset: int, transfer_groups: list[TransferGroup])`
- `addTransferGroup(transfer_group: TransferGroup) -> None`: Appends a transfer group to this thread.

#### `Plugin`
*Transport plugin container holding threads for a specific protocol.*
- `__init__(name: str, priority: int, decimation: int, offset: int, threads: list[Thread])`
- `addThread(thread: Thread) -> None`: Appends a thread to this plugin.

#### `Configuration`
*Top-level configuration object representing an entire `.dsf` file.*
- `__init__(plugins: list[Plugin], dsfversion: dict, version: dict)`
- `addPlugin(plugin: Plugin) -> None`: Appends a plugin to this configuration.

---

## 4. Protocol Definitions (`rdma_definitions.py` & `udp_definitions.py`)

### IP Address Conversion Utilities (`udp_definitions.py`)

```python
def ip_to_string(ip_address: str) -> str
```
Converts a standard IPv4 address string (e.g. `"127.0.0.1"`) into its 32-bit integer string representation (e.g. `"2130706433"`). Used when serializing UDP configurations.

```python
def string_to_ip(int_string: str) -> str
```
Converts a 32-bit integer string (e.g. `"2130706433"`) back into a dotted IPv4 address string (e.g. `"127.0.0.1"`). Used when deserializing UDP configurations.

---

## 5. Protocol Extensibility & Registry (`protocol_factory.py`)

The `ProtocolFactory` decouples GUI creation from specific protocol classes.

```python
class ProtocolHandler:
    def create_plugin(name, threads) -> Plugin
    def create_thread(processor, transfer_groups) -> Thread
    def create_transfer_group(name, direction, transfers) -> TransferGroup
    def create_transfer(name, direction, channels) -> Transfer
    def create_channel(name, unit) -> Channel
```

```python
class ProtocolFactory:
    @classmethod
    def register(cls, handler: ProtocolHandler) -> None
    @classmethod
    def get_handler(cls, protocol_name: str) -> ProtocolHandler
    @classmethod
    def get_available_protocols(cls) -> list[str]
```

### 💡 How to Add a New Protocol in 3 Steps:
1. Define your subclasses in a new file (e.g. `tcp_definitions.py`).
2. Instantiate a `ProtocolHandler` passing your custom classes.
3. Call `ProtocolFactory.register(my_tcp_handler)`.

---

## 6. GUI Architecture (`gui/` package)

### `gui.session.ConfigurationSession`
Manages application session state:
- `load_file(file_path)`: Opens and parses `.dsf` or `.json` file into `session.configuration`.
- `save_file(file_path)`: Serializes `session.configuration.getDict()` to disk.
- `new_configuration()`: Resets `session.configuration` to an empty `Configuration()`.

### `gui.tree`
Treeview control population:
- `populate_tree(tree, value, parent, object_map)`: Recursively populates `ttk.Treeview`.
- `find_parent(root, parent_type, child_list_attr, target_child)`: Locates parent object of a tree item.

### `gui.editor_panel`
Form field editor panel:
- `field_definitions(selected_object)`: Returns list of editable attributes for selected node type.
- `adapt_transfers_to_direction(transfer_group)`: Updates child transfer parameters when a group's direction changes (TX vs RX).

### `gui.mutations`
Tree context menu and node mutations:
- `show_context_menu(event, tree, object_map, ...)`: Displays right-click context menu.
- `add_plugin_to_configuration(...)`, `add_thread_to_plugin(...)`, `add_transfer_to_group(...)`, etc.

---

## 7. Common How-To Code Examples

### Example 1: Building a Configuration Programmatically (Bottom-Up)

```python
from data_sharing_framework_config_api import definitions as d
from data_sharing_framework_config_api import udp_definitions as udp

# 1. Create a Channel
ch1 = udp.Channel(name="Engine_Speed", unit="RPM")

# 2. Create a TX Transfer
tx_transfer = udp.Transfer(
    name="Tx_Packet_1",
    destination_address="192.168.1.100",
    destination_port=5000,
    channels=[ch1]
)

# 3. Create a Transfer Group
tx_group = udp.TransferGroup(
    name="Fast_Loop_TX",
    direction=d.Direction.TX,
    transfers=[tx_transfer]
)

# 4. Create a Thread
thread = udp.Thread(processor=2, transfer_groups=[tx_group])

# 5. Create a Plugin
plugin = udp.Plugin(name="UDP_Plugin", threads=[thread])

# 6. Create Top-level Configuration
config = d.Configuration(plugins=[plugin])

# 7. Convert to Dictionary / JSON
config_json = config.getDict()
print(config)
```

### Example 2: Loading, Modifying, and Saving a `.dsf` File

```python
import json
from data_sharing_framework_config_api import definitions as d

# Load from file
with open("my_config.dsf", "r") as f:
    data = json.load(f)

# Deserialize to object model
config = d.Configuration.from_dict(data)

# Access first plugin
first_plugin = config.plugins[0]
print(f"Loaded plugin: {first_plugin.name}")

# Save changes back to file
with open("my_config_modified.dsf", "w") as f:
    json.dump(config.getDict(), f, indent=4)
```
