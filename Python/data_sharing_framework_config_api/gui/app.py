"""Tkinter editor for configuration files (supports RDMA and UDP protocols)."""

from __future__ import annotations

import json
import logging
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Add the project root when this file is launched directly instead of as a module.
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data_sharing_framework_config_api import definitions, rdma_definitions, udp_definitions
from data_sharing_framework_config_api.gui.session import ConfigurationSession
from data_sharing_framework_config_api.gui.state import editor_state
from data_sharing_framework_config_api.gui.tree import CONFIGURATION_OBJECT_TYPES, find_parent, object_label, refresh_tree_and_select

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
GUI_VERSION = "v2.0"


def update_details_text(tree, details_text, object_map):
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


def field_definitions(selected_object):
    if isinstance(selected_object, definitions.Configuration):
        return [("DSF version", "dsfversion", "json"), ("Version", "version", "json")]
    if isinstance(selected_object, definitions.Plugin):
        return [
            ("Name", "name", "text"),
            ("Components (comma-separated)", "components", "list"),
            ("Priority", "priority", "int"),
            ("Decimation", "decimation", "int"),
            ("Offset", "offset", "int"),
        ]
    if isinstance(selected_object, definitions.Thread):
        return [("Processor", "processor", "int"), ("Priority offset", "priority_offset", "int")]
    if isinstance(selected_object, definitions.TransferGroup):
        return [
            ("Name", "name", "text"),
            ("Direction", "direction", "direction"),
            ("Priority", "priority", "int"),
            ("Decimation", "decimation", "int"),
            ("Offset", "offset", "int"),
            ("Timeout behaviour", "timeout_behaviour", "int"),
            ("Enable conversion", "enable_conversion", "bool"),
        ]
    if isinstance(selected_object, definitions.Transfer):
        return [("Name", "name", "text")]
    if isinstance(selected_object, definitions.Channel):
        return [
            ("Name", "name", "text"),
            ("Unit", "unit", "text"),
            ("Engine data type", "engine_data_type", "int"),
            ("String data type", "string_data_type", "int"),
            ("String offset", "string_offset", "int"),
        ]
    if isinstance(selected_object, definitions.ComponentSettings):
        return [("Component", "component", "text"), ("Values (one key=value per line)", "elements", "elements")]
    return []


def field_value(selected_object, attribute, field_type):
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
        lines = []
        is_udp = getattr(selected_object, "component", "") == "UDP"
        for item in value:
            val_str = str(item.value)
            if is_udp and item.key in ("source address", "destination address", "local address"):
                try:
                    val_str = definitions._format_udp_ip_value(item.key, val_str)
                except Exception:
                    pass
            lines.append(f"{item.key}={val_str}")
        return "\n".join(lines)
    return str(value)


def apply_field_value(selected_object, attribute, field_type, value):
    value = value.strip()
    if field_type == "json":
        value = json.loads(value)
    elif field_type == "list":
        value = [item.strip() for item in value.split(",") if item.strip()]
    elif field_type == "direction":
        value = definitions.Direction[value]
    elif field_type == "bool":
        if value not in ("True", "False"):
            raise ValueError("Use True or False.")
        value = value == "True"
    elif field_type == "int":
        value = int(value)
    elif field_type == "elements":
        elements = []
        is_udp = getattr(selected_object, "component", "") == "UDP"
        for line in value.splitlines():
            if not line.strip():
                continue
            if "=" not in line:
                raise ValueError("Each value must use key=value format.")
            key, item_value = line.split("=", 1)
            key = key.strip()
            item_value = item_value.strip()
            if is_udp and key in ("source address", "destination address", "local address"):
                try:
                    if "." in item_value:
                        import socket, struct
                        packed = socket.inet_aton(item_value)
                        item_value = str(struct.unpack("!L", packed)[0])
                except Exception as e:
                    raise ValueError(f"Invalid IP address format '{item_value}': {e}") from e
            elements.append(definitions.Element(key, item_value))
        value = elements
    setattr(selected_object, attribute, value)


def editor_value(widget, field_type):
    return widget.get("1.0", "end-1c") if field_type == "elements" else widget.get()


def mark_changed(widget, initial_value, field_type, _event=None):
    current_value = editor_value(widget, field_type)
    widget.configure(foreground="red" if current_value != initial_value else "black")


