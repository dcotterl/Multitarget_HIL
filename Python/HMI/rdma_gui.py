"""Tkinter editor for RDMA configuration files.

The GUI loads DSF or JSON configuration data into an
``RDMA_Configuration`` instance and displays only the RDMA model objects in
a tree.  Each tree item is mapped to its live Python object, allowing the
details panel and context-menu actions to inspect or modify that object.

The context menu supports editing objects and adding children through the
RDMA model API: plugins contain threads, threads contain transfer groups,
transfer groups contain transfers, and transfers contain channels.
"""

import sys
import logging
from pathlib import Path
import json

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
#from zipfile import Path
# When run directly, Python searches this examples directory, not its parent.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import RDMA_Definitions as rdma
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "Simple_c1.dsf"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


configuration = rdma.RDMA_Configuration()
CONFIGURATION_OBJECT_TYPES = (
    rdma.RDMA_Configuration,
    rdma.plugin,
    rdma.thread,
    rdma.transferGroup,
    rdma.transfer,
    rdma.channel,
    rdma.component_settings
)


def _object_label(value):
    """Return a readable label for a configuration object."""
    object_name = type(value).__name__
    name = getattr(value, "name", "")
    return f"{object_name}: {name}" if name else object_name


def _populate_tree(tree, value, parent="", object_map=None):
    """Populate the tree with RDMA objects and map IDs to live objects.

    Scalar attributes such as names, ports, and version values are omitted
    from the tree.  They remain available through the selected object's
    details and modification panel.
    """
    if not isinstance(value, CONFIGURATION_OBJECT_TYPES):
        return

    node = tree.insert(parent, "end", text=_object_label(value), open=True)
    if object_map is not None:
        object_map[node] = value

    for child in vars(value).values():
        if isinstance(child, CONFIGURATION_OBJECT_TYPES):
            _populate_tree(tree, child, node, object_map)
        elif isinstance(child, list):
            for item in child:
                if isinstance(item, CONFIGURATION_OBJECT_TYPES):
                    _populate_tree(tree, item, node, object_map)




def load_file(tree, file_path, file_path_label=None, object_map=None):
    """Load a DSF or JSON file into the global configuration and tree."""
    try:
        suffix = Path(file_path).suffix.lower()
        if suffix in (".json", ".dsf"):
            with open(file_path, "r", encoding="utf-8") as file:
                file_content = json.load(file)
        else:
            raise ValueError("Unsupported file type. Expected .json or .dsf.")

        if not isinstance(file_content, dict):
            raise ValueError("Selected file content is not a dictionary.")

        configuration.importFromDict(file_content)

        tree.delete(*tree.get_children())
        if object_map is not None:
            object_map.clear()

        _populate_tree(tree, configuration, object_map=object_map)
        if file_path_label is not None:
            file_path_label.config(text=str(Path(file_path).resolve()))
    except Exception as error:
        messagebox.showerror("Load Error", f"Could not load file:\n{error}")


def load_action(tree, file_path_label, object_map):
    """Open a file picker and load the selected configuration file."""
    tree.delete(*tree.get_children())
    file_path = filedialog.askopenfilename(
        title="Select configuration file",
        filetypes=(
            ("Configuration files", "*.dsf"),
            ("JSON files", "*.json"),
            ("DSF files", "*.dsf"),
            ("All files", "*.*"),
        ),
        initialdir=str(DEFAULT_CONFIG_PATH.parent),
    )
    if not file_path:
        return
    load_file(tree, file_path, file_path_label, object_map)


