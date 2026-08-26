"""Tests for :mod:`udp_definitions`."""
import json
import sys
import unittest
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import udp_definitions as udp
from data_sharing_framework_config_api import definitions as d


DATA_PATH = Path(r"tests/udp_simpleloopback.dsf")


class testIpConversion(unittest.TestCase):
    """Tests for IP address conversion helpers."""

    def test_string_to_ip(self):
        self.assertEqual(udp.string_to_ip("2130706433"), "127.0.0.1")

    def test_ip_to_string(self):
        ip = "127.0.0.1"

        self.assertEqual(udp.ip_to_string(ip), "2130706433")

class udp_Import_Tests(unittest.TestCase):
    """Test udp definition serialization, deserialization, and fixture imports."""

    def test_channel_round_trip(self):
        """Ensure a channel remains unchanged after a dictionary round trip."""
        channel = udp.Channel("Channel1", "V")
        rebuilt = udp.Channel.from_dict(channel.getDict())
        self.assertEqual(channel.getDict(), rebuilt.getDict())

    def test_transfer_tx_round_trip(self):
        """Ensure a transfer remains unchanged after a dictionary round trip."""
        transfer = udp.Transfer(name="Transfer", 
                                destination_address="127.0.0.1", 
                                destination_port=50001,
                                channels=[udp.Channel("Channel1", "V")])
        
        rebuilt = udp.Transfer.from_dict(transfer.getDict())
        self.assertEqual(transfer.getDict(), rebuilt.getDict())

    def test_transfer_rx_round_trip(self):
            """Ensure a transfer remains unchanged after a dictionary round trip."""
            transfer = udp.Transfer(name="Transfer", 
                                    local_address="127.0.0.1", 
                                    local_port=50001,
                                    channels=[udp.Channel("Channel1", "V")])
            
            rebuilt = udp.Transfer.from_dict(transfer.getDict())
            self.assertEqual(transfer.getDict(), rebuilt.getDict())

    def test_transfer_group_tx_round_trip(self):
            """Ensure a transfer group remains unchanged after a dictionary round trip."""
            transfer_group_tx = udp.TransferGroup( name = "TransferGroup_tx",
                                                   direction = d.Direction.TX)
            
            rebuilt = udp.TransferGroup.from_dict(transfer_group_tx.getDict())
            self.assertEqual(transfer_group_tx.getDict(), rebuilt.getDict())

    def test_transfer_group_rx_round_trip(self):
            """Ensure a transfer group remains unchanged after a dictionary round trip."""
            transfer_group_rx = udp.TransferGroup( name = "TransferGroup_rx",
                                                   direction = d.Direction.RX)
            
            rebuilt = udp.TransferGroup.from_dict(transfer_group_rx.getDict())
            self.assertEqual(transfer_group_rx.getDict(), rebuilt.getDict())

    def test_thread_round_trip(self):
            """Ensure a thread remains unchanged after a dictionary round trip."""
            thread = udp.Thread(local_address = "127.0.0.1",
                                local_port = 50001)
            rebuilt = udp.Thread.from_dict(thread.getDict())
            self.assertEqual(thread.getDict(), rebuilt.getDict())

    def test_plugin_round_trip(self):
        """Ensure a plugin remains unchanged after a dictionary round trip."""
        plugin = udp.Plugin(name = "Plugin")
        rebuilt = udp.Plugin.from_dict(plugin.getDict())
        self.assertEqual(plugin.getDict(), rebuilt.getDict())
    
    def test_udp_configuration_round_trip(self):
        """Ensure an udp configuration remains unchanged after a round trip."""
        config = d.Configuration()
        rebuilt = d.Configuration.from_dict(config.getDict())
        self.assertEqual(config.getDict(), rebuilt.getDict())



