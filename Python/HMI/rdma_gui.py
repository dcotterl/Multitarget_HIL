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
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config.dsf"

configuration = rdma.RDMA_Configuration()


def _populate_tree(tree, value, parent=""):
    if isinstance(value, dict):
        for key, child in value.items():
            node = tree.insert(parent, "end", text=str(key))
            _populate_tree(tree, child, node)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            node = tree.insert(parent, "end", text=f"[{index}]")
            _populate_tree(tree, child, node)
    elif hasattr(value, "__dict__"):
        for key, child in vars(value).items():
            if key.startswith("_"):
                continue
            node = tree.insert(parent, "end", text=str(key))
            _populate_tree(tree, child, node)
    else:
        tree.insert(parent, "end", text=str(value))




def load_file(tree, file_path, file_path_label=None):
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

        _populate_tree(tree, configuration.getDict())
        if file_path_label is not None:
            file_path_label.config(text=str(Path(file_path).resolve()))
    except Exception as error:
        messagebox.showerror("Load Error", f"Could not load file:\n{error}")


def load_action(tree, file_path_label):
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
    load_file(tree, file_path, file_path_label)


def show_selected_element(tree, details_text, _event=None):
    selected = tree.selection()
    element = tree.item(selected[0], "text") if selected else ""
    details_text.configure(state="normal")
    details_text.delete("1.0", "end")
    details_text.insert("1.0", element)
    details_text.configure(state="disabled")


def main():
    root = tk.Tk()
    root.title("RDMA GUI")
    root.geometry("400x300")

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
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    tree.bind(
        "<<TreeviewSelect>>",
        lambda event: show_selected_element(tree, details_text, event),
    )

    menu_bar = tk.Menu(root)

    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Load", command=lambda: load_action(tree, file_path_label))
    file_menu.add_command(label="Save", state="disabled")

    menu_bar.add_cascade(label="File", menu=file_menu)

    root.config(menu=menu_bar)

    if DEFAULT_CONFIG_PATH.is_file():
        load_file(tree, str(DEFAULT_CONFIG_PATH), file_path_label)

    root.mainloop()


if __name__ == "__main__":
    main()