def new_action(tree, file_path_label, object_map):
    """Create a new configuration with one complete RDMA data path."""
    new_configuration = rdma.RDMA_Configuration(plugins=[])
    new_plugin = rdma.plugin(name="Plugin 1", protocol="RDMA", threads=[])
    new_thread = rdma.thread(processor=-2, protocol="RDMA", transfer_groups=[])
    new_group = rdma.transferGroup(
        name="Transfer Group 1",
        direction=rdma.Direction.TX,
        protocol="RDMA",
        transfers=[],
    )
    new_transfer = rdma.transfer(
        direction=rdma.Direction.TX,
        protocol="RDMA",
        name="Transfer 1",
        channels=[],
    )
    new_transfer.addChannel(
        rdma.channel(name="Channel 1", protocol="RDMA")
    )
    new_group.addTransfer(new_transfer)
    new_thread.addTransferGroup(new_group)
    new_plugin.addThread(new_thread)
    new_configuration.addPlugin(new_plugin)

    configuration.dsfversion = new_configuration.dsfversion
    configuration.version = new_configuration.version
    configuration.plugins = new_configuration.plugins

    tree.delete(*tree.get_children())
    object_map.clear()
    _populate_tree(tree, configuration, object_map=object_map)
    file_path_label.config(text="New configuration")


def save_action(file_path_label, root):
    """Save the current RDMA configuration as an indented JSON DSF file."""
    file_path = filedialog.asksaveasfilename(
        title="Save configuration file",
        defaultextension=".dsf",
        filetypes=(
            ("Configuration files", "*.dsf"),
            ("JSON files", "*.json"),
            ("All files", "*.*"),
        ),
        initialdir=str(DEFAULT_CONFIG_PATH.parent),
        initialfile="configuration.dsf",
    )
    if not file_path:
        return

    try:
        output_path = Path(file_path)
        if output_path.suffix.lower() != ".dsf":
            output_path = output_path.with_suffix(".dsf")
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(configuration.getDict(), file, indent=4)
        if file_path_label is not None:
            file_path_label.config(text=str(output_path.resolve()))
        messagebox.showinfo(
            "Save Complete",
            f"Configuration saved to:\n{output_path.resolve()}",
            parent=root,
        )
    except (OSError, TypeError, ValueError) as error:
        messagebox.showerror(
            "Save Error",
            f"Could not save the configuration:\n{error}",
            parent=root,
        )


def show_selected_element(tree, details_text, object_map, _event=None):
    """Show the selected object's label, type, and serialized contents."""
    selected = tree.selection()
    selected_object = object_map.get(selected[0]) if selected else None
    element = tree.item(selected[0], "text") if selected else ""
    details_text.configure(state="normal")
    details_text.delete("1.0", "end")
    details_text.insert(
        "1.0",
        (
            f"{element}\n\nType: {type(selected_object).__name__}"
            f"\n\nObject:\n{selected_object}"
        )
        if selected_object is not None
        else element,
    )
    details_text.configure(state="disabled")


def _field_definitions(selected_object):
    """Return ``(label, attribute, type)`` definitions for an RDMA object."""
    if isinstance(selected_object, rdma.RDMA_Configuration):
        return [
            ("DSF version", "dsfversion", "json"),
            ("RDMA version", "version", "json"),
        ]
    if isinstance(selected_object, rdma.plugin):
        return [
            ("Name", "name", "text"),
            ("Components (comma-separated)", "components", "list"),
            ("Priority", "priority", "int"),
            ("Decimation", "decimation", "int"),
            ("Offset", "offset", "int"),
        ]
    if isinstance(selected_object, rdma.thread):
        return [
            ("Processor", "processor", "int"),
            ("Priority offset", "priority_offset", "int"),
        ]
    if isinstance(selected_object, rdma.transferGroup):
        return [
            ("Name", "name", "text"),
            ("Direction", "direction", "direction"),
            ("Priority", "priority", "int"),
            ("Decimation", "decimation", "int"),
            ("Offset", "offset", "int"),
            ("Timeout behaviour", "timeout_behaviour", "int"),
            ("Enable conversion", "enable_conversion", "bool"),
        ]
    if isinstance(selected_object, rdma.transfer):
        return [
            ("Name", "name", "text"),
            ("Direction", "direction", "direction"),
        ]
    if isinstance(selected_object, rdma.channel):
        return [
            ("Name", "name", "text"),
            ("Unit", "unit", "text"),
            ("Engine data type", "engine_data_type", "int"),
            ("String data type", "string_data_type", "int"),
            ("String offset", "string_offset", "int"),
        ]
    if isinstance(selected_object, rdma.component_settings):
        return [
            ("Component", "component", "text"),
            ("Values (one key=value per line)", "elements", "elements"),
        ]
    return []


