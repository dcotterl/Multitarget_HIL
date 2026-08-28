import json
import logging
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import rdma_definitions as rdma
from data_sharing_framework_config_api import udp_definitions as udp
from data_sharing_framework_config_api import definitions as d
from target_configuration_utilities import dsf_network_definitions as dsf

def setup_network() -> dsf.DataSharingNetworkTopology:
    topology = dsf.DataSharingNetworkTopology()

    target_1 = dsf.Target("Target_1", "1.1.1.1")
    target_2 = dsf.Target("Target_2", "2.2.2.2")

    target_1.add_output_interface("169.254.49.44", 5010, d.Protocols.RDMA)
    target_1.add_input_interface("169.254.49.44", 5011, d.Protocols.RDMA)
    target_1.add_output_interface("10.94.1.22", 5012, d.Protocols.UDP)
    target_1.add_input_interface("10.94.1.22", 5013, d.Protocols.UDP)

    target_2.add_input_interface("169.254.23.111", 5010, d.Protocols.RDMA)
    target_2.add_output_interface("169.254.23.111", 5011, d.Protocols.RDMA)
    target_2.add_input_interface("10.94.1.24", 5012, d.Protocols.UDP)
    target_2.add_output_interface("10.94.1.24", 5013, d.Protocols.UDP)

    # create link for RDMA  Target_1 -> Target_2 over port 5010
    topology.add_node_link(source_target = target_1, source_interface=target_1.output_interfaces[0],
                           destination_target=target_2, destination_interface=target_2.input_interfaces[0])
    # create link for RDMA  Target_2 -> Target_1 over port 5011
    topology.add_node_link(source_target=target_2, source_interface=target_2.output_interfaces[0],
                           destination_target=target_1, destination_interface=target_1.input_interfaces[0])
    return topology



class ConfigurationMap():
    def __init__(self):
        self.map = []

    def add_configuration(self, target: str, configuration: d.Configuration):
        self.map.append({"target": target, "configuration": configuration})

    def get_target_configurations(self, target_name) -> d.Configuration:
        for entry in self.map:
            if entry["target"] == target_name:
                return entry["configuration"]
        return None


    def initialize_configuration(self,topology: dsf.DataSharingNetworkTopology) -> None:
        for source in topology.get_all_sources():
            self.add_configuration(source, d.Configuration(source))

    def initialize_plugins(self, topology: dsf.DataSharingNetworkTopology, ) -> None:
        for link in topology.node_links:
            cfg = cfg_map.get_target_configurations(link["source_target"].name)
            found = False
            for plugin in cfg.plugins:
                if plugin.name == link["source_interface"]["protocol"]:
                    found = True
                    break

        pass

if __name__ == "__main__":

    topology = setup_network()
    cfg_map = ConfigurationMap()
    cfg_map.initialize_configuration(topology)
    cfg_map.initialize_plugins(topology)

