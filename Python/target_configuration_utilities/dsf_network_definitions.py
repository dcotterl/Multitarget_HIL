"""Data Sharing Framework Network Topology Definitions.

This module defines the network topology structures for managing communication
targets and their interconnections in the Data Sharing Framework.

    Target
        └── Input/Output Interfaces (NetworkInterface)

    DataSharingNetworkTopology
        └── Node Links [1..n]
            ├── Source Target
            ├── Source Interface
            ├── Destination Target
            └── Destination Interface

Each object level supports dictionary serialization (to_dict()) and
deserialization (from_dict()) for configuration persistence.
"""

from __future__ import annotations
from pathlib import Path
import sys
import logging

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import definitions as d

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

class Target:
    """Represents a communication target with input and output network interfaces.
    
    A Target encapsulates a named entity within the network topology that can
    send and receive data across multiple network interfaces.
    
    Attributes:
        name (str): Identifier for this target.
        main_ip (str): Primary IP address of the target.
        input_interfaces (list[dict]): List of input network interfaces.
        output_interfaces (list[dict]): List of output network interfaces.
    """
    
    def __init__(self,
                 name: str,
                 main_ip: str,
                 input_interfaces: list[dict] | None = None,
                 output_interfaces: list[dict] | None = None,
                 ):
        """Initialize a Target.
        
        Args:
            name: Identifier for the target.
            main_ip: Primary IP address.
            input_interfaces: Optional list of input interface dictionaries.
            output_interfaces: Optional list of output interface dictionaries.
        """
        logger.debug(f"Creating Target '{name}' with main_ip '{main_ip}'")
        self.name = name
        self.main_ip = main_ip
        self.input_interfaces = input_interfaces if input_interfaces is not None else []
        self.output_interfaces = output_interfaces if output_interfaces is not None else []

    def add_input_interface(self, ip : str, port : int, protocol : d.Protocols) -> None:
        """Add an input network interface to this target.
        
        Args:
            ip: IP address of the interface.
            port: Port number of the interface.
            protocol: Communication protocol (UDP, RDMA, etc.).
            
        Raises:
            TypeError: If protocol is not a d.Protocols enum value.
        """
        logger.debug(f"Adding input interface {ip}:{port}:{protocol.value} to target '{self.name}'")
        self.input_interfaces.append({"ip": ip, "port": port, "protocol": protocol})

    def add_output_interface(self, ip : str, port : int, protocol : d.Protocols) -> None:
        """Add an output network interface to this target.
        
        Args:
            ip: IP address of the interface.
            port: Port number of the interface.
            protocol: Communication protocol (UDP, RDMA, etc.).
            
        Raises:
            TypeError: If protocol is not a d.Protocols enum value.
        """
        logger.debug(f"Adding output interface {ip}:{port}:{protocol.value} to target '{self.name}'")
        self.output_interfaces.append({"ip": ip, "port": port, "protocol": protocol})

    def remove_input_interface(self, ip : str, port : int, protocol : d.Protocols) -> None:
        """Remove an input network interface from this target.
        
        Args:
            ip: IP address of the interface to remove.
            port: Port number of the interface to remove.
            protocol: Communication protocol of the interface to remove.
        """
        logger.debug(f"Removing input interface {ip}:{port}:{protocol.value} from target '{self.name}'")
        self.input_interfaces = [
            i for i in self.input_interfaces
            if not (i["ip"] == ip and i["port"] == port and i["protocol"] == protocol)
        ]

    def remove_output_interface(self, ip : str, port : int, protocol : d.Protocols) -> None:
        """Remove an output network interface from this target.
        
        Args:
            ip: IP address of the interface to remove.
            port: Port number of the interface to remove.
            protocol: Communication protocol of the interface to remove.
        """
        logger.debug(f"Removing output interface {ip}:{port}:{protocol.value} from target '{self.name}'")
        self.output_interfaces = [
            o for o in self.output_interfaces
            if not (o["ip"] == ip and o["port"] == port and o["protocol"] == protocol)
        ]

    def find_input_interface(self, interface : dict) -> dict | None:
        """Find an input interface matching the given interface specification.
        
        Args:
            interface: Dictionary with 'ip', 'port', and 'protocol' keys.
            
        Returns:
            dict: The matching interface dictionary if found, None otherwise.
        """
        for i in self.input_interfaces:
            if i["ip"] == interface["ip"] and i["port"] == interface["port"] and i["protocol"] == interface["protocol"]:
                return i
        return None

    def find_output_interface(self, interface : dict) -> dict | None:
        """Find an output interface matching the given interface specification.
        
        Args:
            interface: Dictionary with 'ip', 'port', and 'protocol' keys.
            
        Returns:
            dict: The matching interface dictionary if found, None otherwise.
        """
        for o in self.output_interfaces:
            if o["ip"] == interface["ip"] and o["port"] == interface["port"] and o["protocol"] == interface["protocol"]:
                return o
        return None

    def __str__(self) -> str:
        """Return a human-readable string representation of this target.
        
        Returns:
            str: Formatted string with target name, IP, and interface details.
        """
        s = f"Target name: {self.name} \nMain_ip: {self.main_ip}"
        if self.input_interfaces:
            s += "\nInput Interfaces:"
        for i in self.input_interfaces:
            s += f"\n - {i}"
        if self.output_interfaces:
            s += "\nOutput Interfaces:"
            for o in self.output_interfaces:
                s += f"\n - {o}"
        return s

    def to_dict(self) -> dict:
        """Convert this target to a dictionary representation.
        
        Returns:
            dict: Dictionary with 'name', 'main_ip', 'input_interfaces', and 'output_interfaces' keys.
        """
        logger.debug(f"Serializing target '{self.name}' to dictionary")
        return {
                "name": self.name,
                "main_ip": self.main_ip,
                "input_interfaces": [i for i in self.input_interfaces],
                "output_interfaces": [o for o in self.output_interfaces]
               }

    @classmethod
    def from_dict(cls, data: dict) -> Target:
        """Create a Target instance from a dictionary representation.
        
        Args:
            data: Dictionary with 'name', 'main_ip', and optional 'input_interfaces' and 'output_interfaces'.
            
        Returns:
            Target: A new Target instance initialized from the dictionary.
            
        Raises:
            KeyError: If required keys 'name' or 'main_ip' are missing from data.
        """
        logger.debug(f"Deserializing target from dictionary with name '{data.get('name')}'")
        return cls(
            name=data["name"],
            main_ip=data["main_ip"],
            input_interfaces=data.get("input_interfaces", []),
            output_interfaces=data.get("output_interfaces", [])
        )

