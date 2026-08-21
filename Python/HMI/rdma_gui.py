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
from dataclasses import dataclass, field

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
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
    rdma.Plugin,
    rdma.Thread,
    rdma.TransferGroup,
    rdma.Transfer,
    rdma.Channel,
    rdma.ComponentSettings,
)


@dataclass
class EditorState:
    """State shared across selection, details, and inline editor helpers."""
    selection_guard: bool = False
    modify_panel: object = None
    edit_item_id: str = None
    edit_fields: dict = field(default_factory=dict)
    edit_initial_values: dict = field(default_factory=dict)
    save_changes: object = None


def _editor_state(details_text):
    """Return the editor state container attached to the details widget."""
    state = getattr(details_text, "editor_state", None)
    if state is None:
        state = EditorState()
        details_text.editor_state = state
    return state


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

    children = []
    component_settings = getattr(value, "component_settings", None)
    if isinstance(component_settings, CONFIGURATION_OBJECT_TYPES):
        children.append(component_settings)
    elif isinstance(component_settings, list):
        children.extend(
            item
            for item in component_settings
            if isinstance(item, CONFIGURATION_OBJECT_TYPES)
        )

    for attribute, child in vars(value).items():
        if attribute == "component_settings":
            continue
        children.append(child)

    for child in children:
        if isinstance(child, CONFIGURATION_OBJECT_TYPES):
            _populate_tree(tree, child, node, object_map)
        elif isinstance(child, list):
            for item in child:
                if isinstance(item, CONFIGURATION_OBJECT_TYPES):
                    _populate_tree(tree, item, node, object_map)


def load_file(
    tree, file_path, file_path_label=None, object_map=None, details_text=None,
    right_frame=None, root=None
):
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

        _refresh_tree_and_select(
            tree,
            object_map if object_map is not None else {},
            details_text,
            right_frame,
            root,
        )
        if file_path_label is not None:
            file_path_label.config(text=str(Path(file_path).resolve()))
    except Exception as error:
        messagebox.showerror("Load Error", f"Could not load file:\n{error}")


def load_action(tree, file_path_label, object_map, details_text, right_frame, root):
    """Open a file picker and load the selected configuration file."""
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
    load_file(
        tree, file_path, file_path_label, object_map, details_text, right_frame, root
    )

def new_action(tree, file_path_label, object_map, details_text, right_frame, root):
    """Create a new configuration with one complete RDMA data path."""
    new_configuration = rdma.RDMA_Configuration(plugins=[])
    new_plugin = rdma.Plugin(name="Plugin 1", protocol="RDMA", threads=[])
    new_thread = rdma.Thread(processor=-2, protocol="RDMA", transfer_groups=[])
    new_group = rdma.TransferGroup(
        name="Transfer Group 1",
        direction=rdma.Direction.TX,
        protocol="RDMA",
        transfers=[],
    )
    new_transfer = rdma.Transfer(
        direction=rdma.Direction.TX,
        protocol="RDMA",
        name="Transfer 1",
        channels=[],
    )
    new_transfer.addChannel(
        rdma.Channel(name="Channel 1", protocol="RDMA")
    )
    new_group.addTransfer(new_transfer)
    new_thread.addTransferGroup(new_group)
    new_plugin.addThread(new_thread)
    new_configuration.addPlugin(new_plugin)

    configuration.importFromDict(new_configuration.getDict())

    _refresh_tree_and_select(tree, object_map, details_text, right_frame, root)
    file_path_label.config(text="New configuration")


def save_action(file_path_label, root, details_text=None):
    """Save the current RDMA configuration as an indented JSON DSF file."""
    state = _editor_state(details_text) if details_text is not None else None
    if (
        state is not None
        and state.modify_panel is not None
        and _has_unsaved_changes(details_text)
        and state.save_changes is not None
    ):
        if not state.save_changes():
            return

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
        suffix = output_path.suffix.lower()
        if suffix not in (".dsf", ".json"):
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


def _update_details_text(tree, details_text, object_map):
    """Refresh the read-only data view for the selected tree item."""
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


