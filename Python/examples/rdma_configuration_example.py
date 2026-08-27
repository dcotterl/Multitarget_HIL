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
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def bottom_up():
    logger.info("Create channels")
    channel = rdma.Channel(name="Channel1")

    logger.info("Create TX transfer")
    transfer_tx = rdma.Transfer(
        name="Transfer_Callea_to_Cotterle_Tx",
        local_address="169.254.23.111",
        local_port=5011,
        destination_address="169.254.49.44",
        destination_port=5011,
        channels=[channel],
    )

    logger.info("Create RX transfer")
    transfer_rx = rdma.Transfer(
        name="Transfer_Cotterle_to_Callea_Rx",
        local_address="169.254.23.111",
        local_port=5010,
        channels=[channel],
    )

    logger.info("Create transfer groups")
    transfer_group_tx = rdma.TransferGroup(
        name="TransferGroup_Callea_to_Cotterle_Tx",
        transfers=[transfer_tx],
    )
    transfer_group_rx = rdma.TransferGroup(
        name="TransferGroup_Cotterle_to_Callea_Rx",
        direction=d.Direction.RX,
        transfers=[transfer_rx],
    )

    logger.info("Create bidirectional thread and plugin")
    thread = rdma.Thread(transfer_groups=[transfer_group_tx, transfer_group_rx])
    plugin = rdma.Plugin(name="BidirectionalPlugin", threads=[thread])
    return d.Configuration(plugins=[plugin])


def top_down():
    config = d.Configuration()
    plugin = rdma.Plugin(name="BidirectionalPlugin", threads=[])
    thread = rdma.Thread()
    transfer_group_tx = rdma.TransferGroup(
        name="TransferGroup_Callea_to_Cotterle_Tx",
        direction=d.Direction.TX,
    )
    transfer_group_rx = rdma.TransferGroup(
        name="TransferGroup_Cotterle_to_Callea_Rx",
        direction=d.Direction.RX,
    )
    transfer_tx = rdma.Transfer(
        name="Transfer_Callea_to_Cotterle_Tx",
        local_address="169.254.23.111",
        local_port=5011,
        destination_address="169.254.49.44",
        destination_port=5011,
    )
    transfer_rx = rdma.Transfer(
        name="Transfer_Cotterle_to_Callea_Rx",
        local_address="169.254.23.111",
        local_port=5010,
    )
    channel = rdma.Channel(name="Channel1")

    transfer_rx.channels = [channel]
    transfer_tx.channels = [channel]
    transfer_group_tx.transfers = [transfer_tx]
    transfer_group_rx.transfers = [transfer_rx]
    thread.transfer_groups = [transfer_group_tx, transfer_group_rx]
    plugin.threads = [thread]
    config.plugins = [plugin]
    return config


def export_and_compare(name: str, config: d.Configuration):
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
