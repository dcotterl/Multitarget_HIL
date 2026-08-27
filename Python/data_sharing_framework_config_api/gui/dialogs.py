"""GUI Dialog windows (protocol selector, unsaved changes confirmation, debug log viewer)."""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from data_sharing_framework_config_api import definitions, logger_config
from data_sharing_framework_config_api.gui.state import editor_state

logger = logging.getLogger(__name__)


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


def show_debug_logs_window(root: tk.Tk) -> None:
    """Open a Toplevel window displaying application log history in real-time."""
    logger.info("Opening Debug Logs window")
    win = tk.Toplevel(root)
    win.title("Debug Logs")
    win.geometry("850x550")

    config, config_path = logger_config.load_logging_config()
    level_str = config.get("level", "INFO")
    file_logging = config.get("log_to_file", True)
    file_path = config.get("log_file_path", "app.log")

    info_frame = ttk.Frame(win, padding=8)
    info_frame.pack(fill="x")
    info_text = f"Config: {config_path}   |   Level: {level_str}   |   File Logging: {'Enabled (' + str(file_path) + ')' if file_logging else 'Disabled'}"
    ttk.Label(info_frame, text=info_text, font=("TkDefaultFont", 9, "bold")).pack(anchor="w")

    text_frame = ttk.Frame(win, padding=8)
    text_frame.pack(fill="both", expand=True)

    log_text = tk.Text(text_frame, wrap="none", state="disabled")
    log_text.pack(side="left", fill="both", expand=True)

    scrollbar_y = ttk.Scrollbar(text_frame, orient="vertical", command=log_text.yview)
    scrollbar_y.pack(side="right", fill="y")
    scrollbar_x = ttk.Scrollbar(win, orient="horizontal", command=log_text.xview)
    scrollbar_x.pack(fill="x", padx=8)
    log_text.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

    def refresh_logs():
        log_text.configure(state="normal")
        log_text.delete("1.0", "end")
        logs = logger_config.in_memory_handler.get_logs()
        if not logs:
            log_text.insert("1.0", "[No log records in memory]")
        else:
            log_text.insert("1.0", "\n".join(logs))
        log_text.see("end")
        log_text.configure(state="disabled")

    def clear_logs():
        logger_config.in_memory_handler.clear()
        refresh_logs()

    def copy_logs():
        logs = logger_config.in_memory_handler.get_logs()
        win.clipboard_clear()
        win.clipboard_append("\n".join(logs))
        messagebox.showinfo("Clipboard", "Logs copied to clipboard!", parent=win)

    btn_frame = ttk.Frame(win, padding=8)
    btn_frame.pack(fill="x")

    ttk.Button(btn_frame, text="Refresh", command=refresh_logs).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="Clear Buffer", command=clear_logs).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="Copy Logs", command=copy_logs).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="Close", command=win.destroy).pack(side="right", padx=4)

    refresh_logs()