def show_selected_element(
    tree, details_text, object_map, right_frame, root, _event=None, open_editor=True
):
    """Show the selected object's label, type, and serialized contents."""
    state = _editor_state(details_text)
    if state.selection_guard:
        state.selection_guard = False
        return

    selected = tree.selection()
    selected_item_id = selected[0] if selected else None
    modify_panel = state.modify_panel
    edit_item_id = state.edit_item_id
    if modify_panel is not None:
        if (
            selected_item_id != edit_item_id
            and _has_unsaved_changes(details_text)
        ):
            if not edit_item_id or not tree.exists(edit_item_id):
                _close_inline_editor(details_text)
            else:
                state.selection_guard = True
                tree.selection_set(edit_item_id)
                _prompt_unsaved_changes(
                    tree,
                    details_text,
                    object_map,
                    right_frame,
                    root,
                    selected_item_id,
                )
                return
        _close_inline_editor(details_text)
    if not details_text.winfo_manager():
        details_text.pack(fill="both", expand=True, padx=4, pady=4)

    selected_object = object_map.get(selected[0]) if selected else None
    _update_details_text(tree, details_text, object_map)
    if selected_object is not None and open_editor:
        modify_selected_element(
            tree, object_map, selected[0], details_text, right_frame, root
        )


def _field_definitions(selected_object):
    """Return ``(label, attribute, type)`` definitions for an RDMA object."""
    if isinstance(selected_object, rdma.RDMA_Configuration):
        return [
            ("DSF version", "dsfversion", "json"),
            ("RDMA version", "version", "json"),
        ]
    if isinstance(selected_object, rdma.Plugin):
        return [
            ("Name", "name", "text"),
            ("Components (comma-separated)", "components", "list"),
            ("Priority", "priority", "int"),
            ("Decimation", "decimation", "int"),
            ("Offset", "offset", "int"),
        ]
    if isinstance(selected_object, rdma.Thread):
        return [
            ("Processor", "processor", "int"),
            ("Priority offset", "priority_offset", "int"),
        ]
    if isinstance(selected_object, rdma.TransferGroup):
        return [
            ("Name", "name", "text"),
            ("Direction", "direction", "direction"),
            ("Priority", "priority", "int"),
            ("Decimation", "decimation", "int"),
            ("Offset", "offset", "int"),
            ("Timeout behaviour", "timeout_behaviour", "int"),
            ("Enable conversion", "enable_conversion", "bool"),
        ]
    if isinstance(selected_object, rdma.Transfer):
        return [
            ("Name", "name", "text"),
            ("Direction", "direction", "direction"),
        ]
    if isinstance(selected_object, rdma.Channel):
        return [
            ("Name", "name", "text"),
            ("Unit", "unit", "text"),
            ("Engine data type", "engine_data_type", "int"),
            ("String data type", "string_data_type", "int"),
            ("String offset", "string_offset", "int"),
        ]
    if isinstance(selected_object, rdma.ComponentSettings):
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


def _editor_value(widget, field_type):
    """Return the current text from an editor widget."""
    if field_type == "elements":
        return widget.get("1.0", "end-1c")
    return widget.get()


def _mark_changed(widget, initial_value, field_type, _event=None):
    """Color an editor red while its value differs from its initial value."""
    current_value = _editor_value(widget, field_type)
    widget.configure(foreground="red" if current_value != initial_value else "black")


def _has_unsaved_changes(details_text):
    """Return whether the inline editor contains unsaved values."""
    state = _editor_state(details_text)
    fields = state.edit_fields
    initial_values = state.edit_initial_values
    return any(
        _editor_value(widget, field_type) != initial_values[attribute]
        for attribute, (widget, field_type) in fields.items()
    )


def _close_inline_editor(details_text):
    """Remove the inline editor and clear its tracked editing state."""
    state = _editor_state(details_text)
    panel = state.modify_panel
    if panel is not None:
        panel.destroy()
    state.modify_panel = None
    state.edit_item_id = None
    state.edit_fields = {}
    state.edit_initial_values = {}
    state.save_changes = None


