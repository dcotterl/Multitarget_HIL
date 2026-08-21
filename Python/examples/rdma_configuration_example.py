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

def bottomUp():
# Create a complete RDMA configuration using a bottom-up approach, starting with the creation of channels, transfers, transfer groups, threads, and plugins, and finally assembling them into a complete configuration.
    logger.info("Create channels")
    channels = rdma.channel(name="Channel1", protocol="RDMA")
    logger.info("Create Tx Transfer")
    transferTx = rdma.transfer(name="Transfer_Callea_to_Cotterle_Tx",
                                    direction = rdma.Direction.TX,
                                    protocol = "RDMA",
                                    local_address = "169.254.23.111",
                                    local_port = 5011,
                                    destination_address = "169.254.49.44",
                                    destination_port = 5011,
                                    channels = [channels])
    logger.debug(f"Transfer TX: {transferTx}")

    logger.info("Create Rx Transfer")
    transferRx = rdma.transfer(name="Transfer_Cotterle_to_Callea_Rx",
                                direction = rdma.Direction.RX,
                                protocol = "RDMA",
                                local_address = "169.254.23.111",
                                local_port = 5010,
                                channels = [channels])
    logger.debug(f"Transfer RX: {transferRx}")

    logger.info("Create Tx Transfer Group")
    transfer_groupTx = rdma.transferGroup(name="TransferGroup_Callea_to_Cotterle_Tx",
                                         direction = rdma.Direction.TX,
                                         protocol = "RDMA",
                                         transfers = [transferTx])
    logger.debug(f"Transfer Group TX: {transfer_groupTx}")

    logger.info("Create Rx Transfer Group")
    transfer_groupRx = rdma.transferGroup(name="TransferGroup_Cotterle_to_Callea_Rx",
                                             direction = rdma.Direction.RX,
                                             protocol = "RDMA",
                                             transfers = [transferRx])
    logger.debug(f"Transfer Group RX: {transfer_groupRx}")

    logger.info("Create thread for bidirectional communication")
    thread = rdma.thread(protocol = "RDMA", transfer_groups = [transfer_groupTx, transfer_groupRx])
    logger.debug(f"Thread: {thread}")

    logger.info("Create plugin for bidirectional communication")
    plugin = rdma.plugin(name="BidirectionalPlugin", protocol="RDMA",threads = [thread])
    logger.debug(f"Plugin: {plugin}")

    logger.info("Create RDMA configuration for bidirectional communication between Callea and Cotterle")
    config = rdma.RDMA_Configuration(plugins = [plugin])
    logger.debug(f"Config: {config}")

    # Export config to JSON file
    logger.info("Export configuration to .dsf file")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "configBU.dsf", "w") as f:
        json.dump(config.getDict(), f, indent=4)
    logger.info(f"Configuration exported to {output_dir / 'configBU.dsf'}")

    # Read config from JSON file
    logger.info("Read configuration from .dsf file to use as reference for comparison")
    config_file = Path(__file__).resolve().parent.parent / "data" / "config_multidirectional_1_Callea_to_Cotterle_generated.dsf"
    with open(config_file, "r") as f:
        loaded_config = json.load(f)
    logger.debug(f"Loaded config: {loaded_config}")

    generated_config = config.getDict()
    are_equal = loaded_config == generated_config

    logger.info(f"Compare: loaded_config == config.getDict(): {are_equal}\n\n\n")

def topDown():
    # Generate the configuration top down, starting with the configuration object and adding plugins, threads, transfer groups, transfers, and channels.
    config = rdma.RDMA_Configuration()
    logger.debug(f"Config: {config}")

    logger.info("Create plugin for bidirectional communication")
    plugin = rdma.plugin(name="BidirectionalPlugin", threads=[], protocol="RDMA")
    logger.debug(f"Plugin: {plugin}")

    logger.info("Create thread for bidirectional communication")
    thread = rdma.thread(protocol = "RDMA")
    logger.debug(f"Thread: {thread}")

    logger.info("Create Tx Transfer Group")
    transfer_groupTx = rdma.transferGroup(name="TransferGroup_Callea_to_Cotterle_Tx",
                                         direction = rdma.Direction.TX,
                                         protocol = "RDMA")
    logger.debug(f"Transfer Group TX: {transfer_groupTx}")

    logger.info("Create Rx Transfer Group")
    transfer_groupRx = rdma.transferGroup(name="TransferGroup_Cotterle_to_Callea_Rx",
                                             direction = rdma.Direction.RX,
                                             protocol = "RDMA")
    logger.debug(f"Transfer Group RX: {transfer_groupRx}")


    logger.info("Create Tx Transfer")
    transferTx = rdma.transfer(name="Transfer_Callea_to_Cotterle_Tx",
                                    direction = rdma.Direction.TX,
                                    protocol = "RDMA",
                                    local_address = "169.254.23.111",
                                    local_port = 5011,
                                    destination_address = "169.254.49.44",
                                    destination_port = 5011)
    logger.debug(f"Transfer TX: {transferTx}")

    logger.info("Create Rx Transfer")
    transferRx = rdma.transfer(name="Transfer_Cotterle_to_Callea_Rx",
                                direction = rdma.Direction.RX,
                                protocol = "RDMA",
                                local_address = "169.254.23.111",
                                local_port = 5010)
    logger.debug(f"Transfer RX: {transferRx}")

    logger.info("Create Channel")
    channel = rdma.channel(name="Channel1",
                           protocol = "RDMA")
    logger.debug(f"Channel: {channel}")

# assembly

    logger.info("Start assembly of the configuration")

    logger.info("Set channels for transfers")
    transferRx.channels = [channel]
    logger.debug(f"Transfer RX: {transferRx}")
    transferTx.channels = [channel]
    logger.debug(f"Transfer TX: {transferTx}")

    logger.info("Set transfers for transfer groups")
    transfer_groupTx.transfers = [transferTx]
    logger.debug(f"Transfer Group TX: {transfer_groupTx}")
    transfer_groupRx.transfers = [transferRx]
    logger.debug(f"Transfer Group RX: {transfer_groupRx}")

    logger.info("Set transfer groups for thread")
    thread.transfer_groups = [transfer_groupTx, transfer_groupRx]
    logger.debug(f"Thread: {thread}")

    logger.info("Set threads for plugin")
    plugin.threads = [thread]
    logger.debug(f"Plugin: {plugin}")

    logger.info("Set plugins for configuration")
    config.plugins = [plugin]
    logger.debug(f"Config: {config}")

    # Export config to JSON file
    logger.info("Export configuration to .dsf file")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "configTD.dsf", "w") as f:
        json.dump(config.getDict(), f, indent=4)
    logger.info(f"Configuration exported to {output_dir / 'configTD.dsf'}")

    # Read config from JSON file
    logger.info("Read configuration from .dsf file to use as reference for comparison")
    config_file = Path(__file__).resolve().parent.parent / "data" / "config_multidirectional_1_Callea_to_Cotterle_generated.dsf"
    with open(config_file, "r") as f:
        loaded_config = json.load(f)
    logger.debug(f"Loaded config: {loaded_config}")

    generated_config = config.getDict()
    are_equal = loaded_config == generated_config

    logger.info(f"Compare: loaded_config == config.getDict(): {are_equal}\n\n\n")

if __name__ == "__main__":
    logger.info("Running Top Down Configuration Generation")
    topDown()

    logger.info("Running Bottom Up Configuration Generation")
    bottomUp()
