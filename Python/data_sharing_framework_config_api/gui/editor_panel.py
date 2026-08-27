"""GUI Editor panel and details text view helpers."""

from __future__ import annotations

import json
import logging
from copy import deepcopy
import tkinter as tk
from tkinter import messagebox, ttk

from data_sharing_framework_config_api import definitions, udp_definitions
from data_sharing_framework_config_api.gui import dialogs
from data_sharing_framework_config_api.gui.state import editor_state
from data_sharing_framework_config_api.gui.tree import object_label

logger = logging.getLogger(__name__)


def update_details_text(tree, details_text, object_map):
    """Render details view text for the currently selected item in the treeview."""
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
    """Return a list of (label, attribute_name, field_type) tuples defining editable form fields for selected_object."""
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
    """Retrieve and format the string value of attribute on selected_object for display in an editor widget."""
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


def adapt_transfers_to_direction(transfer_group: definitions.TransferGroup):
    """Adapt child transfers when a TransferGroup direction changes."""
    is_tx = (transfer_group.direction == definitions.Direction.TX)
    logger.info("Adapting child transfers for TransferGroup('%s') to direction=%s", transfer_group.name, transfer_group.direction.name)

    for transfer in getattr(transfer_group, "transfers", []):
        for cs in getattr(transfer, "component_settings", []):
            if cs.component == "RDMA":
                if is_tx:
                    if not transfer.local_address:
                        transfer.local_address = transfer.destination_address or "127.0.0.1"
                    if transfer.local_port == 0:
                        transfer.local_port = transfer.destination_port
                    if not transfer.destination_address:
                        transfer.destination_address = transfer.local_address or "127.0.0.1"
                    if transfer.destination_port == 0:
                        transfer.destination_port = transfer.local_port

                    elements = [
                        definitions.Element("local address", str(transfer.local_address)),
                        definitions.Element("local port", str(transfer.local_port)),
                        definitions.Element("destination address", str(transfer.destination_address)),
                        definitions.Element("destination port", str(transfer.destination_port)),
                    ]
                    cs.elements = elements
                else:
                    if not transfer.local_address:
                        transfer.local_address = transfer.destination_address or "127.0.0.1"
                    if transfer.local_port == 0:
                        transfer.local_port = transfer.destination_port
                    transfer.destination_address = ""
                    transfer.destination_port = 0

                    elements = [
                        definitions.Element("local address", str(transfer.local_address)),
                        definitions.Element("local port", str(transfer.local_port)),
                    ]
                    cs.elements = elements

            elif cs.component == "UDP":
                if is_tx:
                    if not transfer.destination_address:
                        transfer.destination_address = transfer.local_address or "127.0.0.1"
                    if transfer.destination_port == 0:
                        transfer.destination_port = transfer.local_port or 5000
                    transfer.local_address = ""
                    transfer.local_port = 0

                    addr_val = transfer.destination_address
                    if "." in addr_val:
                        try:
                            addr_val = udp_definitions.ip_to_string(addr_val)
                        except Exception:
                            pass

                    elements = [
                        definitions.Element("destination address", addr_val),
                        definitions.Element("destination port", str(transfer.destination_port)),
                    ]
                    cs.elements = elements
                else:
                    if not transfer.local_address:
                        transfer.local_address = transfer.destination_address or "127.0.0.1"
                    if transfer.local_port == 0:
                        transfer.local_port = transfer.destination_port or 5000
                    transfer.destination_address = ""
                    transfer.destination_port = 0

                    addr_val = transfer.local_address
                    if "." in addr_val:
                        try:
                            addr_val = udp_definitions.ip_to_string(addr_val)
                        except Exception:
                            pass

                    elements = [
                        definitions.Element("source address", addr_val),
                        definitions.Element("source port", str(transfer.local_port)),
                    ]
                    cs.elements = elements


def apply_field_value(selected_object, attribute, field_type, value):
    """Parse and apply a string value from an editor widget."""
    parsed_value = parse_field_value(selected_object, field_type, value)
    old_val = getattr(selected_object, attribute, None)
    setattr(selected_object, attribute, parsed_value)
    logger.info("Updated attribute '%s' on %s (old='%s' -> new='%s')", attribute, type(selected_object).__name__, old_val, parsed_value)


def parse_field_value(selected_object, field_type, value):
    """Parse an editor value without mutating the model."""
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
    return value


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
        original_state = deepcopy(selected_object.__dict__)
        try:
            parsed_values = {}
            for attribute, (widget, field_type) in fields.items():
                value = widget.get("1.0", "end-1c") if field_type == "elements" else widget.get()
                parsed_values[attribute] = parse_field_value(selected_object, field_type, value)
            for attribute, value in parsed_values.items():
                setattr(selected_object, attribute, value)
            if isinstance(selected_object, definitions.TransferGroup):
                adapt_transfers_to_direction(selected_object)
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            selected_object.__dict__ = original_state
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
                dialogs.prompt_unsaved_changes(tree, details_text, root, selected_item_id, close_editor_fn=close_inline_editor)
                return
        close_inline_editor(details_text)
    if not details_text.winfo_manager():
        details_text.pack(fill="both", expand=True, padx=4, pady=4)

    selected_object = object_map.get(selected[0]) if selected else None
    update_details_text(tree, details_text, object_map)
    if selected_object is not None and open_editor:
        modify_selected_element(tree, object_map, selected[0], details_text, right_frame, root)