def _prompt_unsaved_changes(
    tree, details_text, object_map, right_frame, root, pending_item_id,
    on_continue=None
):
    """Ask whether to save or discard changes before changing selection."""
    prompt = tk.Toplevel(root)
    prompt.title("Unsaved changes")
    prompt.transient(root)
    prompt.grab_set()

    ttk.Label(
        prompt,
        text="This element has unsaved changes. What would you like to do?",
        padding=12,
    ).pack()
    button_frame = ttk.Frame(prompt)
    button_frame.pack(pady=(0, 12))

    def continue_selection(save):
        state = _editor_state(details_text)
        if save and state.save_changes is not None:
            if not state.save_changes():
                return
        prompt.destroy()
        _close_inline_editor(details_text)
        if on_continue is not None:
            state.selection_guard = False
            on_continue()
            return
        if pending_item_id and tree.exists(pending_item_id):
            state.selection_guard = False
            tree.selection_set(pending_item_id)
            tree.see(pending_item_id)
            show_selected_element(
                tree,
                details_text,
                object_map,
                right_frame,
                root,
                open_editor=(right_frame is not None and root is not None),
            )
        else:
            state.selection_guard = False

    ttk.Button(
        button_frame,
        text="Save changes",
        command=lambda: continue_selection(True),
    ).pack(side="left", padx=4)
    ttk.Button(
        button_frame,
        text="Don't save",
        command=lambda: continue_selection(False),
    ).pack(side="left", padx=4)

    prompt.update_idletasks()
    prompt.geometry(
        f"+{(prompt.winfo_screenwidth() - prompt.winfo_reqwidth()) // 2}"
        f"+{(prompt.winfo_screenheight() - prompt.winfo_reqheight()) // 2}"
    )


def modify_selected_element(tree, object_map, item_id, details_text, right_frame, root):
    """Show an in-place editor in the details panel for the selected object."""
    state = _editor_state(details_text)
    selected_object = object_map.get(item_id)
    if selected_object is None:
        return

    details_text.pack_forget()
    panel = ttk.Frame(right_frame)
    state.modify_panel = panel
    state.edit_item_id = item_id
    panel.pack(fill="x", padx=4, pady=(4, 0))
    details_text.pack(fill="both", expand=True, padx=4, pady=4)
    panel.columnconfigure(1, weight=1)

    ttk.Label(
        panel,
        text=f"Modify {type(selected_object).__name__}",
        font=("TkDefaultFont", 10, "bold"),
    ).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 10))

    fields = {}
    initial_values = {}
    for row, (label, attribute, field_type) in enumerate(
        _field_definitions(selected_object)
    ):
        row += 1
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
        initial_value = _editor_value(widget, field_type)
        initial_values[attribute] = initial_value
        widget.bind(
            "<KeyRelease>",
            lambda event, editor=widget, original=initial_value, kind=field_type:
            _mark_changed(editor, original, kind, event),
        )
        if field_type == "direction":
            widget.bind(
                "<<ComboboxSelected>>",
                lambda event, editor=widget, original=initial_value, kind=field_type:
                _mark_changed(editor, original, kind, event),
            )

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
            messagebox.showerror("Modify Error", str(error), parent=root)
            return False

        for attribute, (widget, field_type) in fields.items():
            initial_values[attribute] = _editor_value(widget, field_type)
            widget.configure(foreground="black")

        tree.item(item_id, text=_object_label(selected_object))
        _update_details_text(tree, details_text, object_map)
        return True

    state.save_changes = save_changes
    state.edit_fields = fields
    state.edit_initial_values = initial_values

    def restore_changes():
        for attribute, (widget, field_type) in fields.items():
            initial_value = initial_values[attribute]
            if field_type == "elements":
                widget.delete("1.0", "end")
                widget.insert("1.0", initial_value)
            elif field_type == "direction":
                widget.set(initial_value)
            else:
                widget.delete(0, "end")
                widget.insert(0, initial_value)
            _mark_changed(widget, initial_value, field_type)

    button_frame = ttk.Frame(panel)
    button_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=8)
    ttk.Button(button_frame, text="Save", command=save_changes).pack(
        side="left", padx=4
    )
    ttk.Button(button_frame, text="Restore", command=restore_changes).pack(
        side="left", padx=4
    )


def _run_tree_mutation_with_unsaved_changes(
    tree, details_text, object_map, right_frame, root, mutate_action
):
    """Run a tree mutation after resolving unsaved inline editor changes."""
    state = _editor_state(details_text)
    modify_panel = state.modify_panel
    if modify_panel is not None and _has_unsaved_changes(details_text):
        _prompt_unsaved_changes(
            tree,
            details_text,
            object_map,
            right_frame,
            root,
            None,
            on_continue=mutate_action,
        )
        return
    if modify_panel is not None:
        _close_inline_editor(details_text)
    mutate_action()


