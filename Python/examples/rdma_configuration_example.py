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
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def bottom_up():
    logger.info("Create channels")
    channel = rdma.channel(name="Channel1", protocol="RDMA")

    logger.info("Create TX transfer")
    transfer_tx = rdma.transfer(
        name="Transfer_Callea_to_Cotterle_Tx",
        direction=rdma.Direction.TX,
        protocol="RDMA",
        local_address="169.254.23.111",
        local_port=5011,
        destination_address="169.254.49.44",
        destination_port=5011,
        channels=[channel],
    )

    logger.info("Create RX transfer")
    transfer_rx = rdma.transfer(
        name="Transfer_Cotterle_to_Callea_Rx",
        direction=rdma.Direction.RX,
        protocol="RDMA",
        local_address="169.254.23.111",
        local_port=5010,
        channels=[channel],
    )

    logger.info("Create transfer groups")
    transfer_group_tx = rdma.transferGroup(
        name="TransferGroup_Callea_to_Cotterle_Tx",
        direction=rdma.Direction.TX,
        protocol="RDMA",
        transfers=[transfer_tx],
    )
    transfer_group_rx = rdma.transferGroup(
        name="TransferGroup_Cotterle_to_Callea_Rx",
        direction=rdma.Direction.RX,
        protocol="RDMA",
        transfers=[transfer_rx],
    )

    logger.info("Create bidirectional thread and plugin")
    thread = rdma.thread(protocol="RDMA", transfer_groups=[transfer_group_tx, transfer_group_rx])
    plugin = rdma.plugin(name="BidirectionalPlugin", protocol="RDMA", threads=[thread])
    return rdma.RDMA_Configuration(plugins=[plugin])


def top_down():
    config = rdma.RDMA_Configuration()
    plugin = rdma.plugin(name="BidirectionalPlugin", threads=[], protocol="RDMA")
    thread = rdma.thread(protocol="RDMA")
    transfer_group_tx = rdma.transferGroup(
        name="TransferGroup_Callea_to_Cotterle_Tx",
        direction=rdma.Direction.TX,
        protocol="RDMA",
    )
    transfer_group_rx = rdma.transferGroup(
        name="TransferGroup_Cotterle_to_Callea_Rx",
        direction=rdma.Direction.RX,
        protocol="RDMA",
    )
    transfer_tx = rdma.transfer(
        name="Transfer_Callea_to_Cotterle_Tx",
        direction=rdma.Direction.TX,
        protocol="RDMA",
        local_address="169.254.23.111",
        local_port=5011,
        destination_address="169.254.49.44",
        destination_port=5011,
    )
    transfer_rx = rdma.transfer(
        name="Transfer_Cotterle_to_Callea_Rx",
        direction=rdma.Direction.RX,
        protocol="RDMA",
        local_address="169.254.23.111",
        local_port=5010,
    )
    channel = rdma.channel(name="Channel1", protocol="RDMA")

    transfer_rx.channels = [channel]
    transfer_tx.channels = [channel]
    transfer_group_tx.transfers = [transfer_tx]
    transfer_group_rx.transfers = [transfer_rx]
    thread.transfer_groups = [transfer_group_tx, transfer_group_rx]
    plugin.threads = [thread]
    config.plugins = [plugin]
    return config


def export_and_compare(name: str, config: rdma.RDMA_Configuration):
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"{name}.dsf"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(config.getDict(), handle, indent=4)
    logger.info("Configuration exported to %s", output_path)

    reference_path = DATA_DIR / "config_multidirectional_1_Callea_to_Cotterle_generated.dsf"
    with reference_path.open("r", encoding="utf-8") as handle:
        loaded_config = json.load(handle)
    logger.info("Matches reference config: %s", loaded_config == config.getDict())


def main():
    logger.info("Running top-down configuration generation")
    export_and_compare("configTD", top_down())
    logger.info("Running bottom-up configuration generation")
    export_and_compare("configBU", bottom_up())


if __name__ == "__main__":
    main()
