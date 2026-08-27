import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import udp_definitions as udp
from data_sharing_framework_config_api import definitions as d

def bottom_up():
    channel = udp.Channel(name="Channel1", unit="V")
    #print(f"Channel: {channel}")

    transfer_tx = udp.Transfer( name = "Transfer",
                                destination_address = "127.0.0.1",
                                destination_port = 50001,
                                channels = [channel, channel])

    #print(f"Transfer: {transfer_tx}")

    transfer_rx = udp.Transfer( name = "Transfer",
                                local_address = "127.0.0.1",
                                local_port = 50001,
                                channels = [channel, channel])
    #print(f"Transfer: {transfer_rx}")

    transfer_group_tx = udp.TransferGroup( name = "TransferGroup_tx",
                                          direction = d.Direction.TX,
                                          transfers = [transfer_tx,transfer_tx])

    #print(f"TransferGroup: {transfer_group_tx}")

    transfer_group_rx = udp.TransferGroup( name = "TransferGroup_rx",
                                          direction = d.Direction.RX,
                                          transfers = [transfer_rx,transfer_rx])
    #print(f"TransferGroup: {transfer_group_rx}")

    thread_tx = udp.Thread(
                        local_address = "127.0.0.1",
                        local_port = 50001,
                        transfer_groups = [transfer_group_tx])

    #print(f"Thread_tx: {thread_tx}")

    thread_rx = udp.Thread(
                        local_address = "127.0.0.1",
                        local_port = 50001,
                        transfer_groups = [transfer_group_rx])

    #print(f"Thread_rx: {thread_rx}")

    plugin = udp.Plugin(name = "Plugin", threads = [thread_tx, thread_rx])

    #print(f"Plugin: {plugin}")

    config = d.Configuration(plugins = [plugin])
    #print(f"Config: {config}")

if __name__ == "__main__":
    bottom_up()