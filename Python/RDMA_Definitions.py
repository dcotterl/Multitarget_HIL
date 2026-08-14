"""RDMA definition model and JSON serializer.

This module provides lightweight classes for constructing an RDMA
configuration in the same hierarchy used by the serialized definition:

    RDMA_Configuration
    └── plugin
        └── thread
            └── transferGroup
                └── transfer
                    └── channel

Each object stores its definition as a dictionary, exposes it through
``getDict()``, and can be rendered as formatted JSON with ``str()``.
``component_settings`` stores component-specific settings used by channels,
transfers, transfer groups, threads, and plugins.  ``Direction`` identifies
transfers and transfer groups as transmit (TX) or receive (RX); a transfer
group rejects transfers with a different direction.

The hierarchy assembled by the ``__main__`` example is:

* Two ``channel`` objects (``channel1`` and ``channel2``) are placed in
  ``transfer1``.
* ``transfer_jolly`` contains a separate ``channel_jolly``.
* Both TX transfers are placed in ``transferGroup1``.
* ``transferGroup1`` is placed in one ``thread``.
* The thread is shared by ``plugin1`` and ``plugin2``.
* Both plugins are placed in ``RDMA_Configuration``.

The resulting configuration is serialized to
``output/rdma_definitions.json`` when this file is run as a script.  The
top-level configuration also contains DSF and definition version metadata.
"""

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
    """Direction of an RDMA transfer."""
    TX = 0
    RX = 1

class component_settings:
    """Store component-specific settings for an RDMA object."""

    def __init__(self, component, initial_values=[]):
        """Create settings for ``component`` with optional initial values."""
        self.component_settings = []
        self.add_setting(component, initial_values)

    def add_setting(self, component, values=[]):
        """Append a component and its associated values."""
        self.component_settings.append({"component": component, "values": values})

    def __str__(self):
         """Return the settings as formatted JSON."""
         return json.dumps(self.component_settings, indent=4)

    def getDict(self):
         """Return the settings as a list of dictionaries."""
         return self.component_settings

class channel:
     """Represent an RDMA channel definition and its serialized settings."""

     def __init__(self, name, unit = "", engine_data_type = 2, string_data_type = 2, string_offset = 0):
            """Initialize a channel.

            Args:
                name: Channel name.
                unit: Engineering unit string for the channel.
                engine_data_type: Numeric engine-side data type identifier.
                string_data_type: Numeric string-side data type identifier.
                string_offset: String table offset for this channel.
            """
            cs = component_settings("RDMA")

            self.channel = {"core":{
                                "name": name,
                                "units": unit,
                                "engine data type": engine_data_type,
                                "string data type": string_data_type,
                                "string offset": string_offset,
                                },
                                "component settings": cs.getDict()}
            logger.debug(f"Creating channel {name} with unit {unit}, engine_data_type {engine_data_type}, string_data_type {string_data_type}, string_offset {string_offset}")

     def __str__(self):
          """Return a formatted JSON string representation of the channel."""
          return json.dumps(self.channel, indent=4)

     def getDict(self):
          """Return the channel as a dictionary for serialization or composition."""
          return self.channel

