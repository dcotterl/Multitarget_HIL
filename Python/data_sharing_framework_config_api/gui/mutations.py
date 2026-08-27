"""GUI tree mutation actions and context menu handlers."""

from __future__ import annotations

import logging
import tkinter as tk

from data_sharing_framework_config_api import definitions
from data_sharing_framework_config_api.protocol_factory import ProtocolFactory
from data_sharing_framework_config_api.gui import dialogs, editor_panel
from data_sharing_framework_config_api.gui.state import editor_state
from data_sharing_framework_config_api.gui.tree import find_parent, refresh_tree_and_select

logger = logging.getLogger(__name__)


def find_ancestor_plugin(configuration: definitions.Configuration, target) -> definitions.Plugin | None:
    """Find the containing Plugin for a given target object in the tree hierarchy."""
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
            comp = str(plugin.components[0]).upper()
            if comp in ProtocolFactory.get_available_protocols():
                return comp
        if getattr(plugin, "component_settings", None):
            for cs in plugin.component_settings:
                component = str(cs.component).upper()
                if component in ProtocolFactory.get_available_protocols():
                    return component
    return getattr(session, "protocol", "RDMA")


def run_tree_mutation_with_unsaved_changes(tree, details_text, root, mutate_action):
    """Execute a tree mutation callback after confirming or discarding any unsaved form field changes."""
    state = editor_state(details_text)
    if state.modify_panel is not None and editor_panel.has_unsaved_changes(details_text):
        dialogs.prompt_unsaved_changes(
            tree, details_text, root, None, on_continue=mutate_action, close_editor_fn=editor_panel.close_inline_editor
        )
        return
    if state.modify_panel is not None:
        editor_panel.close_inline_editor(details_text)
    mutate_action()


def add_channel_to_transfer(session, selected_transfer, refresh):
    """Add a new protocol-specific Channel to selected_transfer and refresh UI."""
    protocol = get_protocol_for_element(session, selected_transfer)
    logger.info("Adding Channel to Transfer('%s') (Protocol: %s)", selected_transfer.name, protocol)
    handler = ProtocolFactory.get_handler(protocol)
    channel_number = len(selected_transfer.channels) + 1
    channel = handler.create_channel(name=f"Channel {channel_number}")
    selected_transfer.add_channel(channel)
    refresh(selected_transfer)


def remove_channel_from_transfer(configuration, selected_channel, refresh):
    """Remove selected_channel from its parent Transfer and refresh UI."""
    parent_transfer = find_parent(configuration, definitions.Transfer, "channels", selected_channel)
    if parent_transfer is None:
        logger.warning("Could not find parent Transfer for selected channel '%s'", getattr(selected_channel, "name", ""))
        return
    logger.info("Removing Channel('%s') from Transfer('%s')", getattr(selected_channel, "name", ""), parent_transfer.name)
    parent_transfer.channels = [channel for channel in parent_transfer.channels if channel is not selected_channel]
    refresh(parent_transfer)


def add_transfer_to_group(session, selected_group, refresh):
    """Add a new protocol-specific Transfer to selected_group and refresh UI."""
    protocol = get_protocol_for_element(session, selected_group)
    logger.info("Adding Transfer to TransferGroup('%s') (Direction: %s, Protocol: %s)", selected_group.name, selected_group.direction.name, protocol)
    handler = ProtocolFactory.get_handler(protocol)
    transfer_number = len(selected_group.transfers) + 1
    transfer = handler.create_transfer(name=f"Transfer {transfer_number}", direction=selected_group.direction)
    selected_group.add_transfer(transfer)
    refresh(selected_group)


def remove_transfer_from_group(configuration, selected_transfer, refresh):
    """Remove selected_transfer from its parent TransferGroup and refresh UI."""
    parent_group = find_parent(configuration, definitions.TransferGroup, "transfers", selected_transfer)
    if parent_group is None:
        logger.warning("Could not find parent TransferGroup for selected transfer '%s'", getattr(selected_transfer, "name", ""))
        return
    logger.info("Removing Transfer('%s') from TransferGroup('%s')", getattr(selected_transfer, "name", ""), parent_group.name)
    parent_group.transfers = [transfer for transfer in parent_group.transfers if transfer is not selected_transfer]
    refresh(parent_group)