def _field_value(selected_object, attribute, field_type):
    """Convert an object attribute to the text used by its editor widget."""
    value = getattr(selected_object, attribute)
    if field_type == "json":
        return json.dumps(value)
    if field_type == "list":
        return ", ".join(value)
    if field_type == "direction":
        return value.name
    if field_type == "bool":
        return "True" if value else "False"
    if field_type == "elements":
        return "\n".join(f"{item.key}={item.value}" for item in value)
    return str(value)


def _apply_field_value(selected_object, attribute, field_type, value):
    """Convert an editor value and assign it to the selected object."""
    value = value.strip()
    if field_type == "json":
        value = json.loads(value)
    elif field_type == "list":
        value = [item.strip() for item in value.split(",") if item.strip()]
    elif field_type == "direction":
        value = rdma.Direction[value]
    elif field_type == "bool":
        if value not in ("True", "False"):
            raise ValueError("Use True or False.")
        value = value == "True"
    elif field_type == "int":
        value = int(value)
    elif field_type == "elements":
        elements = []
        for line in value.splitlines():
            if not line.strip():
                continue
            if "=" not in line:
                raise ValueError("Each value must use key=value format.")
            key, item_value = line.split("=", 1)
            elements.append(rdma.element(key.strip(), item_value.strip()))
        value = elements
    setattr(selected_object, attribute, value)


def modify_selected_element(tree, object_map, item_id, root):
    """Open a modal editor whose fields match the selected object type."""
    selected_object = object_map.get(item_id)
    if selected_object is None:
        return

    panel = tk.Toplevel(root)
    panel.title(f"Modify {type(selected_object).__name__}")
    panel.transient(root)
    panel.grab_set()
    panel.columnconfigure(1, weight=1)

    fields = {}
    for row, (label, attribute, field_type) in enumerate(
        _field_definitions(selected_object)
    ):
        ttk.Label(panel, text=label).grid(
            row=row, column=0, sticky="nw", padx=8, pady=6
        )
        if field_type == "elements":
            widget = tk.Text(panel, width=42, height=8)
            widget.grid(row=row, column=1, sticky="nsew", padx=8, pady=6)
            widget.insert("1.0", _field_value(selected_object, attribute, field_type))
        elif field_type == "direction":
            widget = ttk.Combobox(
                panel, values=[direction.name for direction in rdma.Direction],
                state="readonly",
            )
            widget.grid(row=row, column=1, sticky="ew", padx=8, pady=6)
            widget.set(_field_value(selected_object, attribute, field_type))
        else:
            widget = ttk.Entry(panel, width=42)
            widget.grid(row=row, column=1, sticky="ew", padx=8, pady=6)
            widget.insert(0, _field_value(selected_object, attribute, field_type))
        fields[attribute] = (widget, field_type)

    def save_changes():
        try:
            for attribute, (widget, field_type) in fields.items():
                value = (
                    widget.get("1.0", "end")
                    if field_type == "elements"
                    else widget.get()
                )
                _apply_field_value(selected_object, attribute, field_type, value)
        except (ValueError, json.JSONDecodeError) as error:
            messagebox.showerror("Modify Error", str(error), parent=panel)
            return

        tree.item(item_id, text=_object_label(selected_object))
        panel.destroy()

    button_frame = ttk.Frame(panel)
    button_frame.grid(row=len(fields), column=0, columnspan=2, pady=8)
    ttk.Button(button_frame, text="Save", command=save_changes).pack(
        side="left", padx=4
    )
    ttk.Button(button_frame, text="Cancel", command=panel.destroy).pack(
        side="left", padx=4
    )