class transfer:
     """Represents an RDMA data transfer configuration with direction-specific settings.
     
     Manages TX (transmit) or RX (receive) transfers with associated channels and network parameters.
     """
     def __init__(self, direction: Direction, name, channels, local_address, local_port, destination_address=None, destination_port=None):
          """Initialize a transfer with direction and network settings.
          
          Args:
               direction: Direction enum (TX or RX) specifying transfer direction.
               name: String name identifier for this transfer.
               channels: List of channel objects to include in this transfer.
               local_address: Local network address (IP or hostname).
               local_port: Local port number for the transfer.
               destination_address: Remote address for TX transfers (required for TX, ignored for RX).
               destination_port: Remote port for TX transfers (required for TX, ignored for RX).
          """
          settings = None
          self.direction = direction

          if direction == Direction.TX:
               settings = self.__Setting_TX_Transfer(local_address, local_port, destination_address, destination_port)
          elif direction == Direction.RX:
               settings = self.__Setting_RX_Transfer(local_address, local_port)

          chs = []
          for ch in channels:
               chs.append(ch.getDict())

          self.transfer = {
                          "core": {"name" : name},
                          "component settings": settings.getDict(),
                          "channels": chs
                          }
          logger.debug(f"Created transfer {name} with direction {direction.name}, details:\n{json.dumps(self.transfer, indent=4)}")

     def __Setting_TX_Transfer(self, local_address, local_port, destination_address, destination_port):
          """Configure settings for a transmit (TX) transfer.
          
          Args:
               local_address: Source network address.
               local_port: Source port number.
               destination_address: Target network address.
               destination_port: Target port number.
               
          Returns:
               component_settings: Configured RDMA component settings for TX.
          """
          cs = component_settings("RDMA", [{"key" : "local address", "value" : str(local_address)},
                                            {"key" : "local port", "value" : str(local_port)},
                                            {"key" : "destination address", "value" : str(destination_address)},
                                            {"key" : "destination port", "value" : str(destination_port)}])
          return cs

     def __Setting_RX_Transfer(self, local_address, local_port):
          """Configure settings for a receive (RX) transfer.
          
          Args:
               local_address: Local listening network address.
               local_port: Local listening port number.
               
          Returns:
               component_settings: Configured RDMA component settings for RX.
          """
          cs = component_settings("RDMA", [{"key" : "local address", "value" : str(local_address)},
                                           {"key" : "local port", "value" : str(local_port)}])
          return cs

     def getDict(self):
          """Return the transfer configuration as a dictionary for serialization.
          
          Returns:
               dict: Transfer dictionary containing core settings, component settings, and channels.
          """
          return self.transfer

     def getDictDirection(self):
          """Get the direction of this transfer.
          
          Returns:
               Direction: The direction enum (TX or RX) for this transfer.
          """
          return self.direction

     def addChannel(self, channel):
          """Add a channel to this transfer's channel list.
          
          Args:
               channel: A channel object to append to the transfer.
          """
          self.transfer["channels"].append(channel.getDict())

     def __str__(self):
          """Return a formatted JSON string representation of the transfer.
          
          Returns:
               str: JSON-formatted transfer configuration.
          """
          return json.dumps(self.transfer, indent=4)

class transferGroup:
    """Represents a group of transfers with a common direction.
    
    This class groups multiple transfer objects that share the same direction
    (TX or RX) and manages their configuration including cycle timing and
    component settings.
    """
    
    def __init__(self, name, direction: Direction, transfers):
        """Initialize a transfer group.
        
        Args:
            name (str): The name of the transfer group.
            direction (Direction): The direction enum (TX or RX) for all transfers in this group.
            transfers (list): List of transfer objects to include in this group.
        
        Raises:
            ValueError: If any transfer has a mismatched direction.
        """
        self.direction = direction
        transfer_array = []
        for transfer in transfers:
            if transfer.getDictDirection() != self.direction:
                raise ValueError(f"Transfer group name '{name}' has a transfer with a mismatched direction.")
            else:
                transfer_array.append(transfer.getDict())

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
                                        "component settings" : [component_settings("RDMA").getDict()[0]],
                                        "transfers" : transfer_array
                             }

    def __str__(self):
        """Return a formatted JSON string representation of the transfer group.
        
        Returns:
            str: JSON-formatted transfer group configuration.
        """
        return json.dumps(self.transferGroup, indent=4)

    def getDict(self):
        """Get the dictionary representation of this transfer group.
        
        Returns:
            dict: The transfer group configuration dictionary.
        """
        return self.transferGroup

    def add_transfer(self, transfer):
        """Add a transfer to this group's transfer list.
        
        Args:
            transfer: A transfer object to append to the group.
        
        Raises:
            ValueError: If the transfer has an incompatible direction.
        """
        if transfer.getDictDirection() != self.direction:
            raise ValueError(f"Tramsfer has incompatible direction with transfer group. Transfer direction: {transfer.getDictDirection().name}, Transfer group direction: {self.direction.name}")
        else:
            self.transferGroup["transfers"].append(transfer.getDict())

class thread:
    """Represents a thread configuration for RDMA operations.
    
    This class encapsulates thread settings including core configuration,
    component settings, and associated transfer groups.
    """
    def __init__(self, transferGroups):
        """Initialize a thread with transfer groups.
        
        Args:
            transferGroups: A list of transfer group objects to be assigned to this thread.
        """
        tg_array = []
        for tg in transferGroups:
            tg_array.append(tg.getDict())
        settings = component_settings("RDMA").getDict()
        self.thread = {"core" : {
                                "processor" : -2,
                                "priority offset" : 0
                                },
                        "component settings" : settings,
                        "transfer groups" : tg_array
                        }
                               

    def __str__(self):
        """Return a JSON string representation of this thread.
        
        Returns:
            str: JSON formatted thread configuration.
        """
        return json.dumps(self.thread, indent=4)

    def getDict(self):
        """Get the dictionary representation of this thread.
        
        Returns:
            dict: The thread configuration dictionary.
        """
        return self.thread

    def add_transferGroup(self, transferGroup):
        """Add a transfer group to this thread's transfer groups list.
        
        Args:
            transferGroup: A transfer group object to append to the thread.
        """
        self.thread["transfer groups"].append(transferGroup.getDict())

