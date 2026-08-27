"""Tkinter editor for configuration files (supports multi-protocol configurations)."""

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

from data_sharing_framework_config_api import logger_config
from data_sharing_framework_config_api.gui import dialogs
from data_sharing_framework_config_api.gui.editor_panel import (
    close_inline_editor,
    has_unsaved_changes,
    show_selected_element,
    update_details_text,
)
from data_sharing_framework_config_api.gui.mutations import (
    run_tree_mutation_with_unsaved_changes,
    show_context_menu,
)
from data_sharing_framework_config_api.gui.session import ConfigurationSession
from data_sharing_framework_config_api.gui.state import editor_state
from data_sharing_framework_config_api.gui.tree import refresh_tree_and_select

logger = logging.getLogger(__name__)
GUI_VERSION = "v2.0"


def load_action(tree, file_path_label, object_map, details_text, root, session):
    logger.info("User requested file load action")
    file_path = filedialog.askopenfilename(
        title="Select configuration file",
        filetypes=(("Configuration files", "*.dsf"), ("JSON files", "*.json"), ("All files", "*.*")),
        initialdir=str(session.file_dialog_directory()),
    )
    if not file_path:
        logger.info("File load dialog cancelled by user")
        return
    try:
        session.load_file(file_path)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        logger.error("Failed to load file '%s': %s", file_path, error)
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


def new_action(tree, file_path_label, object_map, details_text, root, session):
    """Create a new protocol-neutral configuration."""
    logger.info("User requested new configuration action")
    session.new_configuration()
    file_path_label.config(text=session.label_text())
    refresh_tree_and_select(
        tree,
        object_map,
        session.configuration,
        lambda: update_details_text(tree, details_text, object_map),
        lambda: close_inline_editor(details_text),
    )


def save_action(file_path_label, root, details_text, session):
    logger.info("User requested save configuration action")
    state = editor_state(details_text)
    if state.modify_panel is not None and has_unsaved_changes(details_text) and state.save_changes is not None:
        if not state.save_changes():
            logger.warning("Save action aborted due to form validation error")
            return

    file_path = filedialog.asksaveasfilename(
        title="Save configuration file",
        defaultextension=".dsf",
        filetypes=(("Configuration files", "*.dsf"), ("JSON files", "*.json"), ("All files", "*.*")),
        initialdir=str(session.file_dialog_directory()),
    )
    if not file_path:
        logger.info("Save file dialog cancelled by user")
        return
    try:
        saved_path = session.save_file(file_path)
    except (OSError, TypeError, ValueError) as error:
        logger.error("Failed to save file '%s': %s", file_path, error)
        messagebox.showerror("Save Error", f"Could not save the configuration:\n{error}", parent=root)
        return
    file_path_label.config(text=str(saved_path))
    messagebox.showinfo("Save Complete", f"Configuration saved to:\n{saved_path}", parent=root)


def show_about(root):
    """Show the current GUI version."""
    logger.info("User opened About dialog")
    messagebox.showinfo(
        "About Configuration Editor",
        f"Configuration Editor\nVersion {GUI_VERSION}\n\nSupports RDMA and UDP protocols",
        parent=root,
    )


def main():
    logger_config.setup_logging()
    logger.info("Starting Configuration Editor GUI (Version %s)", GUI_VERSION)
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

    tree.bind(
        "<<TreeviewSelect>>",
        lambda event: show_selected_element(tree, details_text, object_map, right_frame, root, event),
    )
    tree.bind(
        "<Button-3>",
        lambda event: show_context_menu(event, tree, object_map, details_text, right_frame, root, session),
    )

    menu_bar = tk.Menu(root)
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(
        label="New",
        command=lambda: run_tree_mutation_with_unsaved_changes(
            tree, details_text, root, lambda: new_action(tree, file_path_label, object_map, details_text, root, session)
        ),
    )
    file_menu.add_command(
        label="Load",
        command=lambda: run_tree_mutation_with_unsaved_changes(
            tree, details_text, root, lambda: load_action(tree, file_path_label, object_map, details_text, root, session)
        ),
    )
    file_menu.add_command(label="Save", command=lambda: save_action(file_path_label, root, details_text, session))
    menu_bar.add_cascade(label="File", menu=file_menu)

    debug_menu = tk.Menu(menu_bar, tearoff=0)
    debug_menu.add_command(label="View Logs", command=lambda: dialogs.show_debug_logs_window(root))
    debug_menu.add_command(label="Configure Logger", command=lambda: dialogs.show_configure_logger_window(root))
    menu_bar.add_cascade(label="Debug", menu=debug_menu)

    help_menu = tk.Menu(menu_bar, tearoff=0)
    help_menu.add_command(label="About", command=lambda: show_about(root))
    menu_bar.add_cascade(label="Help", menu=help_menu)
    root.config(menu=menu_bar)

    root.mainloop()


if __name__ == "__main__":
    main()
