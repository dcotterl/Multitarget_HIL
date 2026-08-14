"""
Bidirectional OOP Example

This script demonstrates creating a bidirectional RDMA (Remote Direct Memory Access)
configuration using object-oriented programming patterns. It sets up:
- 10 communication channels
- Separate transmit and receive transfers between two endpoints
- Transfer groups organized by direction
- A complete RDMA configuration that is serialized to JSON

The configuration creates a symmetric communication setup where data flows in both
directions between the two specified network addresses.
"""

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

import RDMA_Definitions as rdma_def

if __name__ == "__main__":
	# Create 10 communication channels for data transfer
	channels = []
	for i in range (1, 11):
		channel = rdma_def.channel(f"Channel{i}", "")
		channels.append(channel)

	# Configure transmit transfer from Callea to Cotterle
	transfer_tx = rdma_def.transfer(rdma_def.Direction.TX, 
						  		name = "Transfer_Callea_to_Cotterle_Tx", 
								channels = channels, 
								local_address = "169.254.23.111", 
								local_port = 5011, 
								destination_address = "169.254.49.44", 
								destination_port = 5011)
	
	# Configure receive transfer from Cotterle to Callea
	transfer_rx = rdma_def.transfer(rdma_def.Direction.RX, 
								name = "Transfer_Cotterle_to_Callea_Rx", 
								channels = channels, 
								local_address = "169.254.23.111", 
								local_port = 5010)

	# Group transfers by direction
	transferGroup_tx = rdma_def.transferGroup("TransferGroup_Callea_to_Cotterle_Tx", rdma_def.Direction.TX, [transfer_tx])
	transferGroup_rx = rdma_def.transferGroup("TransferGroup_Cotterle_to_Callea_Rx", rdma_def.Direction.RX, [transfer_rx])

	# Create thread with both transfer groups for bidirectional communication
	thread = rdma_def.thread([transferGroup_tx, transferGroup_rx])

	# Create plugin containing the thread configuration
	plugin = rdma_def.plugin("BidirectionalPlugin", [thread])

	# Build complete RDMA configuration
	configuration = rdma_def.RDMA_Configuration([plugin])

	# Export configuration to JSON file
	output_dir = Path("output")
	output_dir.mkdir(exist_ok=True)

	with open(output_dir / "rdma_definitions.json", "w") as f:
		json.dump(configuration.getDict(), f, indent=4)