import json
import sys
import unittest
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import rdma_definitions as rdma

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "config_multidirectional_1_Callea_to_Cotterle_generated.dsf"


class RdmaDefinitionsTests(unittest.TestCase):
    def test_round_trip_reference_configuration(self):
        with DATA_PATH.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        config = rdma.RDMA_Configuration.from_dict(loaded)
        self.assertEqual(loaded, config.getDict())

    def test_transfer_group_rejects_mismatched_direction(self):
        rx_transfer = rdma.Transfer(direction=rdma.Direction.RX, protocol="RDMA")
        with self.assertRaisesRegex(ValueError, "does not match group direction"):
            rdma.TransferGroup(direction=rdma.Direction.TX, protocol="RDMA", transfers=[rx_transfer])

    def test_invalid_plugin_list_type_is_rejected(self):
        config = rdma.RDMA_Configuration()
        with self.assertRaisesRegex(TypeError, "RDMA_Configuration.plugins must be a list"):
            config.plugins = "not-a-list"

    def test_invalid_import_shape_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "Transfer.core must be a dictionary"):
            rdma.Transfer.from_dict({"core": []})

    def test_assignment_validates_nested_types(self):
        transfer = rdma.Transfer(protocol="RDMA")
        with self.assertRaisesRegex(TypeError, "Transfer.channels item 0 must be Channel"):
            transfer.channels = ["channel"]


if __name__ == "__main__":
    unittest.main()
