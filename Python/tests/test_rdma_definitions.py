import json
import sys
import unittest
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import rdma_definitions as rdma
from data_sharing_framework_config_api import definitions as d
DATA_PATH = Path(r"tests/config_multidirectional_1_Callea_to_Cotterle_generated.dsf")


class rdma_Import_Tests(unittest.TestCase):
    """Test RDMA definition serialization, deserialization, and fixture imports."""

    def test_channel_initialization_and_defaults(self):
        """Ensure RDMA channel initializes with default RDMA component settings."""
        channel = rdma.Channel(name="RDMA_Channel", unit="V")
        self.assertEqual(channel.name, "RDMA_Channel")
        self.assertEqual(channel.unit, "V")
        self.assertEqual(len(channel.component_settings), 1)
        self.assertEqual(channel.component_settings[0].component, "RDMA")

    def test_channel_round_trip(self):
        """Ensure a channel remains unchanged after a dictionary round trip."""
        channel = rdma.Channel()
        rebuilt = rdma.Channel.from_dict(channel.to_dict())
        self.assertEqual(channel.to_dict(), rebuilt.to_dict())

    def test_transfer_tx_construction(self):
        """Ensure RDMA Transfer TX initializes component settings with local and destination addresses/ports."""
        transfer = rdma.Transfer(
            name="RDMA_TX",
            local_address="10.0.0.1",
            local_port=5000,
            destination_address="10.0.0.2",
            destination_port=5001,
        )
        self.assertEqual(transfer.name, "RDMA_TX")
        self.assertEqual(len(transfer.component_settings), 1)
        cs = transfer.component_settings[0]
        self.assertEqual(cs.component, "RDMA")
        keys = [elem.key for elem in cs.elements]
        self.assertIn("local address", keys)
        self.assertIn("local port", keys)
        self.assertIn("destination address", keys)
        self.assertIn("destination port", keys)

    def test_transfer_rx_construction(self):
        """Ensure RDMA Transfer RX initializes component settings with local address/port only."""
        transfer = rdma.Transfer(
            name="RDMA_RX",
            local_address="10.0.0.1",
            local_port=5000,
        )
        self.assertEqual(transfer.name, "RDMA_RX")
        cs = transfer.component_settings[0]
        keys = [elem.key for elem in cs.elements]
        self.assertIn("local address", keys)
        self.assertIn("local port", keys)
        self.assertNotIn("destination address", keys)

    def test_transfer_round_trip(self):
        """Ensure a transfer remains unchanged after a dictionary round trip."""
        transfer = rdma.Transfer(
            name="RDMA_TX",
            local_address="10.0.0.1",
            local_port=5000,
            destination_address="10.0.0.2",
            destination_port=5001,
        )
        rebuilt = rdma.Transfer.from_dict(transfer.to_dict())
        self.assertEqual(transfer.to_dict(), rebuilt.to_dict())
        self.assertEqual(rebuilt.local_address, "10.0.0.1")
        self.assertEqual(rebuilt.local_port, 5000)
        self.assertEqual(rebuilt.destination_address, "10.0.0.2")
        self.assertEqual(rebuilt.destination_port, 5001)

    def test_transfer_group_construction(self):
        """Ensure RDMA TransferGroup initializes with default RDMA component settings."""
        tg = rdma.TransferGroup(
            name="RDMA_TG",
            direction=d.Direction.TX,
            priority=100,
            decimation=1,
            offset=0,
            timeout_behaviour=0,
            enable_conversion=True,
        )
        self.assertEqual(tg.name, "RDMA_TG")
        self.assertEqual(tg.direction, d.Direction.TX)
        self.assertTrue(tg.enable_conversion)
        self.assertEqual(len(tg.component_settings), 1)
        self.assertEqual(tg.component_settings[0].component, "RDMA")

    def test_transfer_group_round_trip(self):
        """Ensure a transfer group remains unchanged after a dictionary round trip."""
        rx_transfer = rdma.Transfer()
        transfer_group = rdma.TransferGroup(name="transfer", direction=d.Direction.TX, transfers=[rx_transfer])
        rebuilt = rdma.TransferGroup.from_dict(transfer_group.to_dict())
        self.assertEqual(transfer_group.to_dict(), rebuilt.to_dict())

    def test_thread_construction(self):
        """Ensure RDMA Thread initializes with processor binding and RDMA component settings."""
        thread = rdma.Thread(processor=2, priority_offset=5)
        self.assertEqual(thread.processor, 2)
        self.assertEqual(thread.priority_offset, 5)
        self.assertEqual(len(thread.component_settings), 1)
        self.assertEqual(thread.component_settings[0].component, "RDMA")

    def test_thread_round_trip(self):
        """Ensure a thread remains unchanged after a dictionary round trip."""
        thread = rdma.Thread()
        rebuilt = rdma.Thread.from_dict(thread.to_dict())
        self.assertEqual(thread.to_dict(), rebuilt.to_dict())

    def test_plugin_construction(self):
        """Ensure RDMA Plugin initializes components list with ['RDMA']."""
        plugin = rdma.Plugin(name="RDMA_Plugin", priority=10000)
        self.assertEqual(plugin.name, "RDMA_Plugin")
        self.assertEqual(plugin.components, ["RDMA"])
        self.assertEqual(len(plugin.component_settings), 1)
        self.assertEqual(plugin.component_settings[0].component, "RDMA")

    def test_plugin_round_trip(self):
        """Ensure a plugin remains unchanged after a dictionary round trip."""
        plugin = rdma.Plugin()
        rebuilt = rdma.Plugin.from_dict(plugin.to_dict())
        self.assertEqual(plugin.to_dict(), rebuilt.to_dict())

    def test_rdma_configuration_round_trip(self):
        """Ensure a configuration remains unchanged after a round trip."""
        config = d.Configuration()
        rebuilt = d.Configuration.from_dict(config.to_dict())
        self.assertEqual(config.to_dict(), rebuilt.to_dict())

