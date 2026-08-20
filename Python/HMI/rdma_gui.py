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

    """Populate the tree with RDMA configuration objects only."""
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


def show_selected_element(tree, details_text, object_map, _event=None):
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
    """Return the editable fields for a specific RDMA object type."""
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
    """Open a type-specific editor for the selected tree object."""
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
    """Show the tree context menu for the item under the mouse pointer."""
    item_id = tree.identify_row(event.y)
    if not item_id or item_id not in object_map:
        return

    tree.selection_set(item_id)
    context_menu = tk.Menu(tree, tearoff=0)
    context_menu.add_command(
        label="Modify",
        command=lambda: modify_selected_element(tree, object_map, item_id, root),
    )
    context_menu.tk_popup(event.x_root, event.y_root)


def main():
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
        label="Load",
        command=lambda: load_action(tree, file_path_label, object_map),
    )
    file_menu.add_command(label="Save", state="disabled")

    menu_bar.add_cascade(label="File", menu=file_menu)

    root.config(menu=menu_bar)

    if DEFAULT_CONFIG_PATH.is_file():
        load_file(tree, str(DEFAULT_CONFIG_PATH), file_path_label, object_map)

    root.mainloop()


if __name__ == "__main__":
    main()