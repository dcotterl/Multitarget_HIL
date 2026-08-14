import json
from enum import Enum
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

class Direction(Enum):
	TX = 0
	RX = 1

class component_settings:

    def __init__(self, component, initial_values=[]):
        self.component_settings = []
        self.add_setting(component, initial_values)

    def add_setting(self, component, values=[]):
        self.component_settings.append({"component": component, "values": values})

    def __str__(self):
         return json.dumps(self.component_settings, indent=4)

    def getSettings(self):
         return self.component_settings

class channel:
     def __init__(self, name, unit = "", engine_data_type = 2, string_data_type = 2, string_offset = 0):
            cs = component_settings("RDMA")

            self.channel = {"core":{
                                "name": name,
                                "units": unit,
                                "engine data type": engine_data_type,
                                "string data type": string_data_type,
                                "string offset": string_offset,
                                },
                                "component settings": cs.getSettings()}
            logger.debug(f"Creating channel {name} with unit {unit}, engine_data_type {engine_data_type}, string_data_type {string_data_type}, string_offset {string_offset}")

     def __str__(self):
        return json.dumps(self.channel, indent=4)

     def getChannel(self):
        return self.channel

class transfer:
     def __init__(self, direction: Direction, name, channels, local_address, local_port, destination_address=None, destination_port=None):

        settings = None
        self.direction = direction

        if direction == Direction.TX:
            settings = self.__Setting_TX_Transfer(local_address, local_port, destination_address, destination_port)
        elif direction == Direction.RX:
            settings = self.__Setting_RX_Transfer(local_address, local_port)

        chs = []
        for ch in channels:
            chs.append(ch.getChannel())

        self.transfer = {
                        "core": {"name" : name},
                        "component settings": settings.getSettings(),
                        "channels": chs
                        }
        logger.debug(f"Created transfer {name} with direction {direction.name}, details:\n{json.dumps(self.transfer, indent=4)}")

     def __Setting_TX_Transfer(self, local_address, local_port, destination_address, destination_port):
        cs = component_settings("RDMA", [{"key" : "local address", "value" : str(local_address)},
                                          {"key" : "local port", "value" : str(local_port)},
                                          {"key" : "destination address", "value" : str(destination_address)},
                                          {"key" : "destination port", "value" : str(destination_port)}])
        return cs

     def __Setting_RX_Transfer(self, local_address, local_port):
        cs = component_settings("RDMA", [{"key" : "local address", "value" : str(local_address)},
                                         {"key" : "local port", "value" : str(local_port)}])
        return cs

     def getTransfer(self):
         return self.transfer

     def getTransferDirection(self):
         return self.direction

     def addChannel(self, channel):
         self.transfer["channels"].append(channel.getChannel())

     def __str__(self):
         return json.dumps(self.transfer, indent=4)

class transferGroup:
    def __init__(self, name, direction: Direction, transfers):
        self.direction = direction
        transfer_array = []
        for transfer in transfers:
            if transfer.getTransferDirection() != self.direction:
                raise ValueError(f"Transfer group name '{name}' has a transfer with a mismatched direction.")
            else:
                transfer_array.append(transfer.getTransfer())

        self.transferGroup = {"core" : {
                                            "name" : name,
                                            "direction" : direction.value,
                                            "cycle timing" : {
                                                "priority" : 100,
                                                "decimation" : 1,
                                                "offset" : 0
                                            },
                                            "timeout behavior" : 0,
                                            "enable conversion" : False,
                                        },
                                        "component settings" : [component_settings("RDMA").getSettings()[0]],
                                        "transfers" : transfer_array
                             }

    def __str__(self):
        return json.dumps(self.transferGroup, indent=4)

    def getTransferGroup(self):
        return self.transferGroup

    def add_transfer(self, transfer):
        if transfer.getTransferDirection() != self.direction:
            raise ValueError(f"Tramsfer has incompatible direction with transfer group. Transfer direction: {transfer.getTransferDirection().name}, Transfer group direction: {self.direction.name}")
        else:
            self.transferGroup["transfers"].append(transfer.getTransfer())