def show_context_menu(event, tree, object_map, details_text, right_frame, root):
    """Show Modify and type-specific child-creation actions for a tree item."""
    item_id = tree.identify_row(event.y)
    if not item_id or item_id not in object_map:
        return

    tree.selection_set(item_id)
    context_menu = tk.Menu(tree, tearoff=0)
    selected_object = object_map[item_id]
    if isinstance(selected_object, rdma.Transfer):
        context_menu.add_command(
            label="add channel",
            command=lambda: _run_tree_mutation_with_unsaved_changes(
                tree, details_text, object_map, right_frame, root,
                lambda: add_channel_to_transfer(
                    tree, object_map, details_text, right_frame, root, item_id
                )
            ),
        )
        context_menu.add_command(
            label="remove transfer",
            command=lambda: _run_tree_mutation_with_unsaved_changes(
                tree, details_text, object_map, right_frame, root,
                lambda: remove_transfer_from_group(
                    tree, object_map, details_text, right_frame, root, item_id
                )
            ),
        )
    if isinstance(selected_object, rdma.Channel):
        context_menu.add_command(
            label="remove channel",
            command=lambda: _run_tree_mutation_with_unsaved_changes(
                tree, details_text, object_map, right_frame, root,
                lambda: remove_channel_from_transfer(
                    tree, object_map, details_text, right_frame, root, item_id
                )
            ),
        )
    if isinstance(selected_object, rdma.TransferGroup):
        context_menu.add_command(
            label="add transfer",
            command=lambda: _run_tree_mutation_with_unsaved_changes(
                tree, details_text, object_map, right_frame, root,
                lambda: add_transfer_to_group(
                    tree, object_map, details_text, right_frame, root, item_id
                )
            ),
        )
        context_menu.add_command(
            label="remove transfer group",
            command=lambda: _run_tree_mutation_with_unsaved_changes(
                tree, details_text, object_map, right_frame, root,
                lambda: remove_group_from_thread(
                    tree, object_map, details_text, right_frame, root, item_id
                )
            ),
        )
    if isinstance(selected_object, rdma.Thread):
        context_menu.add_command(
            label="add group",
            command=lambda: _run_tree_mutation_with_unsaved_changes(
                tree, details_text, object_map, right_frame, root,
                lambda: add_group_to_thread(
                    tree, object_map, details_text, right_frame, root, item_id
                )
            ),
        )
        context_menu.add_command(
            label="remove thread",
            command=lambda: _run_tree_mutation_with_unsaved_changes(
                tree, details_text, object_map, right_frame, root,
                lambda: remove_thread_from_plugin(
                    tree, object_map, details_text, right_frame, root, item_id
                )
            ),
        )
    if isinstance(selected_object, rdma.Plugin):
        context_menu.add_command(
            label="add thread",
            command=lambda: _run_tree_mutation_with_unsaved_changes(
                tree, details_text, object_map, right_frame, root,
                lambda: add_thread_to_plugin(
                    tree, object_map, details_text, right_frame, root, item_id
                )
            ),
        )
        context_menu.add_command(
            label="remove plugin",
            command=lambda: _run_tree_mutation_with_unsaved_changes(
                tree, details_text, object_map, right_frame, root,
                lambda: remove_plugin_from_configuration(
                    tree, object_map, details_text, right_frame, root, item_id
                )
            ),
        )
    if isinstance(selected_object, rdma.RDMA_Configuration):
        context_menu.add_command(
            label="add plugin",
            command=lambda: _run_tree_mutation_with_unsaved_changes(
                tree, details_text, object_map, right_frame, root,
                lambda: add_plugin_to_configuration(
                    tree, object_map, details_text, right_frame, root, item_id
                )
            ),
        )
    context_menu.tk_popup(event.x_root, event.y_root)


def _parent_component(parent, default=""):
    """Return the component name used by a parent's first setting."""
    settings = getattr(parent, "component_settings", [])
    if isinstance(settings, rdma.ComponentSettings):
        return settings.component
    if settings:
        return settings[0].component
    return default


def _refresh_tree_and_select(
    tree, object_map, details_text=None, right_frame=None, root=None,
    select_object=None
):
    """Rebuild the tree from the global configuration and optionally re-select an object.

    This helper centralises the repeated pattern of clearing the tree,
    repopulating it, and restoring focus to a specific model object.
    """
    tree.delete(*tree.get_children())
    object_map.clear()
    _populate_tree(tree, configuration, object_map=object_map)
    selected_item_id = None
    if select_object is not None:
        for item_id, value in object_map.items():
            if value is select_object:
                selected_item_id = item_id
                tree.selection_set(item_id)
                tree.see(item_id)
                break
    if details_text is None:
        return

    _close_inline_editor(details_text)
    if selected_item_id is None:
        tree.selection_remove(tree.selection())
        _update_details_text(tree, details_text, object_map)
        return

    show_selected_element(
        tree, details_text, object_map, right_frame, root, open_editor=True
    )


