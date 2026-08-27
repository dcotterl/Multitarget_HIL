"""Tree population and lookup helpers for the configuration GUI."""

from __future__ import annotations

from data_sharing_framework_config_api import definitions

CONFIGURATION_OBJECT_TYPES = (
    definitions.Configuration,
    definitions.Plugin,
    definitions.Thread,
    definitions.TransferGroup,
    definitions.Transfer,
    definitions.Channel,
    definitions.ComponentSettings,
)

CHILD_ATTRIBUTES = {
    definitions.Configuration: ("plugins",),
    definitions.Plugin: ("threads",),
    definitions.Thread: ("transfer_groups",),
    definitions.TransferGroup: ("transfers",),
    definitions.Transfer: ("channels",),
}


def object_label(value) -> str:
    """Return a display text label for a configuration model object (e.g. 'Plugin: MyPlugin')."""
    object_name = type(value).__name__
    name = getattr(value, "name", "")
    return f"{object_name}: {name}" if name else object_name


def populate_tree(tree, value, parent="", object_map=None) -> None:
    """Recursively insert nodes into the Treeview control for a configuration model object."""
    if not isinstance(value, CONFIGURATION_OBJECT_TYPES):
        return

    node = tree.insert(parent, "end", text=object_label(value), open=True)
    if object_map is not None:
        object_map[node] = value

    children = []
    component_settings = getattr(value, "component_settings", None)
    if isinstance(component_settings, CONFIGURATION_OBJECT_TYPES):
        children.append(component_settings)
    elif isinstance(component_settings, list):
        children.extend(item for item in component_settings if isinstance(item, CONFIGURATION_OBJECT_TYPES))

    for object_type, attribute_names in CHILD_ATTRIBUTES.items():
        if isinstance(value, object_type):
            for attribute in attribute_names:
                children.append(getattr(value, attribute, []))
            break

    for child in children:
        if isinstance(child, CONFIGURATION_OBJECT_TYPES):
            populate_tree(tree, child, node, object_map)
        elif isinstance(child, list):
            for item in child:
                if isinstance(item, CONFIGURATION_OBJECT_TYPES):
                    populate_tree(tree, item, node, object_map)


def refresh_tree_and_select(tree, object_map, configuration, update_details, close_editor, select_object=None) -> None:
    """Re-populate the tree control from the configuration object and restore selection if requested."""
    tree.delete(*tree.get_children())
    object_map.clear()
    populate_tree(tree, configuration, object_map=object_map)
    selected_item_id = None
    if select_object is not None:
        for item_id, value in object_map.items():
            if value is select_object:
                selected_item_id = item_id
                tree.selection_set(item_id)
                tree.see(item_id)
                break

    close_editor()
    if selected_item_id is None:
        tree.selection_remove(tree.selection())
        update_details()
        return
    update_details()


def find_parent(root, parent_type, child_list_attr, target_child):
    """Search the configuration tree starting at root to find the parent object containing target_child."""
    if isinstance(root, parent_type):
        if any(child is target_child for child in getattr(root, child_list_attr, [])):
            return root
        return None

    if isinstance(root, CONFIGURATION_OBJECT_TYPES):
        for child in vars(root).values():
            if isinstance(child, list):
                for item in child:
                    result = find_parent(item, parent_type, child_list_attr, target_child)
                    if result is not None:
                        return result
            elif isinstance(child, CONFIGURATION_OBJECT_TYPES):
                result = find_parent(child, parent_type, child_list_attr, target_child)
                if result is not None:
                    return result
    return None