def has_unsaved_changes(details_text):
    state = editor_state(details_text)
    return any(
        editor_value(widget, field_type) != state.edit_initial_values[attribute]
        for attribute, (widget, field_type) in state.edit_fields.items()
    )


def close_inline_editor(details_text):
    state = editor_state(details_text)
    panel = state.modify_panel
    if panel is not None:
        panel.destroy()
    state.modify_panel = None
    state.edit_item_id = None
    state.edit_fields = {}
    state.edit_initial_values = {}
    state.save_changes = None


def prompt_unsaved_changes(tree, details_text, root, pending_item_id, on_continue=None):
    prompt = tk.Toplevel(root)
    prompt.title("Unsaved changes")
    prompt.transient(root)
    prompt.grab_set()
    ttk.Label(prompt, text="This element has unsaved changes. What would you like to do?", padding=12).pack()
    button_frame = ttk.Frame(prompt)
    button_frame.pack(pady=(0, 12))

    def continue_selection(save):
        state = editor_state(details_text)
        if save and state.save_changes is not None and not state.save_changes():
            return
        prompt.destroy()
        close_inline_editor(details_text)
        if on_continue is not None:
            state.selection_guard = False
            on_continue()
            return
        if pending_item_id and tree.exists(pending_item_id):
            state.selection_guard = False
            tree.selection_set(pending_item_id)
            tree.see(pending_item_id)
        else:
            state.selection_guard = False

    ttk.Button(button_frame, text="Save changes", command=lambda: continue_selection(True)).pack(side="left", padx=4)
    ttk.Button(button_frame, text="Don't save", command=lambda: continue_selection(False)).pack(side="left", padx=4)
    prompt.update_idletasks()
    prompt.geometry(
        f"+{(prompt.winfo_screenwidth() - prompt.winfo_reqwidth()) // 2}"
        f"+{(prompt.winfo_screenheight() - prompt.winfo_reqheight()) // 2}"
    )


def modify_selected_element(tree, object_map, item_id, details_text, right_frame, root):
    state = editor_state(details_text)
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

    ttk.Label(panel, text=f"Modify {type(selected_object).__name__}", font=("TkDefaultFont", 10, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 10)
    )

    fields = {}
    initial_values = {}
    for row, (label, attribute, field_type) in enumerate(field_definitions(selected_object), start=1):
        ttk.Label(panel, text=label).grid(row=row, column=0, sticky="nw", padx=8, pady=6)
        if field_type == "elements":
            widget = tk.Text(panel, width=42, height=8)
            widget.grid(row=row, column=1, sticky="nsew", padx=8, pady=6)
            widget.insert("1.0", field_value(selected_object, attribute, field_type))
        elif field_type == "direction":
            widget = ttk.Combobox(panel, values=[direction.name for direction in definitions.Direction], state="readonly")
            widget.grid(row=row, column=1, sticky="ew", padx=8, pady=6)
            widget.set(field_value(selected_object, attribute, field_type))
        else:
            widget = ttk.Entry(panel, width=42)
            widget.grid(row=row, column=1, sticky="ew", padx=8, pady=6)
            widget.insert(0, field_value(selected_object, attribute, field_type))
        fields[attribute] = (widget, field_type)
        initial_value = editor_value(widget, field_type)
        initial_values[attribute] = initial_value
        widget.bind(
            "<KeyRelease>",
            lambda event, editor=widget, original=initial_value, kind=field_type: mark_changed(editor, original, kind, event),
        )
        if field_type == "direction":
            widget.bind(
                "<<ComboboxSelected>>",
                lambda event, editor=widget, original=initial_value, kind=field_type: mark_changed(editor, original, kind, event),
            )

    def save_changes():
        try:
            for attribute, (widget, field_type) in fields.items():
                value = widget.get("1.0", "end-1c") if field_type == "elements" else widget.get()
                apply_field_value(selected_object, attribute, field_type, value)
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            messagebox.showerror("Modify Error", str(error), parent=root)
            return False

        for attribute, (widget, field_type) in fields.items():
            initial_values[attribute] = editor_value(widget, field_type)
            widget.configure(foreground="black")

        tree.item(item_id, text=object_label(selected_object))
        update_details_text(tree, details_text, object_map)
        return True

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
            mark_changed(widget, initial_value, field_type)

    state.save_changes = save_changes
    state.edit_fields = fields
    state.edit_initial_values = initial_values

    button_frame = ttk.Frame(panel)
    button_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=8)
    ttk.Button(button_frame, text="Save", command=save_changes).pack(side="left", padx=4)
    ttk.Button(button_frame, text="Restore", command=restore_changes).pack(side="left", padx=4)


