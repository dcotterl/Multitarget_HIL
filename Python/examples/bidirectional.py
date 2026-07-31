import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import RDMA_JSON_Config as rjc
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    force=True
)
logger = logging.getLogger(__name__)

# Hierarchy of templates:
#    config file
#        plugin [1..n]
#            thread [1..n]
#                transfer group [1..n]
#                    transfer [1..n]
#                        channel [1..n]


def make_multidirection_n_channels(nchannels, local_ip, local_tx_port, local_rx_port, dest_ip, dest_tx_port, dest_rx_port, local_name="C1", dest_name="C2"):

    # Create channels for bidirectional communication
    channels = rjc.makeChannels(nchannels)
    logger.info(f"Created {nchannels} channels for bidirectional communication.")

    # Create Tx Transfer
    logger.info(f"Creating TX transfer from {local_name} {local_ip}:{local_tx_port} to {dest_name} {dest_ip}:{dest_tx_port}.")
    transfer_tx = rjc.makeTransfers(
        direction=rjc.Direction.TX,
        channels=channels,
        localIP=local_ip,
        localPort=local_tx_port,
        destIP=dest_ip,
        destPort=dest_rx_port,
        name_prefix=f"Transfer_{local_name}_to_{dest_name}_"
    )

    logger.debug(json.dumps(transfer_tx, indent=4))

    # Create Rx Transfer
    logger.info(f"Creating RX transfer from {dest_name} {dest_ip}:{dest_tx_port} to {local_name} {local_ip}:{local_rx_port}.")
    transfer_rx = rjc.makeTransfers(
        direction=rjc.Direction.RX,
        channels=channels,
        localIP=local_ip,
        localPort=local_rx_port,
        name_prefix=f"Transfer_{dest_name}_to_{local_name}_"
    )

    logger.debug(json.dumps(transfer_rx, indent=4))


    """# Create channels for bidirectional communication
    channels = rjc.makeChannels(number_of_channels)
    logger.info(f"Created {number_of_channels} channels for bidirectional communication.")

    # Create transfers for bidirectional communication
    transfer_tx = rjc.makeTransfers(
        direction=rjc.Direction.TX,
        channels=channels,
        localIP=c1_rdma_ip,
        localPort=c1_tx_port,
        destIP=c2_rdma_ip,
        destPort=c2_rx_port,
        name_prefix="Transfer_C1_to_C2_"
    )

    logger.debug(json.dumps(transfer_tx, indent=4))
    logger.info(f"Created TX transfer from {c1_rdma_ip}:{c1_tx_port} to {c2_rdma_ip}:{c2_rx_port}.")

    transfer_rx = rjc.makeTransfers(
        direction=rjc.Direction.RX,
        channels=channels,
        localIP=c1_rdma_ip,
        localPort=c1_rx_port,
        name_prefix="Transfer_C2_to_C1_"
    )

    logger.debug(json.dumps(transfer_rx, indent=4))
    logger.info(f"Created RX transfer from {c2_rdma_ip}:{c2_tx_port} to {c1_rdma_ip}:{c1_rx_port}.")
    
"""

    # Create Tx transfer group to contain the transfer
    logger.info(f"Creating TX transfer group TransferGroup_{local_name}_to_{dest_name}_.")
    group_tx = rjc.makeTransferGroups(
        direction=rjc.Direction.TX,
        transfers=[transfer_tx],
        groupName=f"TransferGroup_{local_name}_to_{dest_name}_"
    )
    logger.debug(json.dumps(group_tx, indent=4))

    # Create Rx transfer group to contain the transfer
    logger.info(f"Creating RX transfer group TransferGroup_{dest_name}_to_{local_name}_.")
    group_rx = rjc.makeTransferGroups(
        direction=rjc.Direction.RX,
        transfers=[transfer_rx],
        groupName=f"TransferGroup_{dest_name}_to_{local_name}_"
    )
    logger.debug(json.dumps(group_rx, indent=4))

    # Create threads to contain the transfer groups
    logger.info(f"Creating thread to contain the transfer groups.")
    thread = rjc.makeThreads([group_tx, group_rx])
    logger.debug(json.dumps(thread, indent=4))

    # Create plugin for bidirectional communication
    logger.info(f"Creating plugin for bidirectional communication.")
    plugin = rjc.makePlugins(threads=[thread], name="BidirectionalPlugin")
    logger.debug(json.dumps(plugin, indent=4))

    # Create configuration file for bidirectional communication
    logger.info(f"Creating configuration file for bidirectional communication.")
    config_file = rjc.makeConfigFile(plugins=[plugin])
    logger.debug(json.dumps(config_file, indent=4))

    # Print the file path where the configuration file will be saved
    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, f"config_multidirectional_{number_of_channels}_{local_name}_to_{dest_name}_generated.dsf")
    logger.info(f"Saving configuration file to: {output_path}")

    with open(output_path, "w") as outfile:
            json.dump(config_file, outfile, indent=4)
    logger.info(f"Configuration file saved successfully.")



if __name__ == "__main__":
    c1_rdma_ip, c1_tx_port, c1_rx_port = "169.254.49.44", 5010, 5011
    c2_rdma_ip, c2_tx_port, c2_rx_port = "169.254.23.111", 5011, 5010

    number_of_channels = 1


    make_multidirection_n_channels(
        nchannels=number_of_channels,
        local_ip=c1_rdma_ip,
        local_tx_port=c1_tx_port,
        local_rx_port=c1_rx_port,
        dest_ip=c2_rdma_ip,
        dest_tx_port=c2_tx_port,
        dest_rx_port=c2_rx_port,
        local_name="Cotterle",
        dest_name="Callea"
    )

    make_multidirection_n_channels(
        nchannels=number_of_channels,
        local_ip=c2_rdma_ip,
        local_tx_port=c2_tx_port,
        local_rx_port=c2_rx_port,
        dest_ip=c1_rdma_ip,
        dest_tx_port=c1_tx_port,
        dest_rx_port=c1_rx_port,
        local_name="Callea",
        dest_name="Cotterle"
    )