import sys
import logging
from pathlib import Path
import json

logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s [%(levelname)s] %(message)s",
	)
logger = logging.getLogger(__name__)

# When run directly, Python searches this examples directory, not its parent.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import RDMA_Definitions as rdma

if __name__ == "__main__":

    config = rdma.RDMA_Configuration()
    #print(f"Config: {config}")

    plugin = rdma.plugin(name="BidirectionalPlugin", threads=[], protocol="RDMA")
    #print(f"Plugin: {plugin}")

    thread = rdma.thread(protocol = "RDMA")
    #print(f"Thread: {thread}")

    transfer_groupTx = rdma.transferGroup(name="TransferGroup_Callea_to_Cotterle_Tx",
                                         direction = rdma.Direction.TX,
                                         protocol = "RDMA")
    transfer_groupRx = rdma.transferGroup(name="TransferGroup_Cotterle_to_Callea_Rx",
                                             direction = rdma.Direction.RX,
                                             protocol = "RDMA")
    #print(f"Transfer Group: {transfer_group}")

    transferTx = rdma.transfer(name="Transfer_Callea_to_Cotterle_Tx",
                                    direction = rdma.Direction.TX,
                                    protocol = "RDMA",
                                    local_address = "169.254.23.111",
                                    local_port = 5011,
                                    destination_address = "169.254.49.44",
                                    destination_port = 5011)
    #print(f"Transfer TX: {transferTx}")

    transferRx = rdma.transfer(name="Transfer_Cotterle_to_Callea_Rx",
                                direction = rdma.Direction.RX,
                                protocol = "RDMA",
                                local_address = "169.254.23.111",
                                local_port = 5010)
    #print(f"Transfer RX: {transferRx}")

    channel = rdma.channel(name="Channel1",
                           protocol = "RDMA")
    #print(f"Channel: {channel}")

# assembly

transferRx.setChannels([channel])
transferTx.setChannels([channel])

transfer_groupTx.setTransfers([transferTx])
transfer_groupRx.setTransfers([transferRx])

thread.setTransferGroups([transfer_groupTx, transfer_groupRx])

plugin.setThreads([thread])

config.setPlugins([plugin] )

# Export config to JSON file
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)
with open(output_dir / "config.dsf", "w") as f:
    json.dump(config.getDict(), f, indent=4)

# Read config from JSON file
config_file = Path(__file__).resolve().parent.parent / "data" / "config_multidirectional_1_Callea_to_Cotterle_generated.dsf"
with open(config_file, "r") as f:
    loaded_config = json.load(f)

generated_config = config.getDict()
are_equal = loaded_config == generated_config

print(f"loaded_config == config.getDict(): {are_equal}")
if not are_equal:
    import pprint
    print("Generated config:")
    pprint.pp(generated_config)
    print("Loaded config:")
    pprint.pp(loaded_config)
