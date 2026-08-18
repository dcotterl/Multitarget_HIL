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

    value = rdma.element("key_name", "value_data")
    #print(value)

    component_settings = rdma.component_settings("RDMA", [value, value])
    #print(json.dumps(component_settings.getDict(), indent=4))

    array_of_settings = [component_settings]
    #print(json.dumps([s.getDict() for s in array_of_settings], indent=4))

    component_settings = rdma.component_settings("RDMA")
    channel = rdma.channel([component_settings], "channel_name")
    #print(json.dumps(channel.getDict(), indent=4))
  
    channels = [channel, channel]

    transfer = rdma.transfer(rdma.Direction.TX, 
                             "RDMA", "transferTx",
                             channels,
                             "1.2.3.4",
                             1234,
                             "5.6.7.8",
                             5678)
    #print(json.dumps(transfer.getDict(), indent=4))

    tg = rdma.transferGroup("group",
                            rdma.Direction.TX,
                            protocol="RDMA",
                            transfers=[transfer])
    #print(json.dumps(tg.getDict(), indent=4))

    th = rdma.thread(protocol="RDMA",
                     transfer_groups=[tg])
    #print(json.dumps(th.getDict(), indent=4))

    plugin = rdma.plugin(name="bidirectionalPlugin",
                         protocol="RDMA",
                         threads=[th])
    
    #print(json.dumps(plugin.getDict(), indent=4))

    cfg = rdma.RDMA_Configuration([plugin])
    print(json.dumps(cfg.getDict(), indent=4))