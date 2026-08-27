"""GUI tests covering session initialization, loading/saving, new configuration, 
protocol tree mutations (add/remove), and direction adaptation.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import definitions as d
from data_sharing_framework_config_api import rdma_definitions as rdma
from data_sharing_framework_config_api import udp_definitions as udp
from data_sharing_framework_config_api.protocol_factory import ProtocolFactory
from data_sharing_framework_config_api.gui import editor_panel, mutations, tree
from data_sharing_framework_config_api.gui.session import ConfigurationSession


class TestGUISessionAndMutations(unittest.TestCase):
    """Test suite covering GUI session management and tree mutations for all supported protocols."""

    def setUp(self) -> None:
        self.session = ConfigurationSession()

    def test_01_session_initialization_and_new_config(self) -> None:
        """Test creating a new empty configuration session."""
        self.session.new_configuration()
        self.assertIsNotNone(self.session.configuration)
        self.assertEqual(len(self.session.configuration.plugins), 0)
        self.assertIsNone(self.session.current_path)
        self.assertEqual(self.session.label_text(), "New configuration")

    def test_file_dialog_directory_uses_executable_then_last_used_location(self) -> None:
        """File dialogs fall back to the executable directory until a file is used."""
        executable_path = Path("C:/application/DSF_GUI.exe")
        with patch("data_sharing_framework_config_api.gui.session.sys.executable", str(executable_path)):
            self.assertEqual(self.session.file_dialog_directory(), executable_path.parent)

        self.session.current_path = Path("C:/configs/used/configuration.dsf")
        self.assertEqual(self.session.file_dialog_directory(), self.session.current_path.parent)

    def test_protocol_lookup_ignores_case_and_whitespace(self) -> None:
        self.session.new_configuration()
        plugin = ProtocolFactory.get_handler(" udp ").create_plugin(name="UDP")
        self.session.configuration.add_plugin(plugin)
        self.assertEqual(mutations.get_protocol_for_element(self.session, plugin), "UDP")

    def test_mixed_configuration_reports_mixed_protocol_state(self) -> None:
        configuration = d.Configuration(plugins=[
            ProtocolFactory.get_handler("RDMA").create_plugin(),
            ProtocolFactory.get_handler("UDP").create_plugin(),
        ])
        session = ConfigurationSession(configuration=configuration)
        self.assertEqual(session.protocol, "MIXED")

    def test_02_multi_protocol_tree_construction_and_mutations(self) -> None:
        """Test building a multi-protocol configuration (RDMA + UDP) from scratch.
        
        Covers all add and remove actions:
        - add_plugin_to_configuration (for both RDMA and UDP)
        - add_thread_to_plugin
        - add_group_to_thread
        - add_transfer_to_group (TX and RX)
        - add_channel_to_transfer
        - remove_channel_from_transfer
        - remove_transfer_from_group
        - remove_group_from_thread
        - remove_thread_from_plugin
        - remove_plugin_from_configuration
        """
        self.session.new_configuration()
        config = self.session.configuration
        dummy_refresh = lambda obj=None: None

        # 1. Add RDMA Plugin
        rdma_handler = ProtocolFactory.get_handler("RDMA")
        rdma_plugin = rdma_handler.create_plugin(name="RDMA_Plugin_1")
        config.add_plugin(rdma_plugin)
        self.assertEqual(len(config.plugins), 1)

        # Add RDMA Thread, Group, Transfers (TX & RX), Channel
        mutations.add_thread_to_plugin(self.session, rdma_plugin, dummy_refresh)
        self.assertEqual(len(rdma_plugin.threads), 1)
        rdma_thread = rdma_plugin.threads[0]

        mutations.add_group_to_thread(self.session, rdma_thread, dummy_refresh)
        self.assertEqual(len(rdma_thread.transfer_groups), 1)
        rdma_group_tx = rdma_thread.transfer_groups[0]
        rdma_group_tx.direction = d.Direction.TX

        # Add RDMA TX Transfer
        mutations.add_transfer_to_group(self.session, rdma_group_tx, dummy_refresh)
        self.assertEqual(len(rdma_group_tx.transfers), 1)
        rdma_transfer_tx = rdma_group_tx.transfers[0]

        # Add RDMA Channel
        mutations.add_channel_to_transfer(self.session, rdma_transfer_tx, dummy_refresh)
        self.assertEqual(len(rdma_transfer_tx.channels), 1)

        # 2. Add UDP Plugin
        udp_handler = ProtocolFactory.get_handler("UDP")
        udp_plugin = udp_handler.create_plugin(name="UDP_Plugin_1")
        config.add_plugin(udp_plugin)
        self.assertEqual(len(config.plugins), 2)

        # Add UDP Thread, Group, Transfers, Channel
        mutations.add_thread_to_plugin(self.session, udp_plugin, dummy_refresh)
        self.assertEqual(len(udp_plugin.threads), 1)
        udp_thread = udp_plugin.threads[0]

        mutations.add_group_to_thread(self.session, udp_thread, dummy_refresh)
        self.assertEqual(len(udp_thread.transfer_groups), 1)
        udp_group_rx = udp_thread.transfer_groups[0]
        udp_group_rx.direction = d.Direction.RX

        # Add UDP RX Transfer
        mutations.add_transfer_to_group(self.session, udp_group_rx, dummy_refresh)
        self.assertEqual(len(udp_group_rx.transfers), 1)
        udp_transfer_rx = udp_group_rx.transfers[0]

        # Add UDP Channel
        mutations.add_channel_to_transfer(self.session, udp_transfer_rx, dummy_refresh)
        self.assertEqual(len(udp_transfer_rx.channels), 1)

        # Verify protocol inheritance helpers
        self.assertEqual(mutations.get_protocol_for_element(self.session, rdma_transfer_tx), "RDMA")
        self.assertEqual(mutations.get_protocol_for_element(self.session, udp_transfer_rx), "UDP")

        # Verify removal actions
        # Remove RDMA channel
        mutations.remove_channel_from_transfer(config, rdma_transfer_tx.channels[0], dummy_refresh)
        self.assertEqual(len(rdma_transfer_tx.channels), 0)

        # Remove UDP transfer
        mutations.remove_transfer_from_group(config, udp_transfer_rx, dummy_refresh)
        self.assertEqual(len(udp_group_rx.transfers), 0)

        # Remove UDP group
        mutations.remove_group_from_thread(config, udp_group_rx, dummy_refresh)
        self.assertEqual(len(udp_thread.transfer_groups), 0)

        # Remove UDP thread
        mutations.remove_thread_from_plugin(config, udp_thread, dummy_refresh)
        self.assertEqual(len(udp_plugin.threads), 0)

        # Remove UDP plugin
        mutations.remove_plugin_from_configuration(config, udp_plugin, dummy_refresh)
        self.assertEqual(len(config.plugins), 1)
        self.assertEqual(config.plugins[0].name, "RDMA_Plugin_1")

    def test_03_settings_field_edits_and_direction_adaptation(self) -> None:
        """Test editing form field attributes and direction adaptation on TransferGroup."""
        # Test editing attributes
        plugin = d.Plugin(name="OldName", priority=1000)
        editor_panel.apply_field_value(plugin, "name", "text", "NewName")
        self.assertEqual(plugin.name, "NewName")

        editor_panel.apply_field_value(plugin, "priority", "int", "2000")
        self.assertEqual(plugin.priority, 2000)

        # Test TransferGroup direction adaptation (RX -> TX -> RX)
        group = d.TransferGroup(name="Group1", direction=d.Direction.RX)
        transfer = rdma.Transfer(name="Tr1", local_address="192.168.1.50", local_port=6000)
        group.add_transfer(transfer)

        # Adapt to TX
        group.direction = d.Direction.TX
        editor_panel.adapt_transfers_to_direction(group)
        self.assertEqual(transfer.destination_address, "192.168.1.50")
        self.assertEqual(transfer.destination_port, 6000)

        # Adapt back to RX
        group.direction = d.Direction.RX
        editor_panel.adapt_transfers_to_direction(group)
        self.assertEqual(transfer.local_address, "192.168.1.50")
        self.assertEqual(transfer.local_port, 6000)

    def test_04_save_and_load_configuration_round_trip(self) -> None:
        """Test saving a multi-protocol configuration to disk and loading it back."""
        self.session.new_configuration()
        config = self.session.configuration

        # Create multi-protocol plugins
        rdma_handler = ProtocolFactory.get_handler("RDMA")
        udp_handler = ProtocolFactory.get_handler("UDP")

        rdma_plugin = rdma_handler.create_plugin(name="RDMA_Plugin")
        udp_plugin = udp_handler.create_plugin(name="UDP_Plugin")
        rdma_plugin.add_thread(rdma.Thread())
        udp_plugin.add_thread(udp.Thread())

        config.add_plugin(rdma_plugin)
        config.add_plugin(udp_plugin)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_config.dsf"

            # Save file
            saved_path = self.session.save_file(file_path)
            self.assertTrue(saved_path.exists())
            self.assertEqual(self.session.current_path, saved_path.resolve())

            # Clear and reload
            new_session = ConfigurationSession()
            new_session.load_file(saved_path)

            self.assertEqual(len(new_session.configuration.plugins), 2)
            self.assertEqual(new_session.configuration.plugins[0].name, "RDMA_Plugin")
            self.assertEqual(new_session.configuration.plugins[1].name, "UDP_Plugin")
            self.assertIsInstance(new_session.configuration.plugins[0], rdma.Plugin)
            self.assertIsInstance(new_session.configuration.plugins[1], udp.Plugin)
            self.assertIsInstance(new_session.configuration.plugins[0].threads[0], rdma.Thread)
            self.assertIsInstance(new_session.configuration.plugins[1].threads[0], udp.Thread)

    def test_05_gui_app_launch_headless(self) -> None:
        """Test GUI window launch and menu construction in headless mode."""
        try:
            import tkinter as tk
            from tkinter import ttk
            from data_sharing_framework_config_api.gui import app

            root = tk.Tk()
            root.withdraw()  # Keep hidden during test

            session = ConfigurationSession()
            session.new_configuration()

            file_path_label = ttk.Label(root, text="Test")
            details_text = tk.Text(root)
            tree_view = ttk.Treeview(root)

            # Test launching actions programmatically without errors
            with patch.object(app.dialogs, "prompt_protocol_selection") as prompt_protocol:
                app.new_action(tree_view, file_path_label, {}, details_text, root, session)
            self.assertEqual(session.label_text(), "New configuration")
            self.assertEqual(len(session.configuration.plugins), 0)
            prompt_protocol.assert_not_called()

            root.destroy()
        except tk.TclError:
            self.skipTest("Tkinter GUI launch skipped (headless environment without DISPLAY).")

    def test_save_failure_preserves_existing_file(self) -> None:
        """A serialization failure must not truncate an existing configuration."""
        self.session.new_configuration()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "existing.dsf"
            original = '{"original": true}'
            file_path.write_text(original, encoding="utf-8")

            class BrokenConfiguration:
                def to_dict(self):
                    raise TypeError("cannot serialize")

            self.session.configuration = BrokenConfiguration()
            with self.assertRaises(TypeError):
                self.session.save_file(file_path)
            self.assertEqual(file_path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