def show_selected_element(tree, details_text, object_map, right_frame, root, _event=None, open_editor=True):
    state = editor_state(details_text)
    if state.selection_guard:
        state.selection_guard = False
        return

    selected = tree.selection()
    selected_item_id = selected[0] if selected else None
    if state.modify_panel is not None:
        if selected_item_id != state.edit_item_id and has_unsaved_changes(details_text):
            if not state.edit_item_id or not tree.exists(state.edit_item_id):
                close_inline_editor(details_text)
            else:
                state.selection_guard = True
                tree.selection_set(state.edit_item_id)
                prompt_unsaved_changes(tree, details_text, root, selected_item_id)
                return
        close_inline_editor(details_text)
    if not details_text.winfo_manager():
        details_text.pack(fill="both", expand=True, padx=4, pady=4)

    selected_object = object_map.get(selected[0]) if selected else None
    update_details_text(tree, details_text, object_map)
    if selected_object is not None and open_editor:
        modify_selected_element(tree, object_map, selected[0], details_text, right_frame, root)


def run_tree_mutation_with_unsaved_changes(tree, details_text, root, mutate_action):
    state = editor_state(details_text)
    if state.modify_panel is not None and has_unsaved_changes(details_text):
        prompt_unsaved_changes(tree, details_text, root, None, on_continue=mutate_action)
        return
    if state.modify_panel is not None:
        close_inline_editor(details_text)
    mutate_action()


def find_ancestor_plugin(configuration: definitions.Configuration, target) -> definitions.Plugin | None:
    if isinstance(target, definitions.Plugin):
        return target
    if configuration is None:
        return None
    for plugin in getattr(configuration, "plugins", []):
        if target is plugin:
            return plugin
        for thread in getattr(plugin, "threads", []):
            if target is thread:
                return plugin
            for group in getattr(thread, "transfer_groups", []):
                if target is group:
                    return plugin
                for transfer in getattr(group, "transfers", []):
                    if target is transfer or any(ch is target for ch in getattr(transfer, "channels", [])):
                        return plugin
    return None


def get_protocol_for_element(session, selected_object) -> str:
    """Find the protocol of the ancestor plugin for selected_object."""
    plugin = find_ancestor_plugin(session.configuration, selected_object)
    if plugin is not None:
        if getattr(plugin, "components", None) and plugin.components:
            comp = plugin.components[0]
            if comp in [p.value for p in definitions.Protocols]:
                return comp
        if getattr(plugin, "component_settings", None):
            for cs in plugin.component_settings:
                if cs.component in [p.value for p in definitions.Protocols]:
                    return cs.component
        if isinstance(plugin, udp_definitions.Plugin):
            return "UDP"
        if isinstance(plugin, rdma_definitions.Plugin):
            return "RDMA"
    return getattr(session, "protocol", "RDMA")


def prompt_protocol_selection(root, title="Select Protocol", message="Select protocol:"):
    """Show a dialog to select a protocol from available protocols in definitions.Protocols."""
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.transient(root)
    dialog.grab_set()

    ttk.Label(dialog, text=message, padding=12).pack()

    selected_protocol = None

    def make_choice(proto_value):
        nonlocal selected_protocol
        selected_protocol = proto_value
        dialog.destroy()

    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=12)

    available_protocols = [p.value for p in definitions.Protocols]
    for proto_value in available_protocols:
        ttk.Button(button_frame, text=proto_value, command=lambda p=proto_value: make_choice(p)).pack(side="left", padx=4)

    ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=4)

    dialog.update_idletasks()
    dialog.geometry(
        f"+{(dialog.winfo_screenwidth() - dialog.winfo_reqwidth()) // 2}"
        f"+{(dialog.winfo_screenheight() - dialog.winfo_reqheight()) // 2}"
    )

    root.wait_window(dialog)
    return selected_protocol


