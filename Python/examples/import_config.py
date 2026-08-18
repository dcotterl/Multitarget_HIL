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

    logger.info("Creating an element and importing it into another element.")
    element = rdma.element("key1", 3.14)
    logger.debug(f"element: {element.getDict()}")
    element2 = rdma.element("", "")
    element2.importFromDict(element.getDict())
    logger.debug(f"element2: {element2.getDict()}")
    logger.info(f"Confronting element and element2: {element.getDict() == element2.getDict()}")

    logger.info("Creating a component_settings and importing it into another component_settings.")
    component_settings = rdma.component_settings("RDMA",[element,element2])
    logger.debug(f"component_settings: {component_settings.getDict()}")
    component_settings2 = rdma.component_settings()
    component_settings2.importFromDict(component_settings.getDict())
    logger.debug(f"component_settings2: {component_settings2.getDict()}")
    logger.info(f"Confronting component_settings and component_settings2: {component_settings.getDict() == component_settings2.getDict()}")

    logger.info("Creating a channel and importing it into another channel.")
    channel = rdma.channel(protocol="rdma", name="channel1", unit="V")
    logger.debug(f"channel: {channel.getDict()}") 
    channel2 = rdma.channel()
    channel2.importFromDict(channel.getDict())
    logger.debug(f"channel2: {channel2.getDict()}")
    logger.info(f"Confronting channel and channel2: {channel.getDict() == channel2.getDict()}")

    logger.info("Creating a transfer and importing it into another transfer.")
    transfer = rdma.transfer(direction=rdma.Direction.TX,
                             protocol="rdma",
                             channels=[channel, channel2])
    logger.debug(f"transfer: {transfer.getDict()}")
    transfer2 = rdma.transfer()
    transfer2.importFromDict(transfer.getDict())
    logger.debug(f"transfer2: {transfer2.getDict()}")
    logger.info(f"Confronting transfer and transfer2: {transfer.getDict() == transfer2.getDict()}")

    logger.info("Creating a transfer_group and importing it into another transfer_group.")
    transferGroup = rdma.transferGroup(transfers=[transfer, transfer2])
    logger.debug(f"transferGroup: {transferGroup.getDict()}")
    transferGroup2 = rdma.transferGroup()
    transferGroup2.importFromDict(transferGroup.getDict())
    logger.debug(f"transferGroup2: {transferGroup2.getDict()}")
    logger.info(f"Confronting transferGroup and transferGroup2: {transferGroup.getDict() == transferGroup2.getDict()}")