def show_context_menu(event, tree, object_map, root):
    """Show Modify and type-specific child-creation actions for a tree item."""
    item_id = tree.identify_row(event.y)
    if not item_id or item_id not in object_map:
        return

    tree.selection_set(item_id)
    context_menu = tk.Menu(tree, tearoff=0)
    context_menu.add_command(
        label="modify",
        command=lambda: modify_selected_element(tree, object_map, item_id, root),
    )
    selected_object = object_map[item_id]
    if isinstance(selected_object, rdma.transfer):
        context_menu.add_command(
            label="add channel",
            command=lambda: add_channel_to_transfer(
                tree, object_map, item_id
            ),
        )
    if isinstance(selected_object, rdma.transferGroup):
        context_menu.add_command(
            label="add transfer",
            command=lambda: add_transfer_to_group(
                tree, object_map, item_id
            ),
        )
    if isinstance(selected_object, rdma.thread):
        context_menu.add_command(
            label="add group",
            command=lambda: add_group_to_thread(
                tree, object_map, item_id
            ),
        )
    if isinstance(selected_object, rdma.plugin):
        context_menu.add_command(
            label="add thread",
            command=lambda: add_thread_to_plugin(
                tree, object_map, item_id
            ),
        )
    if isinstance(selected_object, rdma.RDMA_Configuration):
        context_menu.add_command(
            label="add plugin",
            command=lambda: add_plugin_to_configuration(
                tree, object_map, item_id
            ),
        )
    context_menu.tk_popup(event.x_root, event.y_root)


def add_channel_to_transfer(tree, object_map, item_id):
    """Create and append a new RDMA channel to the selected transfer."""
    selected_transfer = object_map.get(item_id)
    if not isinstance(selected_transfer, rdma.transfer):
        return
    
    protocol = ""
    if selected_transfer.component_settings:
        protocol = selected_transfer.component_settings[0].component

    logger.debug(f"Adding channel to transfer: {selected_transfer.getName()} with protocol {protocol}")

    channel_number = len(selected_transfer.channels) + 1
    selected_transfer.addChannel(
        rdma.channel(
            name=f"Channel {channel_number}",
            protocol=protocol,
        )
    )

    tree.delete(*tree.get_children())
    object_map.clear()
    _populate_tree(tree, configuration, object_map=object_map)

    for refreshed_item_id, value in object_map.items():
        if value is selected_transfer:
            tree.selection_set(refreshed_item_id)
            tree.see(refreshed_item_id)
            break


def add_transfer_to_group(tree, object_map, item_id):
    """Create and append a new RDMA transfer to the selected group."""
    selected_group = object_map.get(item_id)
    if not isinstance(selected_group, rdma.transferGroup):
        return

    protocol = ""
    if selected_group.component_settings:
        protocol = selected_group.component_settings[0].component

    transfer_number = len(selected_group.transfers) + 1
    new_transfer = rdma.transfer(
        direction=selected_group.direction,
        protocol=protocol,
        name=f"Transfer {transfer_number}",
        channels=[],
    )
    selected_group.addTransfer(new_transfer)

    tree.delete(*tree.get_children())
    object_map.clear()
    _populate_tree(tree, configuration, object_map=object_map)

    for refreshed_item_id, value in object_map.items():
        if value is selected_group:
            tree.selection_set(refreshed_item_id)
            tree.see(refreshed_item_id)
            break


def add_group_to_thread(tree, object_map, item_id):
    """Create and append a new RDMA transfer group to the selected thread."""
    selected_thread = object_map.get(item_id)
    if not isinstance(selected_thread, rdma.thread):
        return

    protocol = ""
    if selected_thread.component_settings:
        protocol = selected_thread.component_settings[0].component

    group_number = len(selected_thread.transfer_groups) + 1
    new_group = rdma.transferGroup(
        name=f"Transfer Group {group_number}",
        direction=rdma.Direction.TX,
        protocol=protocol,
        transfers=[],
    )
    selected_thread.addTransferGroup(new_group)

    tree.delete(*tree.get_children())
    object_map.clear()
    _populate_tree(tree, configuration, object_map=object_map)

    for refreshed_item_id, value in object_map.items():
        if value is selected_thread:
            tree.selection_set(refreshed_item_id)
            tree.see(refreshed_item_id)
            break