def _find_parent(root, parent_type, child_list_attr, target_child):
    """Return the first object of *parent_type* whose *child_list_attr* contains *target_child*.

    This generic helper replaces the four structurally identical
    ``_find_*_with_*`` functions that previously existed in this module.
    The search recurses through all children of ``root`` that belong to
    ``CONFIGURATION_OBJECT_TYPES``.

    Args:
        root: The model object to search from (usually the top-level
            ``RDMA_Configuration`` instance).
        parent_type: The class that owns the child list (e.g. ``rdma.Transfer``).
        child_list_attr: The attribute name of the list on the parent (e.g.
            ``"channels"``).
        target_child: The specific child object to locate.

    Returns:
        The parent object if found, otherwise ``None``.
    """
    if isinstance(root, parent_type):
        if any(child is target_child for child in getattr(root, child_list_attr, [])):
            return root
        return None

    if isinstance(root, CONFIGURATION_OBJECT_TYPES):
        for child in vars(root).values():
            if isinstance(child, list):
                for item in child:
                    result = _find_parent(item, parent_type, child_list_attr, target_child)
                    if result is not None:
                        return result
            elif isinstance(child, CONFIGURATION_OBJECT_TYPES):
                result = _find_parent(child, parent_type, child_list_attr, target_child)
                if result is not None:
                    return result
    return None


def add_channel_to_transfer(tree, object_map, details_text, right_frame, root, item_id):
    """Create and append a new RDMA channel to the selected transfer."""
    selected_transfer = object_map.get(item_id)
    if not isinstance(selected_transfer, rdma.Transfer):
        return

    protocol = _parent_component(selected_transfer)

    logger.debug(f"Adding channel to transfer: {selected_transfer.name} with protocol {protocol}")

    channel_number = len(selected_transfer.channels) + 1
    selected_transfer.addChannel(
        rdma.Channel(
            name=f"Channel {channel_number}",
            protocol=protocol,
        )
    )

    _refresh_tree_and_select(
        tree, object_map, details_text, right_frame, root, selected_transfer
    )


def remove_channel_from_transfer(
    tree, object_map, details_text, right_frame, root, item_id
):
    """Remove the selected channel from its parent transfer."""
    selected_channel = object_map.get(item_id)
    if not isinstance(selected_channel, rdma.Channel):
        return

    parent_transfer = _find_parent(configuration, rdma.Transfer, "channels", selected_channel)
    if parent_transfer is None:
        return

    parent_transfer.channels.remove(selected_channel)
    _refresh_tree_and_select(
        tree, object_map, details_text, right_frame, root, parent_transfer
    )


def remove_transfer_from_group(
    tree, object_map, details_text, right_frame, root, item_id
):
    """Remove the selected transfer from its parent transfer group."""
    selected_transfer = object_map.get(item_id)
    if not isinstance(selected_transfer, rdma.Transfer):
        return

    parent_group = _find_parent(configuration, rdma.TransferGroup, "transfers", selected_transfer)
    if parent_group is None:
        return

    parent_group.transfers.remove(selected_transfer)
    _refresh_tree_and_select(
        tree, object_map, details_text, right_frame, root, parent_group
    )


def remove_group_from_thread(
    tree, object_map, details_text, right_frame, root, item_id
):
    """Remove the selected transfer group from its parent thread."""
    selected_group = object_map.get(item_id)
    if not isinstance(selected_group, rdma.TransferGroup):
        return

    parent_thread = _find_parent(configuration, rdma.Thread, "transfer_groups", selected_group)
    if parent_thread is None:
        return

    parent_thread.transfer_groups.remove(selected_group)
    _refresh_tree_and_select(
        tree, object_map, details_text, right_frame, root, parent_thread
    )


def remove_thread_from_plugin(
    tree, object_map, details_text, right_frame, root, item_id
):
    """Remove the selected thread from its parent plugin."""
    selected_thread = object_map.get(item_id)
    if not isinstance(selected_thread, rdma.Thread):
        return

    parent_plugin = _find_parent(configuration, rdma.Plugin, "threads", selected_thread)
    if parent_plugin is None:
        return

    parent_plugin.threads.remove(selected_thread)
    _refresh_tree_and_select(
        tree, object_map, details_text, right_frame, root, parent_plugin
    )


