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

import RDMA_Definitions as rdad

if __name__ == "__main__":

	channels = []
	for i in range (1, 11):
		channel = rdad.channel(f"Channel{i}", "")
		channels.append(channel)

	transfer_tx = rdad.transfer(rdad.Direction.TX, 
						  		name = "Transfer_Callea_to_Cotterle_Tx", 
								channels = channels, 
								local_address = "169.254.23.111", 
								local_port = 5011, 
								destination_address = "169.254.49.44", 
								destination_port = 5011)
	
	transfer_rx = rdad.transfer(rdad.Direction.RX, 
								name = "Transfer_Cotterle_to_Callea_Rx", 
								channels = channels, 
								local_address = "169.254.23.111", 
								local_port = 5010)



	transferGroup_tx = rdad.transferGroup("TransferGroup_Callea_to_Cotterle_Tx", rdad.Direction.TX, [transfer_tx])
	transferGroup_rx = rdad.transferGroup("TransferGroup_Cotterle_to_Callea_Rx", rdad.Direction.RX, [transfer_rx])

	thread = rdad.thread([transferGroup_tx, transferGroup_rx])

	plugin = rdad.plugin("BidirectionalPlugin", [thread])

	configuration = rdad.RDMA_Configuration([plugin])

	output_dir = Path("output")
	output_dir.mkdir(exist_ok=True)

	with open(output_dir / "rdma_definitions.json", "w") as f:
		json.dump(configuration.getConfiguration(), f, indent=4)