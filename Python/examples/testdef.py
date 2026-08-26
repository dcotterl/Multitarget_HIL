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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

collapse = False

def rdma_portTest():


    element = d.Element(key="local port", value="5011")
    #print (element)

    component_settings = d.ComponentSettings(component="xxxxxxxxxx", initial_elements=[element])
    #print (component_settings)

    channel = d.Channel(name="Channel1")
    #print (channel)

    rdma_channel = rdma.Channel(name="RDMA Channel1")
    #print (rdma_channel)

    transfer = d.Transfer(name = "Generic Transfer",
                          channels = [channel],
                          local_address = "123.456.789.123",
                          local_port = 5011,
                          destination_address = "987.654.321.987",
                          destination_port = 5011)
    #print (transfer.__str__(collapse=collapse))

    rdma_transfer = rdma.Transfer(name = "RDMA Transfer",
                                  channels = [rdma_channel],
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

def udp_portTest():
    channel = udp.Channel(name="UDP Channel1")
    #print(f"{channel}")
    transfer = udp.Transfer(name = "UDP Transfer",
                            channels = [channel],
                            destination_address = "127.0.0.1",
                            destination_port = 5011)
    #print (transfer)
    trasfer_group = udp.TransferGroup(name = "UDP Transfer Group",
                                      transfers = [transfer])
    #print (trasfer_group)

    thread = udp.Thread(transfer_groups = [trasfer_group],
                        local_address = "127.0.0.1",
                        local_port = 5011)
    print (thread)

    plugin = udp.Plugin(name = "UDP Plugin", threads=[thread])
    print (plugin)

def import_udp():
    def makeChannel():
            return udp.Channel(name="Channel", unit="V")
    def makeTransferTx():
        return udp.Transfer(name = "Transfer",
                            destination_address = "127.0.0.1",
                            destination_port = 50001,
                            channels = [makeChannel()])
    def makeTransferRx():
        return udp.Transfer(name = "Transfer",
                            local_address = "127.0.0.1",
                            local_port = 50000,
                            channels = [makeChannel()])
    def makeTransferGroupTx():
        return udp.TransferGroup(name = "Group",
                                    direction = d.Direction.TX,
                                    transfers = [makeTransferTx()])
    def makeTransferGroupRx():
        return udp.TransferGroup(name = "Group",
                                    direction = d.Direction.RX,
                                    transfers = [makeTransferRx()])
    def makeThreadTx():
        return udp.Thread(local_address = "127.0.0.1",
                            local_port = 50000,
                            transfer_groups = [makeTransferGroupTx()])
    def makeThreadRx():
        return udp.Thread(local_address = "127.0.0.1",
                            local_port = 50001,
                            transfer_groups = [makeTransferGroupRx()])
    def makePlugin():
        return udp.Plugin(name = "Plugin",
                            threads = [makeThreadTx(), makeThreadRx()]) 
    def makeConfiguration():
        return d.Configuration(plugins = [makePlugin()])

    print(makeThreadTx().local_port)

    timp = udp.Thread.from_dict(makeThreadTx().getDict())

    print(timp.getDict())

    print(timp.getDict() == makeThreadTx().getDict())

if __name__ == "__main__":
    #rdma_portTest()
    udp_portTest()
    #import_udp()