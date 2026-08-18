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

    logger.info(f"Create RDMA configuration for bidirectional communication between Callea and Cotterle")
    config = rdma.RDMA_Configuration()
    logger.debug(f"Config: {config}")

    logger.info(f"Create plugin for bidirectional communication")
    plugin = rdma.plugin(name="BidirectionalPlugin", threads=[], protocol="RDMA")
    logger.debug(f"Plugin: {plugin}")

    logger.info(f"Create thread for bidirectional communication")
    thread = rdma.thread(protocol = "RDMA")
    logger.debug(f"Thread: {thread}")

    logger.info(f"Create Tx Transfer Group")
    transfer_groupTx = rdma.transferGroup(name="TransferGroup_Callea_to_Cotterle_Tx",
                                         direction = rdma.Direction.TX,
                                         protocol = "RDMA")
    logger.debug(f"Transfer Group TX: {transfer_groupTx}")

    logger.info(f"Create Rx Transfer Group")
    transfer_groupRx = rdma.transferGroup(name="TransferGroup_Cotterle_to_Callea_Rx",
                                             direction = rdma.Direction.RX,
                                             protocol = "RDMA")
    logger.debug(f"Transfer Group RX: {transfer_groupRx}")


    logger.info(f"Create Tx Transfer")
    transferTx = rdma.transfer(name="Transfer_Callea_to_Cotterle_Tx",
                                    direction = rdma.Direction.TX,
                                    protocol = "RDMA",
                                    local_address = "169.254.23.111",
                                    local_port = 5011,
                                    destination_address = "169.254.49.44",
                                    destination_port = 5011)
    logger.debug(f"Transfer TX: {transferTx}")

    logger.info(f"Create Rx Transfer")
    transferRx = rdma.transfer(name="Transfer_Cotterle_to_Callea_Rx",
                                direction = rdma.Direction.RX,
                                protocol = "RDMA",
                                local_address = "169.254.23.111",
                                local_port = 5010)
    logger.debug(f"Transfer RX: {transferRx}")

    logger.info(f"Create Channel")
    channel = rdma.channel(name="Channel1",
                           protocol = "RDMA")
    logger.debug(f"Channel: {channel}")

    # assembly

    logger.info(f"Start assembly of the configuration")

    logger.info(f"Set channels for transfers")
    transferRx.setChannels([channel])
    logger.debug(f"Transfer RX: {transferRx}")
    transferTx.setChannels([channel])
    logger.debug(f"Transfer TX: {transferTx}")

    logger.info(f"Set transfers for transfer groups")
    transfer_groupTx.setTransfers([transferTx])
    logger.debug(f"Transfer Group TX: {transfer_groupTx}")
    transfer_groupRx.setTransfers([transferRx])
    logger.debug(f"Transfer Group RX: {transfer_groupRx}")

    logger.info(f"Set transfer groups for thread")
    thread.setTransferGroups([transfer_groupTx, transfer_groupRx])
    logger.debug(f"Thread: {thread}")

    logger.info(f"Set threads for plugin")
    plugin.setThreads([thread])
    logger.debug(f"Plugin: {plugin}")

    logger.info(f"Set plugins for configuration")
    config.setPlugins([plugin])
    logger.debug(f"Config: {config}")

    # Export config to JSON file
    logger.info(f"Export configuration to .dsf file")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "config.dsf", "w") as f:
        json.dump(config.getDict(), f, indent=4)
    logger.info(f"Configuration exported to {output_dir / 'config.dsf'}")

    # Read config from JSON file
    logger.info(f"Read configuration from .dsf file to use as reference for comparison")
    config_file = Path(__file__).resolve().parent.parent / "data" / "config_multidirectional_1_Callea_to_Cotterle_generated.dsf"
    with open(config_file, "r") as f:
        loaded_config = json.load(f)
    logger.debug(f"Loaded config: {loaded_config}")

    generated_config = config.getDict()
    are_equal = loaded_config == generated_config

    logger.info(f"Compare: loaded_config == config.getDict(): {are_equal}")