def remove_plugin_from_configuration(configuration, selected_plugin, refresh):
    if selected_plugin not in configuration.plugins:
        return
    configuration.plugins = [plugin for plugin in configuration.plugins if plugin is not selected_plugin]
    refresh(configuration)


def show_context_menu(event, tree, object_map, details_text, right_frame, root, session):
    item_id = tree.identify_row(event.y)
    if not item_id or item_id not in object_map:
        return

    tree.selection_set(item_id)
    context_menu = tk.Menu(tree, tearoff=0)
    selected_object = object_map[item_id]

    def refresh(select_object):
        refresh_tree_and_select(
            tree,
            object_map,
            session.configuration,
            lambda: update_details_text(tree, details_text, object_map),
            lambda: close_inline_editor(details_text),
            select_object,
        )

    if isinstance(selected_object, definitions.Transfer):
        context_menu.add_command(label="add channel", command=lambda: run_tree_mutation_with_unsaved_changes(
            tree, details_text, root, lambda: add_channel_to_transfer(session, selected_object, refresh)
        ))
        context_menu.add_command(label="remove transfer", command=lambda: run_tree_mutation_with_unsaved_changes(
            tree, details_text, root, lambda: remove_transfer_from_group(session.configuration, selected_object, refresh)
        ))
    if isinstance(selected_object, definitions.Channel):
        context_menu.add_command(label="remove channel", command=lambda: run_tree_mutation_with_unsaved_changes(
            tree, details_text, root, lambda: remove_channel_from_transfer(session.configuration, selected_object, refresh)
        ))
    if isinstance(selected_object, definitions.TransferGroup):
        context_menu.add_command(label="add transfer", command=lambda: run_tree_mutation_with_unsaved_changes(
            tree, details_text, root, lambda: add_transfer_to_group(session, selected_object, refresh)
        ))
        context_menu.add_command(label="remove transfer group", command=lambda: run_tree_mutation_with_unsaved_changes(
            tree, details_text, root, lambda: remove_group_from_thread(session.configuration, selected_object, refresh)
        ))
    if isinstance(selected_object, definitions.Thread):
        context_menu.add_command(label="add group", command=lambda: run_tree_mutation_with_unsaved_changes(
            tree, details_text, root, lambda: add_group_to_thread(session, selected_object, refresh)
        ))
        context_menu.add_command(label="remove thread", command=lambda: run_tree_mutation_with_unsaved_changes(
            tree, details_text, root, lambda: remove_thread_from_plugin(session.configuration, selected_object, refresh)
        ))
    if isinstance(selected_object, definitions.Plugin):
        context_menu.add_command(label="add thread", command=lambda: run_tree_mutation_with_unsaved_changes(
            tree, details_text, root, lambda: add_thread_to_plugin(session, selected_object, refresh)
        ))
        context_menu.add_command(label="remove plugin", command=lambda: run_tree_mutation_with_unsaved_changes(
            tree, details_text, root, lambda: remove_plugin_from_configuration(session.configuration, selected_object, refresh)
        ))
    if isinstance(selected_object, definitions.Configuration):
        context_menu.add_command(label="add plugin", command=lambda: run_tree_mutation_with_unsaved_changes(
            tree, details_text, root, lambda: add_plugin_to_configuration(session, selected_object, refresh, root)
        ))
    context_menu.tk_popup(event.x_root, event.y_root)


def load_action(tree, file_path_label, object_map, details_text, root, session):
    default_path = session.default_config_path()
    file_path = filedialog.askopenfilename(
        title="Select configuration file",
        filetypes=(("Configuration files", "*.dsf"), ("JSON files", "*.json"), ("All files", "*.*")),
        initialdir=str(default_path.parent) if default_path is not None else None,
    )
    if not file_path:
        return
    try:
        session.load_file(file_path)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        messagebox.showerror("Load Error", f"Could not load file:\n{error}", parent=root)
        return
    file_path_label.config(text=str(session.current_path))
    refresh_tree_and_select(
        tree,
        object_map,
        session.configuration,
        lambda: update_details_text(tree, details_text, object_map),
        lambda: close_inline_editor(details_text),
    )