class thread:
    def __init__(self, transferGroups):

        tg_array = []
        for tg in transferGroups:
            tg_array.append(tg.getTransferGroup())
        settings = component_settings("RDMA").getSettings()
        self.thread = {"core" : {
                                "processor" : -2,
                                "priority offset" : 0
                                },
                        "component settings" : settings,
                        "transfer groups" : tg_array
                        }
                               

    def __str__(self):
        return json.dumps(self.thread, indent=4)

    def getThread(self):
        return self.thread

    def add_transferGroup(self, transferGroup):
        self.thread["transfer groups"].append(transferGroup.getTransferGroup())

class plugin:
    def __init__(self, name, threads):
        thread_array = []
        for th in threads:
            thread_array.append(th.getThread())

        self.plugin = {"core" : {
                                "name" : name,
                                "components" : ["RDMA"],
                                "cycle timing" : {
                                                "priority" : 10000,
                                                "decimation" : 1,
                                                "offset" : 0
                                                },
                                },
                        "component settings" : component_settings("RDMA").getSettings(),
                        "threads" : thread_array
                        }
                        
    def add_thread(self, thread):
        self.plugin["threads"].append(thread.getThread())

    def __str__(self):
        return json.dumps(self.plugin, indent=4)

    def getPlugin(self):
        return self.plugin

class RDMA_Configuration:
    def __init__(self, plugins):
        plgs = []
        for plugin in plugins:
            plgs.append(plugin.getPlugin())
        self.definition = {
                            "dsfversion": {
                                 "major": 1,
                                 "minor": 4,
                                 "fix": 0,
                                 "build": "",
                             },
                             "version": {
                                 "major": 1,
                                 "minor": 0,
                                 "fix": 0,
                                 "build": "",
                             },
                             "configuration": {
                                 "plugins": plgs,
                             }       
                        }

    def __str__(self):
        return json.dumps(self.definition, indent=4)

    def getConfiguration(self):
        return self.definition

    def addPlugin(self, plugin):
        self.definition["configuration"]["plugins"].append(plugin.getPlugin())

def get_version():
    return {"major": 1, "minor": 0, "fix": 0, "build": ""}

if __name__ == "__main__":



    chs = []

    for i in range(0, 2):
        c = channel(f"channel{i+1}")
        chs.append(c)
  
    c_jolly = channel("channel_jolly")

    t = transfer(Direction.TX, "transfer1", chs, "1.2.3.4", 1234, "5.6.7.8", 5678)
    #t.addChannel(c_jolly)

    #logger.info(f"Created transfer: {json.dumps(t.getTransfer(), indent=4)}")

    t_jolly = transfer(Direction.TX, "transfer_jolly", [c_jolly], "9.10.11.12", 9101112, "5.6.7.8", 5678)


    tg = transferGroup("transferGroup1", Direction.TX, [t])
    #logger.info(f"Created transfer group: {json.dumps(tg.getTransferGroup(), indent=4)}")

    tg.add_transfer(t_jolly)
    #logger.info(json.dumps(tg.getTransferGroup(), indent=4))

    th = thread([tg])
    #logger.info(f"Created thread: {json.dumps(th.getThread(), indent=4)}")

    pl1 = plugin("plugin1", [th])
    #logger.info(f"Created plugin: {json.dumps(pl1.getPlugin(), indent=4)}")

    pl2 = plugin("plugin2", [th])
    rdma_def = RDMA_Configuration([pl1, pl2])
    #rdma_def.addPlugin(pl2)

    #logger.info(f"Created RDMA definitions: {json.dumps(rdma_def.getConfiguration(), indent=4)}")

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "rdma_definitions.json", "w") as f:
        json.dump(rdma_def.getConfiguration(), f, indent=4)