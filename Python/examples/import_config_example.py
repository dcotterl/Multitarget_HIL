import json
import logging
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import rdma_definitions as rdma

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "config_multidirectional_1_Callea_to_Cotterle_generated.dsf"


def round_trip_objects():
    logger.info("Creating and round-tripping RDMA objects")
    element = rdma.Element("key1", 3.14)
    component_settings = rdma.ComponentSettings("RDMA", [element, rdma.Element("key2", "value")])
    channel = rdma.Channel(protocol="rdma", name="channel1", unit="V")
    transfer = rdma.Transfer(protocol="rdma", channels=[channel])
    transfer_group = rdma.TransferGroup(transfers=[transfer])
    thread = rdma.Thread(protocol="rdma", transfer_groups=[transfer_group])
    plugin = rdma.Plugin(name="plugin1", threads=[thread], protocol="rdma")
    config = rdma.RDMA_Configuration(plugins=[plugin])

    clones = [
        rdma.Element.from_dict(element.getDict()),
        rdma.ComponentSettings.from_dict(component_settings.getDict()),
        rdma.Channel.from_dict(channel.getDict()),
        rdma.Transfer.from_dict(transfer.getDict()),
        rdma.TransferGroup.from_dict(transfer_group.getDict()),
        rdma.Thread.from_dict(thread.getDict()),
        rdma.Plugin.from_dict(plugin.getDict()),
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