class plugin:
    """Represents an RDMA plugin configuration with core settings and threads.
    
    This class manages the plugin-level configuration including core settings,
    component settings, and thread definitions.
    """
    
    def __init__(self, name, threads):
        """Initialize a plugin with the given name and threads.
        
        Args:
            name (str): The name of the plugin.
            threads (list): A list of thread objects to include in this plugin.
        """
        thread_array = []
        for th in threads:
            thread_array.append(th.getDict())

        self.plugin = {"core" : {
                                "name" : name,
                                "components" : ["RDMA"],
                                "cycle timing" : {
                                                "priority" : 10000,
                                                "decimation" : 1,
                                                "offset" : 0
                                                },
                                },
                        "component settings" : component_settings("RDMA").getDict(),
                        "threads" : thread_array
                        }
                        
    def add_thread(self, thread):
        """Add a thread to this plugin's thread list.
        
        Args:
            thread: A thread object to append to the plugin.
        """
        self.plugin["threads"].append(thread.getDict())

    def __str__(self):
        """Return a JSON string representation of this plugin.
        
        Returns:
            str: JSON formatted plugin configuration.
        """
        return json.dumps(self.plugin, indent=4)

    def getDict(self):
        """Get the dictionary representation of this plugin.
        
        Returns:
            dict: The plugin configuration dictionary.
        """
        return self.plugin

class RDMA_Configuration:
    """Represent a complete RDMA plugin configuration.

    The configuration contains DSF and configuration version information,
    together with the serialized definitions of the supplied plugins.

    Args:
        plugins: An iterable of plugin objects exposing ``getDict()``.
    """

    def __init__(self, plugins):
        """Initialize a configuration from a collection of plugins."""
        plgs = []
        for plugin in plugins:
            plgs.append(plugin.getDict())
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
        """Return the configuration as an indented JSON string."""
        return json.dumps(self.definition, indent=4)

    def getDict(self):
        """Return the underlying configuration dictionary."""
        return self.definition

    def addPlugin(self, plugin):
        """Append a plugin definition to the configuration.

        Args:
            plugin: A plugin object exposing ``getDict()``.
        """
        self.definition["configuration"]["plugins"].append(plugin.getDict())

def get_version():
    """Return the current RDMA definition format version."""
    return {"major": 1, "minor": 0, "fix": 1, "build": ""}

if __name__ == "__main__":
    """Build a sample RDMA definition and write it to ``output``.

    The example creates two transfers in one transfer group, wraps that
    group in a thread and two plugins, and serializes the resulting
    configuration as JSON for use by other tools.
    """

    # Create the channels used by the primary transfer.
    chs = []

    for i in range(0, 2):
        c = channel(f"channel{i+1}")
        chs.append(c)
  
    # Keep a separate channel for the optional secondary transfer.
    c_jolly = channel("channel_jolly")

    # Define the primary transfer and its network endpoints.
    t = transfer(Direction.TX, "transfer1", chs, "1.2.3.4", 1234, "5.6.7.8", 5678)
    #t.addChannel(c_jolly)

    #logger.info(f"Created transfer: {json.dumps(t.getDict(), indent=4)}")

    # Define a second transfer and add it to the transfer group.
    t_jolly = transfer(Direction.TX, "transfer_jolly", [c_jolly], "9.10.11.12", 9101112, "5.6.7.8", 5678)

    tg = transferGroup("transferGroup1", Direction.TX, [t])
    #logger.info(f"Created transfer group: {json.dumps(tg.getDict(), indent=4)}")

    tg.add_transfer(t_jolly)
    #logger.info(json.dumps(tg.getDict(), indent=4))

    # Assemble the hierarchy: transfer group -> thread -> plugins.
    th = thread([tg])
    #logger.info(f"Created thread: {json.dumps(th.getDict(), indent=4)}")

    # Build the top-level configuration from both plugin definitions.
    pl1 = plugin("plugin1", [th])
    #logger.info(f"Created plugin: {json.dumps(pl1.getDict(), indent=4)}")

    pl2 = plugin("plugin2", [th])
    rdma_def = RDMA_Configuration([pl1, pl2])
    #rdma_def.addPlugin(pl2)

    #logger.info(f"Created RDMA definitions: {json.dumps(rdma_def.getDict(), indent=4)}")

    # Ensure the destination exists before writing the generated JSON.
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Serialize the configuration in a human-readable format.
    with open(output_dir / "rdma_definitions.json", "w") as f:
        json.dump(rdma_def.getDict(), f, indent=4)