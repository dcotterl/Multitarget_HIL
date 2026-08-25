import json
import logging
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import rdma_definitions as rdma
from data_sharing_framework_config_api import definitions as d

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

"""
class Parent:
    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return f"(name={self.name})"

class Child(Parent):
    def __init__(self, name: str, value: int) -> None:
        super().__init__(name)
        self.value = value

    def __str__(self) -> str:
        return f"(name={self.name}, value={self.value})"
"""

def rdma_portTest():
    collapse = True

    element = d.Element(key="local port", value="5011")
    #print (element)

    component_settings = d.ComponentSettings(component="xxxxxxxxxx", initial_elements=[element])
    #print (component_settings)

    channel = d.Channel(name="Channel1")
    #print (channel)

    transfer = d.Transfer(name = "Generic Transfer",
                          channels = [channel],
                          local_address = "123.456.789.123",
                          local_port = 5011,
                          destination_address = "987.654.321.987",
                          destination_port = 5011)
    #print (transfer.__str__(collapse=collapse))

    rdma_transfer = rdma.Transfer(name = "RDMA Transfer",
                                  channels = [channel],
                                  local_address = "123.456.789.123",
                                  local_port = 5011,)
    #print (rdma_transfer.__str__(collapse=collapse))

    transfer_group = d.TransferGroup(name = "Generic Transfer Group",
                                     transfers = [transfer])
    #print (transfer_group.__str__(collapse=collapse))

    rdma_transfer_group = rdma.TransferGroup(name = "RDMA Transfer Group",
                                            transfers = [rdma_transfer])
    #print (rdma_transfer_group.__str__(collapse=collapse))

    thread = d.Thread(transfer_groups = [transfer_group])
    #print (thread.__str__(collapse=collapse))

    rdma_thread = rdma.Thread(transfer_groups = [rdma_transfer_group])
    #print (rdma_thread.__str__(collapse=collapse))

    plugin = d.Plugin(name = "Generic Plugin", threads=[thread])
    #print (plugin.__str__(collapse=collapse))

    rdma_plugin = rdma.Plugin(name = "RDMA Plugin", threads=[rdma_thread])
    #print (rdma_plugin.__str__(collapse=collapse))

    configuration = d.Configuration(plugins=[plugin,rdma_plugin])
    print (configuration.__str__(collapse=collapse))


if __name__ == "__main__":
    rdma_portTest()