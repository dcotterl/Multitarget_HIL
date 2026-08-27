"""GUI Dialog windows (protocol selector, unsaved changes confirmation)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from data_sharing_framework_config_api import definitions
from data_sharing_framework_config_api.gui.state import editor_state


def prompt_protocol_selection(root: tk.Tk, title: str = "Select Protocol", message: str = "Select protocol:") -> str | None:
    """Show a dialog to select a protocol from available protocols defined in definitions.Protocols."""
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.transient(root)
    dialog.grab_set()

    ttk.Label(dialog, text=message, padding=12).pack()

    selected_protocol: str | None = None

    def make_choice(proto_value: str) -> None:
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


def prompt_unsaved_changes(tree, details_text, root, pending_item_id, on_continue=None, close_editor_fn=None):
    """Prompt user when unsaved changes exist in the editor panel before switching selection or mutating tree."""
    prompt = tk.Toplevel(root)
    prompt.title("Unsaved changes")
    prompt.transient(root)
    prompt.grab_set()
    ttk.Label(prompt, text="This element has unsaved changes. What would you like to do?", padding=12).pack()
    button_frame = ttk.Frame(prompt)
    button_frame.pack(pady=(0, 12))

    def continue_selection(save: bool):
        state = editor_state(details_text)
        if save and state.save_changes is not None and not state.save_changes():
            return
        prompt.destroy()
        if close_editor_fn is not None:
            close_editor_fn(details_text)
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
