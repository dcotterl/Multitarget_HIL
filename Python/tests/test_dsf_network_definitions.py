import inspect
import sys
import unittest
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from target_configuration_utilities.dsf_network_definitions import Target, DataSharingNetworkTopology
from data_sharing_framework_config_api import definitions as d

class testTargets(unittest.TestCase):
    """Contract tests for the public API of ``Target``.

    These tests deliberately use the class' signatures rather than duplicating
    constructor details here, so they remain useful when optional Target
    attributes are added.
    """

    def test_target_is_a_class_with_an_inspectable_constructor(self):
        self.assertTrue(inspect.isclass(Target))
        signature = inspect.signature(Target)
        self.assertIsNotNone(signature)

        # Every required constructor parameter must be explicitly documented
        # by the callable signature (and not hidden behind *args/**kwargs).
        for parameter in signature.parameters.values():
            if parameter.default is inspect.Parameter.empty:
                self.assertNotEqual(
                    parameter.kind,
                    inspect.Parameter.VAR_POSITIONAL,
                )
                self.assertNotEqual(
                    parameter.kind,
                    inspect.Parameter.VAR_KEYWORD,
                )

    def test_all_public_target_functions_are_callable(self):
        public_functions = [
            (name, member)
            for name, member in inspect.getmembers(Target, inspect.isroutine)
            if not name.startswith("_")
        ]

        for name, member in public_functions:
            with self.subTest(function=name):
                self.assertTrue(callable(member))
                signature = inspect.signature(member)
                self.assertIsNotNone(signature)
                for parameter in signature.parameters.values():
                    self.assertNotEqual(
                        parameter.kind,
                        inspect.Parameter.POSITIONAL_ONLY,
                    )

    def test_target_public_properties_are_descriptors(self):
        for name, member in inspect.getmembers(Target):
            if name.startswith("_"):
                continue
            if isinstance(member, property):
                with self.subTest(property=name):
                    self.assertTrue(member.fget is not None)

