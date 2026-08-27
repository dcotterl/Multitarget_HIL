# GUI Editor Package (`data_sharing_framework_config_api.gui`)

## High-Level Purpose

This subpackage contains the Graphical User Interface (GUI) components built with Python **Tkinter**. It allows users to visually open, inspect, modify, and save `.dsf` configuration trees for multi-protocol HIL communication setups.

---

## File Overview

- **`app.py`**
  - Main GUI entry point. Configures the root Tkinter window, menu bar (File -> New, Load, Save), treeview layout, and event handlers. Includes `main()` executable launcher.

- **`session.py`**
  - Manages session state (`ConfigurationSession`). Handles file I/O operations (loading and saving `.dsf`/`.json` files) and tracks the current file path.

- **`tree.py`**
  - Helpers for building and managing the `ttk.Treeview` control. Maps tree node IDs to underlying Python model objects (`populate_tree`, `refresh_tree_and_select`, `find_parent`).

- **`editor_panel.py`**
  - Controls the right-side details panel and inline form editor. Generates dynamic form fields, formats attribute values for display (including IP address conversion), and handles TX/RX direction parameter adaptation (`adapt_transfers_to_direction`).

- **`dialogs.py`**
  - Reusable modal dialog popups:
    - Protocol selection dialog (`prompt_protocol_selection`).
    - Unsaved changes confirmation dialog (`prompt_unsaved_changes`).
    - Auto-refreshing debug log viewer (`show_debug_logs_window`) that polls the in-memory logger buffer while open.
    - Logger settings configuration window (`show_configure_logger_window`).

- **`mutations.py`**
  - Handles tree structure modifications: adding and removing plugins, threads, transfer groups, transfers, and channels. Also builds right-click context menus (`show_context_menu`).

- **`state.py`**
  - Shared state container (`EditorState`) attached to UI elements to track unsaved form modifications and selection guards.

- **`__init__.py`**
  - Subpackage initialization marker.
