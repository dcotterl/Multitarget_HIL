import json
import logging
from pathlib import Path

from multitarget_hil import rdma_definitions as rdma

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "config_multidirectional_1_Callea_to_Cotterle_generated.dsf"


def round_trip_objects():
    logger.info("Creating and round-tripping RDMA objects")
    element = rdma.element("key1", 3.14)
    component_settings = rdma.component_settings("RDMA", [element, rdma.element("key2", "value")])
    channel = rdma.channel(protocol="rdma", name="channel1", unit="V")
    transfer = rdma.transfer(direction=rdma.Direction.TX, protocol="rdma", channels=[channel])
    transfer_group = rdma.transferGroup(transfers=[transfer])
    thread = rdma.thread(protocol="rdma", transfer_groups=[transfer_group])
    plugin = rdma.plugin(name="plugin1", threads=[thread], protocol="rdma")
    config = rdma.RDMA_Configuration(plugins=[plugin])

    clones = [
        rdma.element.from_dict(element.getDict()),
        rdma.component_settings.from_dict(component_settings.getDict()),
        rdma.channel.from_dict(channel.getDict()),
        rdma.transfer.from_dict(transfer.getDict()),
        rdma.transferGroup.from_dict(transfer_group.getDict()),
        rdma.thread.from_dict(thread.getDict()),
        rdma.plugin.from_dict(plugin.getDict()),
        rdma.RDMA_Configuration.from_dict(config.getDict()),
    ]
    logger.info("Round-trip succeeded for %d object types", len(clones))


def import_config_from_dsf():
    logger.info("Read and validate configuration from %s", DATA_PATH)
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        loaded_config = json.load(handle)
    config = rdma.RDMA_Configuration.from_dict(loaded_config)
    logger.info("Imported config matches file: %s", loaded_config == config.getDict())


def main():
    round_trip_objects()
    import_config_from_dsf()


if __name__ == "__main__":
    main()
