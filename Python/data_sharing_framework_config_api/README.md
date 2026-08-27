# Data Sharing Framework Config API (`data_sharing_framework_config_api`)

## High-Level Purpose

This directory contains the primary Python package for the **Data Sharing Framework Config API**. It provides the object model, serialization/deserialization logic, protocol registry, and Tkinter GUI for building and editing Data Sharing Framework (`.dsf`) configuration files used in Hardware-in-the-Loop (HIL) systems.

---

## File Overview

- **`definitions.py`**
  - Defines the core object-oriented model hierarchy (`Configuration`, `Plugin`, `Thread`, `TransferGroup`, `Transfer`, `Channel`, `ComponentSettings`, `Element`).
  - Contains base JSON/dict serialization (`getDict()`) and deserialization (`importFromDict()`, `from_dict()`) methods.

- **`rdma_definitions.py`**
  - Protocol-specific extensions for **RDMA** communication.
  - Subclasses base definitions to automatically initialize RDMA component settings (e.g. `local address`, `local port`, `destination address`, `destination port`).

- **`udp_definitions.py`**
  - Protocol-specific extensions for **UDP** communication.
  - Includes IP address conversion helpers (`ip_to_string` and `string_to_ip`) to convert dotted IPv4 strings to/from 32-bit integer representations expected by DSF files.

- **`protocol_factory.py`**
  - Implements the **Protocol Registry & Factory Pattern** (`ProtocolFactory`, `ProtocolHandler`).
  - Decouples object creation from the GUI layer so new protocols can be added dynamically without modifying UI code.

- **`__init__.py`**
  - Package initialization file exposing the public package API.

---

## Subdirectories

- **[`gui/`](gui/README.md)**
  - Graphical User Interface package built with Python Tkinter for visually viewing, editing, and mutating `.dsf` configuration trees.
