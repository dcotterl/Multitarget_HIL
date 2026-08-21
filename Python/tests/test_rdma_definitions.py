import json
import sys
import unittest
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import rdma_definitions as rdma

DATA_PATH = Path(r"tests/config_multidirectional_1_Callea_to_Cotterle_generated.dsf")


class Rdma_Import_Tests(unittest.TestCase):
    """Test RDMA definition serialization, deserialization, and fixture imports."""

    def test_channel_round_trip(self):
        """Ensure a channel remains unchanged after a dictionary round trip."""
        channel = rdma.Channel()
        rebuilt = rdma.Channel.from_dict(channel.getDict())
        self.assertEqual(channel.getDict(), rebuilt.getDict())

    def test_transfer_round_trip(self):
        """Ensure a transfer remains unchanged after a dictionary round trip."""
        transfer = rdma.Transfer(protocol="RDMA")
        rebuilt = rdma.Transfer.from_dict(transfer.getDict())
        self.assertEqual(transfer.getDict(), rebuilt.getDict())

    def test_thread_round_trip(self):
            """Ensure a thread remains unchanged after a dictionary round trip."""
            thread = rdma.Thread()
            rebuilt = rdma.Thread.from_dict(thread.getDict())
            self.assertEqual(thread.getDict(), rebuilt.getDict())
    
    def test_plugin_round_trip(self):
        """Ensure a plugin remains unchanged after a dictionary round trip."""
        plugin = rdma.Plugin()
        rebuilt = rdma.Plugin.from_dict(plugin.getDict())
        self.assertEqual(plugin.getDict(), rebuilt.getDict())

    def test_transfer_group_round_trip(self):
        """Ensure a transfer group remains unchanged after a dictionary round trip."""
        rx_transfer = rdma.Transfer(protocol="RDMA")
        transfer_group = rdma.TransferGroup(protocol="RDMA", transfers=[rx_transfer])
        rebuilt = rdma.TransferGroup.from_dict(transfer_group.getDict())
        self.assertEqual(transfer_group.getDict(), rebuilt.getDict())

    def test_rdma_configuration_round_trip(self):
        """Ensure an RDMA configuration remains unchanged after a round trip."""
        config = rdma.RDMA_Configuration()
        rebuilt = rdma.RDMA_Configuration.from_dict(config.getDict())
        self.assertEqual(config.getDict(), rebuilt.getDict())

    def test_import_matches_generated_file(self):
            """Ensure the generated configuration imports without changes."""
            with open(DATA_PATH, "r") as f:
                expected_dict = json.load(f)

            config = rdma.RDMA_Configuration.from_dict(expected_dict)
            self.assertEqual(config.getDict(), expected_dict)

class Rdma_benchmark_configuration(unittest.TestCase):
    """Test construction of the expected bidirectional benchmark configuration."""

    def test_bottomup_configuration(self):
        """Ensure a bottom-up configuration matches the generated fixture."""

        channel = rdma.Channel(name="Channel1", protocol="RDMA")
        
        transfer_tx = rdma.Transfer(
            name="Transfer_Callea_to_Cotterle_Tx",
            protocol="RDMA",
            local_address="169.254.23.111",
            local_port=5011,
            destination_address="169.254.49.44",
            destination_port=5011,
            channels=[channel],
        )
    
        transfer_rx = rdma.Transfer(
            name="Transfer_Cotterle_to_Callea_Rx",
            protocol="RDMA",
            local_address="169.254.23.111",
            local_port=5010,
            channels=[channel],
        )

        transfer_group_tx = rdma.TransferGroup(
            name="TransferGroup_Callea_to_Cotterle_Tx",
            direction=rdma.Direction.TX,
            protocol="RDMA",
            transfers=[transfer_tx],
        )
    
        transfer_group_rx = rdma.TransferGroup(
            name="TransferGroup_Cotterle_to_Callea_Rx",
            direction=rdma.Direction.RX,
            protocol="RDMA",
            transfers=[transfer_rx],
        )

        thread = rdma.Thread(protocol="RDMA", transfer_groups=[transfer_group_tx, transfer_group_rx])

        plugin = rdma.Plugin(name="BidirectionalPlugin", protocol="RDMA", threads=[thread])

        config = rdma.RDMA_Configuration(plugins=[plugin])

        with open(DATA_PATH, "r") as f:
            expected_dict = json.load(f)

        self.assertEqual(config.getDict(), expected_dict)

    def test_topdown_configuration(self):
         self.maxDiff = None  # Show full diff if test fails
         config = rdma.RDMA_Configuration()

         plugin = rdma.Plugin(name="BidirectionalPlugin", threads=[], protocol="RDMA")

         thread = rdma.Thread(protocol="RDMA")

         transfer_group_tx = rdma.TransferGroup(
            name="TransferGroup_Callea_to_Cotterle_Tx",
            direction=rdma.Direction.TX,
            protocol="RDMA")
         
         transfer_group_rx = rdma.TransferGroup(
            name="TransferGroup_Cotterle_to_Callea_Rx",
            direction=rdma.Direction.RX,
            protocol="RDMA")
         
         transfer_tx = rdma.Transfer(
            name="Transfer_Callea_to_Cotterle_Tx",
            protocol="RDMA",
            local_address="169.254.23.111",
            local_port=5011,
            destination_address="169.254.49.44",
            destination_port=5011)
         
         transfer_rx = rdma.Transfer(
            name="Transfer_Cotterle_to_Callea_Rx",
            protocol="RDMA",
            local_address="169.254.23.111",
            local_port=5010)

         channel = rdma.Channel(name="Channel1", protocol="RDMA")
    
         transfer_rx.channels = [channel]
         transfer_tx.channels = [channel]
         transfer_group_tx.transfers = [transfer_tx]
         transfer_group_rx.transfers = [transfer_rx]
         thread.transfer_groups = [transfer_group_tx, transfer_group_rx]
         plugin.threads = [thread]
         config.plugins = [plugin]

         with open(DATA_PATH, "r") as f:
                     expected_dict = json.load(f)
         
         self.assertEqual(config.getDict(), expected_dict)

if __name__ == "__main__":
    unittest.main()