def add_channel_to_transfer(session, selected_transfer, refresh):
    protocol = get_protocol_for_element(session, selected_transfer)
    channel_number = len(selected_transfer.channels) + 1
    if protocol == "UDP":
        selected_transfer.addChannel(udp_definitions.Channel(name=f"Channel {channel_number}"))
    else:
        selected_transfer.addChannel(rdma_definitions.Channel(name=f"Channel {channel_number}"))
    refresh(selected_transfer)


def remove_channel_from_transfer(configuration, selected_channel, refresh):
    parent_transfer = find_parent(configuration, definitions.Transfer, "channels", selected_channel)
    if parent_transfer is None:
        return
    parent_transfer.channels = [channel for channel in parent_transfer.channels if channel is not selected_channel]
    refresh(parent_transfer)


def remove_transfer_from_group(configuration, selected_transfer, refresh):
    parent_group = find_parent(configuration, definitions.TransferGroup, "transfers", selected_transfer)
    if parent_group is None:
        return
    parent_group.transfers = [transfer for transfer in parent_group.transfers if transfer is not selected_transfer]
    refresh(parent_group)


def remove_group_from_thread(configuration, selected_group, refresh):
    parent_thread = find_parent(configuration, definitions.Thread, "transfer_groups", selected_group)
    if parent_thread is None:
        return
    parent_thread.transfer_groups = [group for group in parent_thread.transfer_groups if group is not selected_group]
    refresh(parent_thread)


def remove_thread_from_plugin(configuration, selected_thread, refresh):
    parent_plugin = find_parent(configuration, definitions.Plugin, "threads", selected_thread)
    if parent_plugin is None:
        return
    parent_plugin.threads = [thread for thread in parent_plugin.threads if thread is not selected_thread]
    refresh(parent_plugin)


def add_transfer_to_group(session, selected_group, refresh):
    protocol = get_protocol_for_element(session, selected_group)
    transfer_number = len(selected_group.transfers) + 1
    
    if protocol == "UDP":
        if selected_group.direction == definitions.Direction.RX:
            transfer = udp_definitions.Transfer(name=f"Transfer {transfer_number}", channels=[], local_address="127.0.0.1", local_port=5000)
        elif selected_group.direction == definitions.Direction.TX:
            transfer = udp_definitions.Transfer(
                name=f"Transfer {transfer_number}", 
                channels=[],
                destination_address="127.0.0.1", 
                destination_port=5000
            )
        else:
            transfer = udp_definitions.Transfer(name=f"Transfer {transfer_number}", channels=[])
    else:
        if selected_group.direction == definitions.Direction.RX:
            transfer = rdma_definitions.Transfer(name=f"Transfer {transfer_number}", channels=[], local_address="127.0.0.1", local_port=0)
        elif selected_group.direction == definitions.Direction.TX:
            transfer = rdma_definitions.Transfer(
                name=f"Transfer {transfer_number}", 
                channels=[],
                destination_address="127.0.0.1", 
                destination_port=0
            )
        else:
            transfer = rdma_definitions.Transfer(name=f"Transfer {transfer_number}", channels=[])
    
    selected_group.addTransfer(transfer)
    refresh(selected_group)


def add_group_to_thread(session, selected_thread, refresh):
    protocol = get_protocol_for_element(session, selected_thread)
    group_number = len(selected_thread.transfer_groups) + 1
    if protocol == "UDP":
        selected_thread.addTransferGroup(
            udp_definitions.TransferGroup(name=f"Transfer Group {group_number}", direction=definitions.Direction.TX, transfers=[])
        )
    else:
        selected_thread.addTransferGroup(
            rdma_definitions.TransferGroup(name=f"Transfer Group {group_number}", direction=definitions.Direction.TX, transfers=[])
        )
    refresh(selected_thread)


def add_thread_to_plugin(session, selected_plugin, refresh):
    protocol = get_protocol_for_element(session, selected_plugin)
    if protocol == "UDP":
        selected_plugin.addThread(udp_definitions.Thread(processor=-2, transfer_groups=[]))
    else:
        selected_plugin.addThread(rdma_definitions.Thread(processor=-2, transfer_groups=[]))
    refresh(selected_plugin)


def add_plugin_to_configuration(session, selected_configuration, refresh, root):
    protocol = prompt_protocol_selection(root, title="Select Protocol", message="Select protocol for new plugin:")
    if protocol is None:
        return

    plugin_number = len(selected_configuration.plugins) + 1
    if protocol == "UDP":
        selected_configuration.addPlugin(udp_definitions.Plugin(name=f"Plugin {plugin_number}", threads=[]))
    else:
        selected_configuration.addPlugin(rdma_definitions.Plugin(name=f"Plugin {plugin_number}", threads=[]))
    refresh(selected_configuration)