def add_thread_to_plugin(tree, object_map, item_id):
    """Create and append a new RDMA thread to the selected plugin."""
    selected_plugin = object_map.get(item_id)
    if not isinstance(selected_plugin, rdma.plugin):
        return

    protocol = ""
    if selected_plugin.component_settings:
        protocol = selected_plugin.component_settings[0].component

    new_thread = rdma.thread(
        processor=-2,
        protocol=protocol,
        transfer_groups=[],
    )
    selected_plugin.addThread(new_thread)

    tree.delete(*tree.get_children())
    object_map.clear()
    _populate_tree(tree, configuration, object_map=object_map)

    for refreshed_item_id, value in object_map.items():
        if value is selected_plugin:
            tree.selection_set(refreshed_item_id)
            tree.see(refreshed_item_id)
            break


def add_plugin_to_configuration(tree, object_map, item_id):
    """Create and append a new RDMA plugin to the configuration."""
    selected_configuration = object_map.get(item_id)
    if not isinstance(selected_configuration, rdma.RDMA_Configuration):
        return

    plugin_number = len(selected_configuration.plugins) + 1
    new_plugin = rdma.plugin(
        name=f"Plugin {plugin_number}",
        protocol="RDMA",
        threads=[],
    )
    selected_configuration.addPlugin(new_plugin)

    tree.delete(*tree.get_children())
    object_map.clear()
    _populate_tree(tree, configuration, object_map=object_map)

    for refreshed_item_id, value in object_map.items():
        if value is selected_configuration:
            tree.selection_set(refreshed_item_id)
            tree.see(refreshed_item_id)
            break


def main():
    """Create the maximized editor window and start Tkinter's event loop."""
    root = tk.Tk()
    root.title("RDMA GUI")
    root.state("zoomed")

    file_path_label = ttk.Label(root, text="No file loaded", anchor="w")
    file_path_label.pack(fill="x", padx=8, pady=(8, 0))

    content_frame = ttk.Frame(root)
    content_frame.pack(fill="both", expand=True, padx=8, pady=8)

    tree_frame = ttk.Frame(content_frame)
    tree_frame.pack(side="left", fill="both", expand=True)

    right_frame = ttk.LabelFrame(content_frame, text="Details")
    right_frame.pack(side="right", fill="both", expand=True, padx=(8, 0))

    details_text = tk.Text(right_frame, wrap="word", state="disabled")
    details_text.pack(fill="both", expand=True, padx=4, pady=4)

    tree = ttk.Treeview(tree_frame, show="tree")
    object_map = {}
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    tree.bind(
        "<<TreeviewSelect>>",
        lambda event: show_selected_element(tree, details_text, object_map, event),
    )
    tree.bind(
        "<Button-3>",
        lambda event: show_context_menu(event, tree, object_map, root),
    )

    menu_bar = tk.Menu(root)

    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(
        label="New",
        command=lambda: new_action(tree, file_path_label, object_map),
    )
    file_menu.add_command(
        label="Load",
        command=lambda: load_action(tree, file_path_label, object_map),
    )
    file_menu.add_command(
        label="Save",
        command=lambda: save_action(file_path_label, root),
    )

    menu_bar.add_cascade(label="File", menu=file_menu)

    root.config(menu=menu_bar)

    if DEFAULT_CONFIG_PATH.is_file():
        load_file(tree, str(DEFAULT_CONFIG_PATH), file_path_label, object_map)

    root.mainloop()


if __name__ == "__main__":
    main()