def add_group_to_thread(session, selected_thread, refresh):
    """Add a new protocol-specific TransferGroup to selected_thread and refresh UI."""
    protocol = get_protocol_for_element(session, selected_thread)
    logger.info("Adding TransferGroup to Thread(processor=%d) (Protocol: %s)", selected_thread.processor, protocol)
    handler = ProtocolFactory.get_handler(protocol)
    group_number = len(selected_thread.transfer_groups) + 1
    group = handler.create_transfer_group(name=f"Transfer Group {group_number}", direction=definitions.Direction.TX)
    selected_thread.add_transfer_group(group)
    refresh(selected_thread)


def remove_group_from_thread(configuration, selected_group, refresh):
    """Remove selected_group from its parent Thread and refresh UI."""
    parent_thread = find_parent(configuration, definitions.Thread, "transfer_groups", selected_group)
    if parent_thread is None:
        logger.warning("Could not find parent Thread for selected group '%s'", getattr(selected_group, "name", ""))
        return
    logger.info("Removing TransferGroup('%s') from Thread(processor=%d)", getattr(selected_group, "name", ""), parent_thread.processor)
    parent_thread.transfer_groups = [group for group in parent_thread.transfer_groups if group is not selected_group]
    refresh(parent_thread)


def add_thread_to_plugin(session, selected_plugin, refresh):
    """Add a new protocol-specific Thread to selected_plugin and refresh UI."""
    protocol = get_protocol_for_element(session, selected_plugin)
    logger.info("Adding Thread to Plugin('%s') (Protocol: %s)", selected_plugin.name, protocol)
    handler = ProtocolFactory.get_handler(protocol)
    thread = handler.create_thread(processor=-2)
    selected_plugin.add_thread(thread)
    refresh(selected_plugin)


def remove_thread_from_plugin(configuration, selected_thread, refresh):
    """Remove selected_thread from its parent Plugin and refresh UI."""
    parent_plugin = find_parent(configuration, definitions.Plugin, "threads", selected_thread)
    if parent_plugin is None:
        logger.warning("Could not find parent Plugin for selected thread")
        return
    logger.info("Removing Thread(processor=%d) from Plugin('%s')", selected_thread.processor, parent_plugin.name)
    parent_plugin.threads = [thread for thread in parent_plugin.threads if thread is not selected_thread]
    refresh(parent_plugin)


def add_plugin_to_configuration(session, selected_configuration, refresh, root):
    """Prompt for protocol selection, create a new Plugin using ProtocolFactory, and refresh UI."""
    protocol = dialogs.prompt_protocol_selection(root, title="Select Protocol", message="Select protocol for new plugin:")
    if protocol is None:
        logger.info("User cancelled protocol selection for new plugin")
        return

    logger.info("Adding Plugin with protocol '%s' to Configuration", protocol)
    handler = ProtocolFactory.get_handler(protocol)
    plugin_number = len(selected_configuration.plugins) + 1
    plugin = handler.create_plugin(name=f"Plugin {plugin_number}")
    selected_configuration.add_plugin(plugin)
    refresh(selected_configuration)


def remove_plugin_from_configuration(configuration, selected_plugin, refresh):
    """Remove selected_plugin from configuration and refresh UI."""
    if selected_plugin not in configuration.plugins:
        logger.warning("Selected plugin '%s' not found in configuration", getattr(selected_plugin, "name", ""))
        return
    logger.info("Removing Plugin('%s') from Configuration", getattr(selected_plugin, "name", ""))
    configuration.plugins = [plugin for plugin in configuration.plugins if plugin is not selected_plugin]
    refresh(configuration)


def show_context_menu(event, tree, object_map, details_text, right_frame, root, session):
    """Construct and display a context menu for treeview right-click events based on selected node type."""
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
            lambda: editor_panel.update_details_text(tree, details_text, object_map),
            lambda: editor_panel.close_inline_editor(details_text),
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