class testTargetMethods(unittest.TestCase):
    """Tests for the methods of the ``Target`` class."""

    def test_target_initialization(self):
        target = Target("Target_1", "1.1.1.1")
        self.assertEqual(target.name, "Target_1")
        self.assertEqual(target.main_ip, "1.1.1.1")

    def test_add_and_remove_input_interface(self):
        target = Target("Target_1", "1.1.1.1")
        target.add_input_interface("127.0.0.1", 8080, d.Protocols.UDP)
        self.assertIn({"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP}, target.input_interfaces)
        target.remove_input_interface("127.0.0.1", 8080, d.Protocols.UDP)
        self.assertNotIn({"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP}, target.input_interfaces)

    def test_add_and_remove_output_interface(self):
        target = Target("Target_1", "1.1.1.1")
        target.add_output_interface("127.0.0.1", 8080, d.Protocols.UDP)
        self.assertIn({"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP}, target.output_interfaces)
        target.remove_output_interface("127.0.0.1", 8080, d.Protocols.UDP)
        self.assertNotIn({"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP}, target.output_interfaces)

    def test_target_str_representation(self):
        target = Target("Target_1", "1.1.1.1")
        target.add_input_interface("127.0.0.1", 8080, d.Protocols.UDP)
        target.add_output_interface("127.0.0.1", 8080, d.Protocols.UDP)
        target_str = str(target)
        self.assertIn("Target_1", target_str)
        self.assertIn("1.1.1.1", target_str)
        self.assertIn("127.0.0.1", target_str)
        self.assertIn("8080", target_str)
        self.assertIn("UDP", target_str)


class testDataSharingNetworkTopology(unittest.TestCase):
    """Contract tests for the public API of the network topology class."""

    def test_topology_is_a_class_with_an_inspectable_constructor(self):
        self.assertTrue(inspect.isclass(DataSharingNetworkTopology))
        signature = inspect.signature(DataSharingNetworkTopology)
        self.assertIsNotNone(signature)

        for parameter in signature.parameters.values():
            if parameter.default is inspect.Parameter.empty:
                self.assertNotEqual(
                    parameter.kind,
                    inspect.Parameter.VAR_POSITIONAL,
                )
                self.assertNotEqual(
                    parameter.kind,
                    inspect.Parameter.VAR_KEYWORD,
                )

    def test_all_public_topology_functions_are_callable(self):
        public_functions = [
            (name, member)
            for name, member in inspect.getmembers(
                DataSharingNetworkTopology, inspect.isroutine
            )
            if not name.startswith("_")
        ]

        for name, member in public_functions:
            with self.subTest(function=name):
                self.assertTrue(callable(member))
                signature = inspect.signature(member)
                self.assertIsNotNone(signature)
                for parameter in signature.parameters.values():
                    self.assertNotEqual(
                        parameter.kind,
                        inspect.Parameter.POSITIONAL_ONLY,
                    )

class testNodeLink(unittest.TestCase):
    """Tests for the node link representation within the network topology."""

    def test_node_link_creation(self):
        source_target = Target("Source", "1.1.1.1")
        destination_target = Target("Destination", "2.2.2.2")
        source_interface = {"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP}
        destination_interface = {"ip": "127.0.0.2", "port": 8080, "protocol": d.Protocols.UDP}

        source_target.add_output_interface("127.0.0.1", 8080, d.Protocols.UDP)
        destination_target.add_input_interface("127.0.0.2", 8080, d.Protocols.UDP)

        topology = DataSharingNetworkTopology()
        topology.add_node_link(
            source_target=source_target,
            source_interface=source_interface,
            destination_target=destination_target,
            destination_interface=destination_interface,
        )

        self.assertEqual(len(topology.node_links), 1)
        link = topology.node_links[0]
        self.assertEqual(link["source_target"], source_target)
        self.assertEqual(link["source_interface"], source_interface)
        self.assertEqual(link["destination_target"], destination_target)
        self.assertEqual(link["destination_interface"], destination_interface)

    def test_node_link_creation_missing_arguments_raises(self):
        source_target = Target("Source", "1.1.1.1")
        source_interface = {"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP}

        topology = DataSharingNetworkTopology()
        with self.assertRaises(TypeError):
            topology.add_node_link(
                source_target=source_target,
                source_interface=source_interface,
            )

    def test_node_link_creation_wrong_target_type_raises(self):
        source_interface = {"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP}
        destination_interface = {"ip": "127.0.0.2", "port": 8080, "protocol": d.Protocols.UDP}

        topology = DataSharingNetworkTopology()
        with self.assertRaises((TypeError, AttributeError)):
            topology.add_node_link(
                source_target="not_a_target",
                source_interface=source_interface,
                destination_target="not_a_target_either",
                destination_interface=destination_interface,
            )

    def test_node_link_creation_wrong_interface_type_raises(self):
        source_target = Target("Source", "1.1.1.1")
        destination_target = Target("Destination", "2.2.2.2")

        topology = DataSharingNetworkTopology()
        with self.assertRaises((TypeError, AttributeError, KeyError)):
            topology.add_node_link(
                source_target=source_target,
                source_interface="not_a_dict",
                destination_target=destination_target,
                destination_interface="not_a_dict_either",
            )

    def test_node_link_creation_none_arguments_raises(self):
        topology = DataSharingNetworkTopology()
        with self.assertRaises((TypeError, AttributeError)):
            topology.add_node_link(
                source_target=None,
                source_interface=None,
                destination_target=None,
                destination_interface=None,
            )


    
class testImportExportToDict(unittest.TestCase):
    """Tests for serialization and deserialization of Target and DataSharingNetworkTopology."""

    def test_target_to_dict(self):
        target = Target("Target_1", "1.1.1.1")
        target.add_input_interface("127.0.0.1", 8080, d.Protocols.UDP)
        target.add_output_interface("127.0.0.2", 9090, d.Protocols.RDMA)
        
        target_dict = target.to_dict()
        
        self.assertEqual(target_dict["name"], "Target_1")
        self.assertEqual(target_dict["main_ip"], "1.1.1.1")
        self.assertEqual(len(target_dict["input_interfaces"]), 1)
        self.assertEqual(len(target_dict["output_interfaces"]), 1)
        self.assertEqual(target_dict["input_interfaces"][0]["ip"], "127.0.0.1")
        self.assertEqual(target_dict["input_interfaces"][0]["port"], 8080)
        self.assertEqual(target_dict["output_interfaces"][0]["ip"], "127.0.0.2")
        self.assertEqual(target_dict["output_interfaces"][0]["port"], 9090)

    def test_target_from_dict(self):
        target_dict = {
            "name": "Target_1",
            "main_ip": "1.1.1.1",
            "input_interfaces": [{"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP}],
            "output_interfaces": [{"ip": "127.0.0.2", "port": 9090, "protocol": d.Protocols.RDMA}]
        }
        
        target = Target.from_dict(target_dict)
        
        self.assertEqual(target.name, "Target_1")
        self.assertEqual(target.main_ip, "1.1.1.1")
        self.assertEqual(len(target.input_interfaces), 1)
        self.assertEqual(len(target.output_interfaces), 1)
        self.assertEqual(target.input_interfaces[0]["ip"], "127.0.0.1")
        self.assertEqual(target.output_interfaces[0]["ip"], "127.0.0.2")

    def test_target_to_dict_from_dict_roundtrip(self):
        original_target = Target("Target_1", "1.1.1.1")
        original_target.add_input_interface("127.0.0.1", 8080, d.Protocols.UDP)
        original_target.add_output_interface("127.0.0.2", 9090, d.Protocols.RDMA)
        
        target_dict = original_target.to_dict()
        reconstructed_target = Target.from_dict(target_dict)
        
        self.assertEqual(reconstructed_target.name, original_target.name)
        self.assertEqual(reconstructed_target.main_ip, original_target.main_ip)
        self.assertEqual(reconstructed_target.input_interfaces, original_target.input_interfaces)
        self.assertEqual(reconstructed_target.output_interfaces, original_target.output_interfaces)

    def test_topology_to_dict(self):
        source_target = Target("Source", "1.1.1.1")
        destination_target = Target("Destination", "2.2.2.2")
        source_target.add_output_interface("127.0.0.1", 8080, d.Protocols.UDP)
        destination_target.add_input_interface("127.0.0.2", 8080, d.Protocols.UDP)
        
        source_interface = {"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP}
        destination_interface = {"ip": "127.0.0.2", "port": 8080, "protocol": d.Protocols.UDP}
        
        topology = DataSharingNetworkTopology()
        topology.add_node_link(
            source_target=source_target,
            source_interface=source_interface,
            destination_target=destination_target,
            destination_interface=destination_interface
        )
        
        topology_dict = topology.to_dict()
        
        self.assertIn("node_links", topology_dict)
        self.assertEqual(len(topology_dict["node_links"]), 1)
        link = topology_dict["node_links"][0]
        self.assertEqual(link["source_target"]["name"], "Source")
        self.assertEqual(link["destination_target"]["name"], "Destination")

    def test_topology_from_dict(self):
        topology_dict = {
            "node_links": [
                {
                    "source_target": {
                        "name": "Source",
                        "main_ip": "1.1.1.1",
                        "input_interfaces": [],
                        "output_interfaces": [{"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP}]
                    },
                    "source_interface": {"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP},
                    "destination_target": {
                        "name": "Destination",
                        "main_ip": "2.2.2.2",
                        "input_interfaces": [{"ip": "127.0.0.2", "port": 8080, "protocol": d.Protocols.UDP}],
                        "output_interfaces": []
                    },
                    "destination_interface": {"ip": "127.0.0.2", "port": 8080, "protocol": d.Protocols.UDP}
                }
            ]
        }
        
        topology = DataSharingNetworkTopology.from_dict(topology_dict)
        
        self.assertEqual(len(topology.node_links), 1)
        link = topology.node_links[0]
        self.assertEqual(link["source_target"].name, "Source")
        self.assertEqual(link["destination_target"].name, "Destination")

    def test_topology_to_dict_from_dict_roundtrip(self):
        source_target = Target("Source", "1.1.1.1")
        destination_target = Target("Destination", "2.2.2.2")
        source_target.add_output_interface("127.0.0.1", 8080, d.Protocols.UDP)
        destination_target.add_input_interface("127.0.0.2", 8080, d.Protocols.UDP)
        
        source_interface = {"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP}
        destination_interface = {"ip": "127.0.0.2", "port": 8080, "protocol": d.Protocols.UDP}
        
        original_topology = DataSharingNetworkTopology()
        original_topology.add_node_link(
            source_target=source_target,
            source_interface=source_interface,
            destination_target=destination_target,
            destination_interface=destination_interface
        )
        
        topology_dict = original_topology.to_dict()
        reconstructed_topology = DataSharingNetworkTopology.from_dict(topology_dict)
        
        self.assertEqual(len(reconstructed_topology.node_links), len(original_topology.node_links))
        for i, link in enumerate(reconstructed_topology.node_links):
            original_link = original_topology.node_links[i]
            self.assertEqual(link["source_target"].name, original_link["source_target"].name)
            self.assertEqual(link["destination_target"].name, original_link["destination_target"].name)
            self.assertEqual(link["source_interface"], original_link["source_interface"])
            self.assertEqual(link["destination_interface"], original_link["destination_interface"])

class testReverseNodeLinks(unittest.TestCase):
    def test_reverse_node_links_single_link(self):
        source_target = Target("Source", "1.1.1.1")
        destination_target = Target("Destination", "2.2.2.2")
        source_target.add_output_interface("127.0.0.1", 8080, d.Protocols.UDP)
        destination_target.add_input_interface("127.0.0.2", 8080, d.Protocols.UDP)
        
        source_interface = {"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP}
        destination_interface = {"ip": "127.0.0.2", "port": 8080, "protocol": d.Protocols.UDP}
        
        topology = DataSharingNetworkTopology()
        topology.add_node_link(
            source_target=source_target,
            source_interface=source_interface,
            destination_target=destination_target,
            destination_interface=destination_interface
        )
        
        reversed_topology = DataSharingNetworkTopology.reverse_node_links(topology)
        
        self.assertEqual(len(reversed_topology.node_links), 1)
        reversed_link = reversed_topology.node_links[0]
        self.assertEqual(reversed_link["source_target"].name, "Destination")
        self.assertEqual(reversed_link["destination_target"].name, "Source")
        self.assertEqual(reversed_link["source_interface"], destination_interface)
        self.assertEqual(reversed_link["destination_interface"], source_interface)

    def test_reverse_node_links_multiple_links(self):
        target_a = Target("TargetA", "1.1.1.1")
        target_b = Target("TargetB", "2.2.2.2")
        target_c = Target("TargetC", "3.3.3.3")
        
        target_a.add_output_interface("127.0.0.1", 8080, d.Protocols.UDP)
        target_b.add_input_interface("127.0.0.2", 8080, d.Protocols.UDP)
        target_b.add_output_interface("127.0.0.3", 9090, d.Protocols.RDMA)
        target_c.add_input_interface("127.0.0.4", 9090, d.Protocols.RDMA)
        
        topology = DataSharingNetworkTopology()
        topology.add_node_link(
            source_target=target_a,
            source_interface={"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP},
            destination_target=target_b,
            destination_interface={"ip": "127.0.0.2", "port": 8080, "protocol": d.Protocols.UDP}
        )
        topology.add_node_link(
            source_target=target_b,
            source_interface={"ip": "127.0.0.3", "port": 9090, "protocol": d.Protocols.RDMA},
            destination_target=target_c,
            destination_interface={"ip": "127.0.0.4", "port": 9090, "protocol": d.Protocols.RDMA}
        )
        
        reversed_topology = DataSharingNetworkTopology.reverse_node_links(topology)
        
        self.assertEqual(len(reversed_topology.node_links), 2)
        
        # First link should be reversed
        self.assertEqual(reversed_topology.node_links[0]["source_target"].name, "TargetB")
        self.assertEqual(reversed_topology.node_links[0]["destination_target"].name, "TargetA")
        
        # Second link should be reversed
        self.assertEqual(reversed_topology.node_links[1]["source_target"].name, "TargetC")
        self.assertEqual(reversed_topology.node_links[1]["destination_target"].name, "TargetB")

    def test_reverse_node_links_empty_topology(self):
        topology = DataSharingNetworkTopology()
        reversed_topology = DataSharingNetworkTopology.reverse_node_links(topology)
        
        self.assertEqual(len(reversed_topology.node_links), 0)

    def test_reverse_node_links_preserves_interface_details(self):
        source_target = Target("Source", "1.1.1.1")
        destination_target = Target("Destination", "2.2.2.2")
        source_target.add_output_interface("192.168.1.10", 5000, d.Protocols.RDMA)
        destination_target.add_input_interface("192.168.2.20", 6000, d.Protocols.RDMA)
        
        source_interface = {"ip": "192.168.1.10", "port": 5000, "protocol": d.Protocols.RDMA}
        destination_interface = {"ip": "192.168.2.20", "port": 6000, "protocol": d.Protocols.RDMA}
        
        topology = DataSharingNetworkTopology()
        topology.add_node_link(
            source_target=source_target,
            source_interface=source_interface,
            destination_target=destination_target,
            destination_interface=destination_interface
        )
        
        reversed_topology = DataSharingNetworkTopology.reverse_node_links(topology)
        reversed_link = reversed_topology.node_links[0]
        
        self.assertEqual(reversed_link["source_interface"]["ip"], "192.168.2.20")
        self.assertEqual(reversed_link["source_interface"]["port"], 6000)
        self.assertEqual(reversed_link["source_interface"]["protocol"], d.Protocols.RDMA)
        self.assertEqual(reversed_link["destination_interface"]["ip"], "192.168.1.10")
        self.assertEqual(reversed_link["destination_interface"]["port"], 5000)