def add_transfer_to_group(tree, object_map, details_text, right_frame, root, item_id):
    """Create and append a new RDMA transfer to the selected group."""
    selected_group = object_map.get(item_id)
    if not isinstance(selected_group, rdma.TransferGroup):
        return

    protocol = _parent_component(selected_group)

    transfer_number = len(selected_group.transfers) + 1
    new_transfer = rdma.Transfer(
        direction=selected_group.direction,
        protocol=protocol,
        name=f"Transfer {transfer_number}",
        channels=[],
    )
    selected_group.addTransfer(new_transfer)
    _refresh_tree_and_select(
        tree, object_map, details_text, right_frame, root, selected_group
    )


def add_group_to_thread(tree, object_map, details_text, right_frame, root, item_id):
    """Create and append a new RDMA transfer group to the selected thread."""
    selected_thread = object_map.get(item_id)
    if not isinstance(selected_thread, rdma.Thread):
        return

    protocol = _parent_component(selected_thread)

    group_number = len(selected_thread.transfer_groups) + 1
    new_group = rdma.TransferGroup(
        name=f"Transfer Group {group_number}",
        direction=rdma.Direction.TX,
        protocol=protocol,
        transfers=[],
    )
    selected_thread.addTransferGroup(new_group)
    _refresh_tree_and_select(
        tree, object_map, details_text, right_frame, root, selected_thread
    )


def add_thread_to_plugin(tree, object_map, details_text, right_frame, root, item_id):
    """Create and append a new RDMA thread to the selected plugin."""
    selected_plugin = object_map.get(item_id)
    if not isinstance(selected_plugin, rdma.Plugin):
        return

    protocol = _parent_component(selected_plugin)

    new_thread = rdma.Thread(
        processor=-2,
        protocol=protocol,
        transfer_groups=[],
    )
    selected_plugin.addThread(new_thread)
    _refresh_tree_and_select(
        tree, object_map, details_text, right_frame, root, selected_plugin
    )


def add_plugin_to_configuration(
    tree, object_map, details_text, right_frame, root, item_id
):
    """Create and append a new RDMA plugin to the configuration."""
    selected_configuration = object_map.get(item_id)
    if not isinstance(selected_configuration, rdma.RDMA_Configuration):
        return

    plugin_number = len(selected_configuration.plugins) + 1
    new_plugin = rdma.Plugin(
        name=f"Plugin {plugin_number}",
        protocol="RDMA",
        threads=[],
    )
    selected_configuration.addPlugin(new_plugin)
    _refresh_tree_and_select(
        tree, object_map, details_text, right_frame, root, selected_configuration
    )


def remove_plugin_from_configuration(
    tree, object_map, details_text, right_frame, root, item_id
):
    """Remove the selected plugin from the configuration."""
    selected_plugin = object_map.get(item_id)
    if not isinstance(selected_plugin, rdma.Plugin):
        return

    if selected_plugin not in configuration.plugins:
        return

    configuration.plugins.remove(selected_plugin)
    _refresh_tree_and_select(
        tree, object_map, details_text, right_frame, root, configuration
    )


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
        lambda event: show_selected_element(
            tree, details_text, object_map, right_frame, root, event
        ),
    )
    tree.bind(
        "<Button-3>",
        lambda event: show_context_menu(
            event, tree, object_map, details_text, right_frame, root
        ),
    )

    menu_bar = tk.Menu(root)

    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(
        label="New",
        command=lambda: _run_tree_mutation_with_unsaved_changes(
            tree, details_text, object_map, right_frame, root,
            lambda: new_action(
                tree, file_path_label, object_map, details_text, right_frame, root
            ),
        ),
    )
    file_menu.add_command(
        label="Load",
        command=lambda: _run_tree_mutation_with_unsaved_changes(
            tree, details_text, object_map, right_frame, root,
            lambda: load_action(
                tree, file_path_label, object_map, details_text, right_frame, root
            ),
        ),
    )
    file_menu.add_command(
        label="Save",
        command=lambda: save_action(file_path_label, root, details_text),
    )

    menu_bar.add_cascade(label="File", menu=file_menu)

    root.config(menu=menu_bar)

    root.mainloop()


if __name__ == "__main__":
    main()