class udp_benchmark_configuration(unittest.TestCase):
     def makeChannel(self):
        return udp.Channel(name="Channel", unit="V")
     def makeTransferTx(self):
        return udp.Transfer(name = "Transfer",
                            destination_address = "127.0.0.1",
                            destination_port = 50001,
                            channels = [self.makeChannel()])
     def makeTransferRx(self):
        return udp.Transfer(name = "Transfer",
                            local_address = "127.0.0.1",
                            local_port = 50000,
                            channels = [self.makeChannel()])
     def makeTransferGroupTx(self):
        return udp.TransferGroup(name = "Group",
                                 direction = d.Direction.TX,
                                 transfers = [self.makeTransferTx()])
     def makeTransferGroupRx(self):
        return udp.TransferGroup(name = "Group",
                                 direction = d.Direction.RX,
                                 transfers = [self.makeTransferRx()])
     def makeThreadTx(self):
        return udp.Thread(local_address = "127.0.0.1",
                          local_port = 50000,
                          transfer_groups = [self.makeTransferGroupTx()])
     def makeThreadRx(self):
        return udp.Thread(local_address = "127.0.0.1",
                          local_port = 50001,
                          transfer_groups = [self.makeTransferGroupRx()])
     def makePlugin(self):
        return udp.Plugin(name = "Plugin",
                          threads = [self.makeThreadTx(), self.makeThreadRx()])
     def makeConfiguration(self):
        return d.Configuration(plugins = [self.makePlugin()])

     def test_import_matches_generated_file(self):
            """Ensure the generated configuration imports without changes."""
            with open(DATA_PATH, "r") as f:
                expected_dict = json.load(f)

            config = d.Configuration.from_dict(expected_dict)
            self.assertEqual(config.getDict(), expected_dict)

     def test_bottomup_configuration(self):
        """Ensure a bottom-up configuration matches the generated fixture."""

        channel = udp.Channel(name="Channel", unit="V")
        
        transfer_tx = udp.Transfer(name="Transfer",
                                   destination_address= udp.string_to_ip("2130706433"),
                                   destination_port=50001,
                                   channels=[channel],
                                  )

        transfer_rx = udp.Transfer(name="Transfer",
                                   local_address= udp.string_to_ip("2130706433"),
                                   local_port=50000,
                                   channels=[channel],
                                  )
        transfer_group_tx = udp.TransferGroup(name="Group",
                                              direction=d.Direction.TX,
                                              transfers=[transfer_tx],
                                             )   
        transfer_group_rx = udp.TransferGroup(name="Group",
                                              direction=d.Direction.RX,
                                              transfers=[transfer_rx],
                                             )
        thread_tx = udp.Thread(local_address= udp.string_to_ip("2130706433"),
                               local_port=50000,
                               transfer_groups=[transfer_group_tx],
                            )

        thread_rx = udp.Thread(local_address= udp.string_to_ip("2130706433"),
                               local_port=50001,
                               transfer_groups=[transfer_group_rx],
                            )

        plugin = udp.Plugin(name="Plugin",
                            threads=[thread_tx, thread_rx],
                        )

        config = d.Configuration(plugins=[plugin])

        with open(DATA_PATH, "r") as f:
            expected_dict = json.load(f)

        self.assertEqual(config.getDict(), expected_dict)

     def test_import_channel(self):
        with open(DATA_PATH, "r") as f:
            expected_dict = json.load(f)

        config = d.Configuration.from_dict(expected_dict)
        plugin = config.plugins[0]
        thread_tx = plugin.threads[0]
        transfer_group_tx = thread_tx.transfer_groups[0]
        transfer_tx = transfer_group_tx.transfers[0]
        channel = transfer_tx.channels[0]

        self.assertEqual(channel.getDict(), self.makeChannel().getDict())

     def test_import_transfer_tx(self):
        with open(DATA_PATH, "r") as f:
            expected_dict = json.load(f)

        config = d.Configuration.from_dict(expected_dict)
        plugin = config.plugins[0]
        thread_tx = plugin.threads[0]
        transfer_group_tx = thread_tx.transfer_groups[0]
        transfer_tx = transfer_group_tx.transfers[0]

        transfer_test = self.makeTransferTx()

        self.assertEqual(transfer_tx.getDict(), transfer_test.getDict())

     def test_import_transfer_rx(self):
            with open(DATA_PATH, "r") as f:
                expected_dict = json.load(f)
    
            config = d.Configuration.from_dict(expected_dict)
            plugin = config.plugins[0]
            thread_rx = plugin.threads[1]
            transfer_group_rx = thread_rx.transfer_groups[0]
            transfer_rx = transfer_group_rx.transfers[0]
    
            transfer_test = self.makeTransferRx()
    
            self.assertEqual(transfer_rx.getDict(), transfer_test.getDict())

     def test_import_transfer_group_tx(self):
        with open(DATA_PATH, "r") as f:
            expected_dict = json.load(f)

        config = d.Configuration.from_dict(expected_dict)
        plugin = config.plugins[0]
        thread_tx = plugin.threads[0]
        transfer_group_tx = thread_tx.transfer_groups[0]

        transfer_group_test = self.makeTransferGroupTx()

        self.assertEqual(transfer_group_tx.getDict(), transfer_group_test.getDict())

     def test_import_transfer_group_rx(self):
        with open(DATA_PATH, "r") as f:
            expected_dict = json.load(f)

        config = d.Configuration.from_dict(expected_dict)
        plugin = config.plugins[0]
        thread_rx = plugin.threads[1]
        transfer_group_rx = thread_rx.transfer_groups[0]

        transfer_group_test = self.makeTransferGroupRx()

        self.assertEqual(transfer_group_rx.getDict(), transfer_group_test.getDict())

     def test_import_thread_tx(self):
        with open(DATA_PATH, "r") as f:
            expected_dict = json.load(f)

        config = d.Configuration.from_dict(expected_dict)
        plugin = config.plugins[0]
        thread_tx = plugin.threads[0]

        thread_test = self.makeThreadTx()

        self.assertEqual(thread_tx.getDict(), thread_test.getDict())

     def test_import_thread_rx(self):
        with open(DATA_PATH, "r") as f:
            expected_dict = json.load(f)

        config = d.Configuration.from_dict(expected_dict)
        plugin = config.plugins[0]
        thread_rx = plugin.threads[1]

        thread_test = self.makeThreadRx()

        self.assertEqual(thread_rx.getDict(), thread_test.getDict())

     def test_import_plugin(self):
        with open(DATA_PATH, "r") as f:
            expected_dict = json.load(f)

        config = d.Configuration.from_dict(expected_dict)
        plugin = config.plugins[0]

        plugin_test = self.makePlugin()

        self.assertEqual(plugin.getDict(), plugin_test.getDict())
    
     def test_import_configuration(self):
        with open(DATA_PATH, "r") as f:
            expected_dict = json.load(f)

        config = d.Configuration.from_dict(expected_dict)

        config_test = self.makeConfiguration()

        self.assertEqual(config.getDict(), config_test.getDict())