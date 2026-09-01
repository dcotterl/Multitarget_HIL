import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import definitions as d
from target_configuration_utilities import dsf_network_definitions as dsf
from data_sharing_framework_config_api import configuration_builder as cb

def setup_network(add_udp_links: bool = False, channels: int = 4) -> dsf.DataSharingNetworkTopology:

    topology = dsf.DataSharingNetworkTopology()

    target_1 = dsf.Target("Target_1", "1.1.1.1")
    target_2 = dsf.Target("Target_2", "2.2.2.2")
    target_3 = dsf.Target("Target_3", "3.3.3.3")

    target_1.add_output_interface("169.254.49.44", 5010, d.Protocols.RDMA)
    target_1.add_input_interface("169.254.49.44", 5011, d.Protocols.RDMA)
    target_1.add_output_interface("169.254.49.44", 5012, d.Protocols.RDMA)
    target_1.add_output_interface("10.94.1.22", 5022, d.Protocols.UDP)
    target_1.add_input_interface("10.94.1.22", 5023, d.Protocols.UDP)

    target_2.add_input_interface("169.254.23.111", 5010, d.Protocols.RDMA)
    target_2.add_output_interface("169.254.23.111", 5011, d.Protocols.RDMA)
    target_2.add_input_interface("10.94.1.24", 5022, d.Protocols.UDP)
    target_2.add_output_interface("10.94.1.24", 5023, d.Protocols.UDP)

    target_3.add_input_interface("169.254.33.33", 5012, d.Protocols.RDMA)


    # create link for RDMA  Target_1 -> Target_2 over port 5010
    topology.add_node_link(source_target = target_1, 
                           source_interface=target_1.output_interfaces[0],
                           destination_target=target_2, 
                           destination_interface=target_2.input_interfaces[0],
                           number_of_channels=channels)
    
    # create link for RDMA  Target_2 -> Target_1 over port 5011
    topology.add_node_link(source_target=target_2, 
                           source_interface=target_2.output_interfaces[0],
                           destination_target=target_1, 
                           destination_interface=target_1.input_interfaces[0],
                           number_of_channels=channels)

    # create link for RDMA  Target_1 -> Target_3 over port 5012
    topology.add_node_link(source_target=target_1, 
                           source_interface=target_1.output_interfaces[1],
                           destination_target=target_3, 
                           destination_interface=target_3.input_interfaces[0],
                           number_of_channels=channels)
    
    if add_udp_links:
        topology.add_node_link(source_target=target_1, 
                               source_interface=target_1.output_interfaces[2],
                               destination_target=target_2, 
                               destination_interface=target_2.input_interfaces[2],
                               number_of_channels=channels)
        
        topology.add_node_link(source_target=target_2, source_interface=target_2.output_interfaces[2],
                               destination_target=target_1, destination_interface=target_1.input_interfaces[2],
                               number_of_channels=channels)

    return topology

if __name__ == "__main__":
    print(f"here is the module {__name__} for building configurations from topology")

    topology = setup_network()

    print(topology)

    cfg_map = cb.ConfigurationMap()

    cfg_map.initialize_configurations(topology)

    cfg_map.export_configurations("examples/output")
