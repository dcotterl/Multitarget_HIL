from __future__ import annotations
from pathlib import Path
import sys


PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import definitions as d

class Target:
    def __init__(self,
                 name: str,
                 main_ip: str,
                 input_interfaces: list[dict] | None = None,
                 output_interfaces: list[dict] | None = None,
                 ):

        self.name = name
        self.main_ip = main_ip
        self.input_interfaces = input_interfaces if input_interfaces is not None else []
        self.output_interfaces = output_interfaces if output_interfaces is not None else []

    def add_input_interface(self, ip : str, port : int, protocol : d.Protocols) -> None:
        self.input_interfaces.append({"ip": ip, "port": port, "protocol": protocol})

    def add_output_interface(self, ip : str, port : int, protocol : d.Protocols) -> None:
        self.output_interfaces.append({"ip": ip, "port": port, "protocol": protocol})

    def remove_input_interface(self, ip : str, port : int, protocol : d.Protocols) -> None:
        self.input_interfaces = [
            i for i in self.input_interfaces
            if not (i["ip"] == ip and i["port"] == port and i["protocol"] == protocol)
        ]

    def remove_output_interface(self, ip : str, port : int, protocol : d.Protocols) -> None:
        self.output_interfaces = [
            o for o in self.output_interfaces
            if not (o["ip"] == ip and o["port"] == port and o["protocol"] == protocol)
        ]

    def find_input_interface(self, interface : dict) -> dict | None:
        for i in self.input_interfaces:
            if i["ip"] == interface["ip"] and i["port"] == interface["port"] and i["protocol"] == interface["protocol"]:
                return i
        return None

    def find_output_interface(self, interface : dict) -> dict | None:
        for o in self.output_interfaces:
            if o["ip"] == interface["ip"] and o["port"] == interface["port"] and o["protocol"] == interface["protocol"]:
                return o
        return None

    def __str__(self):
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
        return {
                "name": self.name,
                "main_ip": self.main_ip,
                "input_interfaces": [i for i in self.input_interfaces],
                "output_interfaces": [o for o in self.output_interfaces]
               }

    @classmethod
    def from_dict(cls, data: dict) -> Target:
        return cls(
            name=data["name"],
            main_ip=data["main_ip"],
            input_interfaces=data.get("input_interfaces", []),
            output_interfaces=data.get("output_interfaces", [])
        )



class DataSharingNetworkTopology:
    def __init__(self):
        self.node_links = []

    def add_node_link(self, 
                      source_target : Target,
                      source_interface : dict,
                      destination_target: Target,
                      destination_interface: dict) -> None:

        print(source_interface)
        print(destination_interface)

        if source_target.find_output_interface(source_interface) and \
           destination_target.find_input_interface(destination_interface):
            self.node_links.append({
                "source_target": source_target,
                "source_interface": source_interface,
                "destination_target": destination_target,
                "destination_interface": destination_interface
            })
        else:
            if source_interface["protocol"] != destination_interface["protocol"]:
                raise ValueError("Source and destination interface protocols do not match")
            raise ValueError("Invalid source or destination interface") 

    def remove_node_link(self, 
                         source_target : Target,
                         source_interface : dict,
                         destination_target: Target,
                         destination_interface: dict) -> None:
        self.node_links = [
            link for link in self.node_links
            if not (link["source_target"] == source_target and link["source_interface"] == source_interface and link["destination_target"] == destination_target and link["destination_interface"] == destination_interface)
        ]

    def __str__(self) -> str:
        s = "Data Sharing Network Topology:"
        for link in self.node_links:
            s += f"\n{link['source_target'].name} - {link['source_interface']['ip']}:{link['source_interface']['port']}:{link['source_interface']['protocol'].value} -> {link['destination_target'].name} - {link['destination_interface']['ip']}:{link['destination_interface']['port']}:{link['destination_interface']['protocol'].value}"
        return s

    def to_dict(self) -> dict:
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

    dict_representation = topology.to_dict()
    print(dict_representation)
    topology_from_dict = DataSharingNetworkTopology.from_dict(dict_representation)
    print(topology_from_dict)