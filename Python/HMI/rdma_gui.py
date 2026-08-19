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