def new_action(tree, file_path_label, object_map, details_text, root, session):
    """Create a new empty configuration."""
    session.new_configuration()
    file_path_label.config(text=session.label_text())
    refresh_tree_and_select(
        tree,
        object_map,
        session.configuration,
        lambda: update_details_text(tree, details_text, object_map),
        lambda: close_inline_editor(details_text),
    )
    
    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=12)
    
    ttk.Button(button_frame, text="RDMA", command=on_rdma).pack(side="left", padx=4)
    ttk.Button(button_frame, text="UDP", command=on_udp).pack(side="left", padx=4)
    ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side="left", padx=4)
    
    dialog.update_idletasks()
    dialog.geometry(
        f"+{(dialog.winfo_screenwidth() - dialog.winfo_reqwidth()) // 2}"
        f"+{(dialog.winfo_screenheight() - dialog.winfo_reqheight()) // 2}"
    )
    
    root.wait_window(dialog)
    
    # If user cancelled, do nothing
    if selected_protocol is None:
        return
    
    # Create configuration with selected protocol
    session.new_configuration(selected_protocol)
    file_path_label.config(text=session.label_text())
    refresh_tree_and_select(
        tree,
        object_map,
        session.configuration,
        lambda: update_details_text(tree, details_text, object_map),
        lambda: close_inline_editor(details_text),
    )


def save_action(file_path_label, root, details_text, session):
    state = editor_state(details_text)
    if state.modify_panel is not None and has_unsaved_changes(details_text) and state.save_changes is not None:
        if not state.save_changes():
            return

    default_path = session.current_path or session.default_config_path()
    file_path = filedialog.asksaveasfilename(
        title="Save configuration file",
        defaultextension=".dsf",
        filetypes=(("Configuration files", "*.dsf"), ("JSON files", "*.json"), ("All files", "*.*")),
        initialdir=str(default_path.parent) if default_path is not None else None,
        initialfile=default_path.name if default_path is not None else "configuration.dsf",
    )
    if not file_path:
        return
    try:
        saved_path = session.save_file(file_path)
    except (OSError, TypeError, ValueError) as error:
        messagebox.showerror("Save Error", f"Could not save the configuration:\n{error}", parent=root)
        return
    file_path_label.config(text=str(saved_path))
    messagebox.showinfo("Save Complete", f"Configuration saved to:\n{saved_path}", parent=root)


def show_about(root):
    """Show the current GUI version."""
    messagebox.showinfo("About Configuration Editor", f"Configuration Editor\nVersion {GUI_VERSION}\n\nSupports RDMA and UDP protocols", parent=root)


def main():
    root = tk.Tk()
    root.title("Configuration Editor (RDMA/UDP)")
    root.state("zoomed")
    session = ConfigurationSession()

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

    tree.bind("<<TreeviewSelect>>", lambda event: show_selected_element(tree, details_text, object_map, right_frame, root, event))
    tree.bind("<Button-3>", lambda event: show_context_menu(event, tree, object_map, details_text, right_frame, root, session))

    menu_bar = tk.Menu(root)
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="New", command=lambda: run_tree_mutation_with_unsaved_changes(
        tree, details_text, root, lambda: new_action(tree, file_path_label, object_map, details_text, root, session)
    ))
    file_menu.add_command(label="Load", command=lambda: run_tree_mutation_with_unsaved_changes(
        tree, details_text, root, lambda: load_action(tree, file_path_label, object_map, details_text, root, session)
    ))
    file_menu.add_command(label="Save", command=lambda: save_action(file_path_label, root, details_text, session))
    menu_bar.add_cascade(label="File", menu=file_menu)
    help_menu = tk.Menu(menu_bar, tearoff=0)
    help_menu.add_command(label="About", command=lambda: show_about(root))
    menu_bar.add_cascade(label="Help", menu=help_menu)
    root.config(menu=menu_bar)

    if session.default_config_path() is not None:
        file_path_label.config(text=f"No file loaded")

    root.mainloop()


if __name__ == "__main__":
    main()