class DataSharingNetworkTopology:
    """Manages the network topology of interconnected targets.
    
    A DataSharingNetworkTopology represents the connections and data flows
    between multiple Target entities. Each node link defines a communication
    path from a source target's output interface to a destination target's input interface.
    
    Attributes:
        node_links (list[dict]): List of node link dictionaries defining connections.
    """
    
    def __init__(self):
        """Initialize an empty DataSharingNetworkTopology."""
        logger.debug("Creating new DataSharingNetworkTopology")
        self.node_links = []

    def add_node_link(self, 
                      source_target : Target,
                      source_interface : dict,
                      destination_target: Target,
                      destination_interface: dict,
                      number_of_channels: int = 1) -> None:
        """Add a connection link between two targets.
        
        Args:
            source_target: The source Target entity.
            source_interface: Dictionary with interface details for the source.
            destination_target: The destination Target entity.
            destination_interface: Dictionary with interface details for the destination.
            
        Raises:
            ValueError: If the source target lacks the specified output interface,
                       the destination target lacks the specified input interface,
                       or the protocols don't match between interfaces.
        """
        logger.info(f"Adding node link: {source_target.name} -> {destination_target.name}")
        
        if source_target.find_output_interface(source_interface) and \
           destination_target.find_input_interface(destination_interface):
            self.node_links.append({
                "source_target": source_target,
                "source_interface": source_interface,
                "destination_target": destination_target,
                "destination_interface": destination_interface,
                "number_of_channels": number_of_channels
            })
            logger.debug(f"Successfully added node link to topology (total links: {len(self.node_links)})")
        else:
            if source_interface["protocol"] != destination_interface["protocol"]:
                logger.error(f"Protocol mismatch: {source_interface['protocol']} != {destination_interface['protocol']}")
                raise ValueError("Source and destination interface protocols do not match")
            logger.error(f"Invalid interfaces: source interface not found in {source_target.name} or destination interface not found in {destination_target.name}")
            raise ValueError("Invalid source or destination interface") 

    def remove_node_link(self, 
                         source_target : Target,
                         source_interface : dict,
                         destination_target: Target,
                         destination_interface: dict) -> None:
        """Remove a connection link between two targets.
        
        Args:
            source_target: The source Target entity.
            source_interface: Dictionary with interface details for the source.
            destination_target: The destination Target entity.
            destination_interface: Dictionary with interface details for the destination.
        """
        logger.info(f"Removing node link: {source_target.name} -> {destination_target.name}")
        self.node_links = [
            link for link in self.node_links
            if not (link["source_target"] == source_target and link["source_interface"] == source_interface and link["destination_target"] == destination_target and link["destination_interface"] == destination_interface)
        ]
        logger.debug(f"Node link removed (remaining links: {len(self.node_links)})")

    def __str__(self) -> str:
        """Return a human-readable string representation of the topology.
        
        Returns:
            str: Formatted string showing all node links and their details.
        """
        s = "Data Sharing Network Topology:"
        for link in self.node_links:
            s += f"\n{link['source_target'].name} - {link['source_interface']['ip']}:{link['source_interface']['port']}:{link['source_interface']['protocol'].value} -> {link['destination_target'].name} - {link['destination_interface']['ip']}:{link['destination_interface']['port']}:{link['destination_interface']['protocol'].value} - #ch:{link['number_of_channels']}"
        return s

    def to_dict(self) -> dict:
        """Convert this topology to a dictionary representation.
        
        Returns:
            dict: Dictionary with 'node_links' key containing serialized links.
        """
        logger.debug(f"Serializing topology with {len(self.node_links)} node links to dictionary")
        return {
            "node_links": [
                {
                    "source_target": link["source_target"].to_dict(),
                    "source_interface": link["source_interface"],
                    "destination_target": link["destination_target"].to_dict(),
                    "destination_interface": link["destination_interface"]
                }
                for link in self.node_links
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> DataSharingNetworkTopology:
        """Create a DataSharingNetworkTopology instance from a dictionary representation.
        
        Args:
            data: Dictionary with 'node_links' key containing list of link dictionaries.
            
        Returns:
            DataSharingNetworkTopology: A new topology instance initialized from the dictionary.
        """
        logger.debug(f"Deserializing topology from dictionary with {len(data.get('node_links', []))} node links")
        topology = cls()
        for link_data in data.get("node_links", []):
            source_target = Target.from_dict(link_data["source_target"])
            destination_target = Target.from_dict(link_data["destination_target"])
            topology.add_node_link(
                source_target=source_target,
                source_interface=link_data["source_interface"],
                destination_target=destination_target,
                destination_interface=link_data["destination_interface"]
            )
        return topology

    @classmethod
    def reverse_node_links(cls, topology: DataSharingNetworkTopology) -> DataSharingNetworkTopology:
        """Create a new topology with all node links reversed.
        
        Reversal swaps source and destination targets and their interfaces,
        effectively reversing the direction of data flow in the topology.
        
        Args:
            topology: The topology to reverse.
            
        Returns:
            DataSharingNetworkTopology: A new topology with reversed links.
        """
        logger.info(f"Reversing topology with {len(topology.node_links)} node links")
        reversed_topology = cls()
        reversed_topology.node_links = [
            {
                "source_target": link["destination_target"],
                "source_interface": link["destination_interface"],
                "destination_target": link["source_target"],
                "destination_interface": link["source_interface"],
                "number_of_channels": link["number_of_channels"],
            }
            for link in topology.node_links
        ]
        logger.debug(f"Topology reversed (new topology has {len(reversed_topology.node_links)} node links)")
        return reversed_topology

    def get_all_sources(self):
        """Get all unique source target names in the topology.

        Returns:
            set: A set of unique source target names.
        """
        unique_source_names = []
        for link in self.node_links:
            source_name = link["source_target"].name
            if source_name not in unique_source_names:
                unique_source_names.append(source_name)
        return unique_source_names

    def get_links_with_target_destination(self, target_name: str) -> list:
        """Get all links where the specified target is the destination.

        Args:
            target_name: The name of the destination target.

        Returns:
            list: A list of links where the target is the destination.
        """
        return [link for link in self.node_links if link["destination_target"].name == target_name]

    def get_links_with_target_source(self, target_name: str) -> list:
        """Get all links where the specified target is the source.

        Args:
            target_name: The name of the source target.

        Returns:
            list: A list of links where the target is the source.
        """
        return [link for link in self.node_links if link["source_target"].name == target_name]

    def get_source_protocols(self, target_name: str) -> list:
        """Get all unique protocols used by the source target in the topology.

        Args:
            target_name: The name of the source target.

        Returns:
            list: A list of unique protocols used by the source target.
        """
        protocols = [link["source_interface"]["protocol"] for link in self.node_links if link["source_target"].name == target_name]
        return list(set(protocols))

if __name__ == "__main__":

    interface = {"ip": "127.0.0.2", "port": 8080, "protocol": d.Protocols.UDP}

    target_1 = Target("Target_1", "1.1.1.1")
    target_1.add_output_interface("127.0.0.1", 8080, d.Protocols.UDP)

    target_2 = Target("Target_2", "2.2.2.2", input_interfaces=[interface])

    target_3 = Target("Target_3", "3.3.3.3")
    target_3.add_input_interface("127.0.0.3", 8080, d.Protocols.UDP)
    target_3.add_input_interface("127.0.0.3", 8081, d.Protocols.RDMA)

    target_3.remove_input_interface("127.0.0.3", 8080, d.Protocols.UDP)

    topology = DataSharingNetworkTopology()
    
    topology.add_node_link(
        source_target=target_1,
        source_interface={"ip": "127.0.0.1", "port": 8080, "protocol": d.Protocols.UDP},
        destination_target=target_2,
        destination_interface={"ip": "127.0.0.2", "port": 8080, "protocol": d.Protocols.UDP})

    reversed_topology = DataSharingNetworkTopology.reverse_node_links(topology)
    print(topology)

    print(reversed_topology)

    print(topology.get_links_with_target_source("Target_1"))
    print(topology.get_links_with_target_destination("Target_2"))
