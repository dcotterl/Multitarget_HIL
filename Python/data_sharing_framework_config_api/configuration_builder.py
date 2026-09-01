from __future__ import annotations

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

logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s [%(levelname)s] [%(module)s:%(filename)s:%(lineno)d] %(message)s")
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

#TODO: complete UPD

class ConfigurationMap():
    def __init__(self):
        self.cfg_map = []

    def add_configuration(self, target: str, configuration: d.Configuration):
        logger.debug(f"Adding configuration for target: {target}")
        self.cfg_map.append({"target": target, "configuration": configuration})

    def get_target_configurations(self, target_name) -> d.Configuration:
        for entry in self.cfg_map:
            if entry["target"] == target_name:
                return entry["configuration"]
        return None

    def initialize_configurations(self,topology: dsf.DataSharingNetworkTopology) -> None:
        logger.info(f"Available sources in the topology: {topology.get_all_sources()}")
        for source in topology.get_all_sources():
            logger.info(f"\tInitializing configuration for source: {source}")
            logger.info(f"\tAvailable protocols for {source}: outgoing {topology.get_source_protocols(source)}, incoming {topology.get_destination_protocols(source)}")

            protocols_source = topology.get_source_protocols(source)
            protocols_destination = topology.get_destination_protocols(source)

            protocols = protocols_source + protocols_destination #list(set(protocols_source + protocols_destination))
            
            for protocol in protocols:
                
                plugin = self.initialize_plugin(topology=topology, target_name=source, protocol=protocol)

            configuration = d.Configuration(plugins=[plugin])
            logger.info(f"\t\tConfiguration for source {source} initialized")
            self.add_configuration(target=source, configuration=configuration)

    def initialize_plugin(self, topology: dsf.DataSharingNetworkTopology, target_name: str , protocol: d.Protocols) -> None:
        logger.info(f"\t\tInitializing plugin for protocol: {protocol}")
        if protocol == d.Protocols.RDMA:
            thread = self.initialize_thread(target=target_name, protocol=protocol, topology=topology)
            plugin = rdma.Plugin(name = f"Plugin_{target_name}_{protocol.name}", threads = [thread])
        elif protocol == d.Protocols.UDP:
            logger.warning(f"UDP protocol initialization not yet implemented for target: {target_name}")
            pass #TODO: implement for UDP

        return plugin

    def initialize_thread(self, target :str, protocol : d.Protocols, topology: dsf.DataSharingNetworkTopology) -> None:
        logger.info(f"\t\t\tInitializing thread")
        transfer_groups = []
        if protocol == d.Protocols.RDMA:
            logger.info(f"\t\t\tGathering TX links for target: {target}")
            links_tx = topology.get_links_with_target_source(target) #get all links where the target is the source

            logger.info(f"\t\t\tGathering RX Links for target: {target}")
            links_rx = topology.get_links_with_target_destination(target) #get all links where the target is the destination

            logger.info(f"\t\t\tFiltering RDMA links")
            links_tx = [link for link in links_tx if link["source_interface"]["protocol"] == d.Protocols.RDMA] #filter only RDMA links for TX
            links_rx = [link for link in links_rx if link["destination_interface"]["protocol"] == d.Protocols.RDMA] #filter only RDMA links for RX

            if links_tx:  # Only initialize transfer group if there are TX links
                transfer_groups.append(self.initialize_transfer_group(direction=d.Direction.TX, list_of_links=links_tx))
            else:
                logger.info(f"\t\t\tNo TX links found for target: {target}")

            if links_rx:  # Only initialize transfer group if there are RX links
                transfer_groups.append(self.initialize_transfer_group(direction=d.Direction.RX, list_of_links=links_rx))
            else:
                logger.info(f"\t\t\tNo RX links found for target: {target}")

            thread = rdma.Thread(transfer_groups=transfer_groups)
        elif protocol == d.Protocols.UDP:
            logger.warning(f"UDP protocol initialization not yet implemented for target: {target}")
            pass #TODO: implement for UDP

        return thread

    def initialize_transfer_group(self, direction : d.Direction, list_of_links: list[dict]) -> None:
        logger.info(f"\t\t\t\tInitializing transfer group for direction: {direction.name}")
        transfers = [] #create one transfer for each target
        for link in list_of_links:
            logger.info(f"\t\t\t\tProcessing link from {link['source_target'].name} to {link['destination_target'].name}")
            if link['source_interface']["protocol"] == d.Protocols.RDMA:
                transfers.append(self.initialize_transfer(link, direction=direction))
            elif link['source_interface']["protocol"] == d.Protocols.UDP:
                logger.warning(f"UDP transfer initialization not yet implemented")
                pass #TODO: initilize trnsfers for UDP consider they need to know thedistinaation

        if link['source_interface']["protocol"] == d.Protocols.RDMA:
            if direction == d.Direction.TX:
                transfergroup = rdma.TransferGroup(name=f"TransferGroup_{link['source_target'].name}_to_{link['destination_target'].name}_TX",
                                                   direction=direction,
                                                   transfers=transfers)
            elif direction == d.Direction.RX:
                transfergroup = rdma.TransferGroup(name=f"TransferGroup_{link['source_target'].name}_to_{link['destination_target'].name}_RX",
                                                   direction=direction,
                                                   transfers=transfers)
        elif link['source_interface']["protocol"] == d.Protocols.UDP:
            logger.warning(f"UDP transfer group initialization not yet implemented")
            pass #TODO: initialize transfer group for UDP
            transfergroup = None

        return transfergroup

    def initialize_transfer(self, link: dict, direction: d.Direction) -> None:
        logger.info(f"\t\t\t\t\tInitializing {direction.name} transfer for link from {link['source_target'].name} to {link['destination_target'].name}")

        protocol = link['source_interface']["protocol"]
        channels = self.initialize_channels(number_of_channels=link['number_of_channels'], protocol=protocol)

        if protocol == d.Protocols.RDMA:
            if direction == d.Direction.TX:
                transfer = rdma.Transfer(name = f"Transfer_{link['source_target'].name}_to_{link['destination_target'].name}_TX",
                                        channels=channels,
                                        local_address=link['source_interface']['ip'],
                                        local_port=link['source_interface']['port'],
                                        destination_address=link['destination_interface']['ip'],
                                        destination_port=link['destination_interface']['port']
                                        )
            elif direction == d.Direction.RX:
                transfer = rdma.Transfer(name = f"Transfer_{link['destination_target'].name}_to_{link['source_target'].name}_RX",
                                        channels=channels,
                                        local_address=link['destination_interface']['ip'],
                                        local_port=link['destination_interface']['port'],
                                        )
        elif protocol == d.Protocols.UDP:
            if direction == d.Direction.TX:
                transfer = udp.Transfer(name = f"Transfer_{link['source_target'].name}_to_{link['destination_target'].name}_UDP",
                                        channels=channels,
                                        destination_address=link['destination_interface']['ip'],
                                        destination_port=link['destination_interface']['port']
                                        )
            elif direction == d.Direction.RX:
                transfer = udp.Transfer(name = f"Transfer_{link['destination_target'].name}_to_{link['source_target'].name}_UDP",
                                        channels=channels,
                                        local_address=link['destination_interface']['ip'],
                                        local_port=link['destination_interface']['port'],
                                        )

        return transfer

    def initialize_channels(self, number_of_channels : int, protocol: d.Protocols) -> list[d.Channel]:
        logger.info(f"\t\t\t\t\t\tInitializing {number_of_channels} channels for protocol {protocol.name}")
        channels = []
        for i in range(number_of_channels):
            if protocol == d.Protocols.RDMA:
                channel = rdma.Channel(name = f"RDMA_Channel_{i}")
            elif protocol == d.Protocols.UDP:
                channel = udp.Channel(name = f"UDP_Channel_{i}")
            channels.append(channel)
        return channels

    def export_configurations(self, base_path: str | Path) -> None:
        for element in self.cfg_map:
            logger.error(f"Exporting configuration for target {element['target']}")
            # Write configuration to file
            config_dict = element['configuration'].to_dict()
            filename = Path(base_path) / f"config_{element['target']}.dsf"
            try:
                with open(filename, 'w') as f:
                    json.dump(config_dict, f, indent=4, default=str)
                logger.info(f"Configuration for target {element['target']} written to {filename}")
            except Exception as e:
                logger.error(f"Failed to write configuration for target {element['target']}: {e}")

if __name__ == "__main__":
    print(f"here is the module {__name__} for building configurations from topology")