class rdma_benchmark_configuration(unittest.TestCase):
    """Test construction of the expected bidirectional benchmark configuration."""
    
    def test_import_matches_generated_file(self):
            """Ensure the generated configuration imports without changes."""
            with open(DATA_PATH, "r") as f:
                expected_dict = json.load(f)

            config = d.Configuration.from_dict(expected_dict)
            self.assertEqual(config.to_dict(), expected_dict)

    def test_bottomup_configuration(self):
        """Ensure a bottom-up configuration matches the generated fixture."""

        channel = rdma.Channel(name="Channel1")
        
        transfer_tx = rdma.Transfer(
            name="Transfer_Callea_to_Cotterle_Tx",
            local_address="169.254.23.111",
            local_port=5011,
            destination_address="169.254.49.44",
            destination_port=5011,
            channels=[channel],
        )
    
        transfer_rx = rdma.Transfer(
            name="Transfer_Cotterle_to_Callea_Rx",
            local_address="169.254.23.111",
            local_port=5010,
            channels=[channel],
        )

        transfer_group_tx = rdma.TransferGroup(
            name="TransferGroup_Callea_to_Cotterle_Tx",
            direction=d.Direction.TX,
            transfers=[transfer_tx],
        )
    
        transfer_group_rx = rdma.TransferGroup(
            name="TransferGroup_Cotterle_to_Callea_Rx",
            direction=d.Direction.RX,
            transfers=[transfer_rx],
        )

        thread = rdma.Thread(transfer_groups=[transfer_group_tx, transfer_group_rx])

        plugin = rdma.Plugin(name="BidirectionalPlugin", threads=[thread])

        config = d.Configuration(plugins=[plugin])

        with open(DATA_PATH, "r") as f:
            expected_dict = json.load(f)

        self.assertEqual(config.to_dict(), expected_dict)

    def test_topdown_configuration(self):
         self.maxDiff = None  # Show full diff if test fails
         config = d.Configuration()

         plugin = rdma.Plugin(name="BidirectionalPlugin", threads=[])

         thread = rdma.Thread()

         transfer_group_tx = rdma.TransferGroup(
            name="TransferGroup_Callea_to_Cotterle_Tx",
            direction=d.Direction.TX)
         
         transfer_group_rx = rdma.TransferGroup(
            name="TransferGroup_Cotterle_to_Callea_Rx",
            direction=d.Direction.RX)
         
         transfer_tx = rdma.Transfer(
            name="Transfer_Callea_to_Cotterle_Tx",
            local_address="169.254.23.111",
            local_port=5011,
            destination_address="169.254.49.44",
            destination_port=5011)
         
         transfer_rx = rdma.Transfer(
            name="Transfer_Cotterle_to_Callea_Rx",
            local_address="169.254.23.111",
            local_port=5010)

         channel = rdma.Channel(name="Channel1")
    
         transfer_rx.channels = [channel]
         transfer_tx.channels = [channel]
         transfer_group_tx.transfers = [transfer_tx]
         transfer_group_rx.transfers = [transfer_rx]
         thread.transfer_groups = [transfer_group_tx, transfer_group_rx]
         plugin.threads = [thread]
         config.plugins = [plugin]

         with open(DATA_PATH, "r") as f:
                     expected_dict = json.load(f)
         
         self.assertEqual(config.to_dict(), expected_dict)

if __name__ == "__main__":
    unittest.main()
