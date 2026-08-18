"""RDMA definition model and JSON serializer.

This module provides lightweight classes for constructing an RDMA
configuration in the same hierarchy used by the serialized definition:

# Hierarchy of templates:
#    config file
#        plugin [1..n]
#            thread [1..n]
#                transfer group [1..n]
#                    transfer [1..n]
#                        channel [1..n]

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

class element:
    def __init__(self, key, value):
        """Create a key-value pair for component settings."""
        self.key = key
        self.value = value

    def getKey(self):
        """Return the key for this value."""
        return self.key

    def getValue(self):
        """Return the value for this key-value pair."""
        return self.value

    def setKey(self, key):
        """Set the key for this value."""
        self.key = key

    def setValue(self, value):
        """Set the value for this key-value pair."""
        self.value = value

    def getDict(self):
        """Return the key-value pair as a dictionary."""
        return {"key": self.key, "value": self.value}

    def __str__(self):
        """Return the key-value pair as a formatted JSON string."""
        return json.dumps(self.getDict(), indent=4) 

class component_settings:
    """Store component-specific settings for an object."""

    def __init__(self, component = "", initial_values:list[element] = []):
        """Create settings for ``component`` with optional initial values."""
        self.component = component
        self.values = initial_values

    def __str__(self):
         """Return the settings as formatted JSON."""
         return json.dumps(self.getDict(), indent=4)

    def getDict(self):
            """Return the component settings dictionary."""
            return {"component": self.component, "values": [v.getDict() for v in self.values]}

    def getComponent(self):
         """Return the component name for these settings."""
         return self.component

    def setComponent(self, component):
         """Set the component name for these settings."""
         self.component = component

    def getValues(self):
         """Return the list of key-value pairs for these settings."""
         return self.values
    
    def setValues(self, values):
         """Set the values for these settings."""
         self.values = values

    def addElement(self, key, value):
         """Add a key-value pair to the settings."""
         e = element(key, value)
         self.values.append(e)

class channel:
     """Represent an RDMA channel definition and its serialized settings."""

     def __init__(self, component_settings:list[component_settings],
                  name="", 
                  unit = "",
                  engine_data_type = 2, 
                  string_data_type = 2, 
                  string_offset = 0):
            """Initialize a channel.

            Args:
                name: Channel name.
                unit: Engineering unit string for the channel.
                engine_data_type: Numeric engine-side data type identifier.
                string_data_type: Numeric string-side data type identifier.
                string_offset: String table offset for this channel.
            """

            self.name = name
            self.unit = unit
            self.engine_data_type = engine_data_type
            self.string_data_type = string_data_type
            self.string_offset = string_offset
            self.component_settings = component_settings

            # logger.debug(f"Creating channel {name} with unit {unit}, engine_data_type {engine_data_type}, string_data_type {string_data_type}, string_offset {string_offset}")

     def __str__(self):
          """Return a formatted JSON string representation of the channel."""
          return json.dumps(self.getDict(), indent=4)

     def getDict(self):
          """Return the channel as a dictionary for serialization or composition."""
          dict = {"core":{
                                "name": self.name,
                                "units": self.unit,
                                "engine data type": self.engine_data_type,
                                "string data type": self.string_data_type,
                                "string offset": self.string_offset,
                                },
                                "component settings": [cs.getDict() for cs in self.component_settings]}
          return dict

     def getName(self):
            """Return the channel name."""
            return self.name
     def setName(self, name):
            """Set the channel name."""
            self.name = name    
     def getUnit(self):
            """Return the channel's engineering unit string."""
            return self.unit
     def setUnit(self, unit):
            """Set the channel's engineering unit string."""
            self.unit = unit
     def getEngineDataType(self):
            """Return the channel's engine-side data type identifier."""
            return self.engine_data_type
     def setEngineDataType(self, engine_data_type):
            """Set the channel's engine-side data type identifier."""
            self.engine_data_type = engine_data_type
     def getStringDataType(self):
            """Return the channel's string-side data type identifier."""
            return self.string_data_type
     def setStringDataType(self, string_data_type):
            """Set the channel's string-side data type identifier."""
            self.string_data_type = string_data_type
     def getStringOffset(self):
            """Return the channel's string table offset."""
            return self.string_offset
     def setStringOffset(self, string_offset):
            """Set the channel's string table offset."""
            self.string_offset = string_offset
     def getComponentSettings(self):
            """Return the list of component settings for this channel."""
            return self.component_settings
     def setComponentSettings(self, component_settings:list[component_settings]):
            """Set the list of component settings for this channel."""
            self.component_settings = component_settings
     def addComponentSetting(self, component_setting:component_settings):
            """Add a component setting to this channel's list."""
            self.component_settings.append(component_setting)

class transfer:
     """Represents an RDMA data transfer configuration with direction-specific settings.
     
     Manages TX (transmit) or RX (receive) transfers with associated channels and network parameters.
     """
     def __init__(self, direction: Direction, protocol, name="", channels:list[channel]=[], local_address="", local_port=0, destination_address="", destination_port=0):
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

          self.direction = direction
          self.name = name
          self.channels = channels
          elements = [element("local address",str(local_address)),
                    element("local port", str(local_port))]
          self.component_settings = [component_settings(protocol,elements)]
          if self.direction == Direction.TX:
               self.component_settings[0].addElement("destination address",destination_address)
               self.component_settings[0].addElement("destination port", destination_port)
    
     def getDict(self):
          """Return the transfer configuration as a dictionary for serialization.
          
          Returns:
               dict: Transfer dictionary containing core settings, component settings, and channels.
          """

          dict = {
                    "core": {"name" : self.name},
                    "component settings": [cs.getDict() for cs in self.component_settings],
                    "channels": [ch.getDict() for ch in self.channels]
                 }

          return dict

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
    
    def __init__(self, name = "", 
                 direction: Direction = Direction.TX,
                 priority = 100, 
                 decimation = 1, 
                 offset = 0, 
                 timeout_behaviour = 0,
                 enable_conversion:bool = False,
                 protocol = "",
                 transfers:list[transfer]=[]):
        """Initialize a transfer group.
        
        Args:
            name (str): The name of the transfer group.
            direction (Direction): The direction enum (TX or RX) for all transfers in this group.
            transfers (list): List of transfer objects to include in this group.
        
        Raises:
            ValueError: If any transfer has a mismatched direction.
        """
        self.name = name
        self.direction = direction
        self.priority = priority
        self.decimation = decimation
        self.offset = offset
        self.timeout_behaviour = timeout_behaviour
        self.enable_conversion = enable_conversion
        self.component_settings = [component_settings(protocol)]
        self.transfers = transfers

    def __str__(self):
        """Return a formatted JSON string representation of the transfer group.
        
        Returns:
            str: JSON-formatted transfer group configuration.
        """
        return json.dumps(self.transferGroup.getDict(), indent=4)

    def getDict(self):
        """Get the dictionary representation of this transfer group.
        
        Returns:
            dict: The transfer group configuration dictionary.
        """
        dict = {"core" : {
                          "name" : self.name,
                          "direction" : self.direction.value,
                          "cycle timing" : {
                                            "priority" : self.priority,
                                            "decimation" : self.decimation,
                                            "offset" : self.offset
                                          },
                          "timeout behavior" : self.timeout_behaviour,
                          "enable conversion" : self.enable_conversion,
                    },
                "component settings" : [cs.getDict() for cs in self.component_settings],
                "transfers" : [t.getDict() for t in self.transfers]
                }
        
        return dict

    def add_transfer(self, transfer):
        """Add a transfer to this group's transfer list.
        
        Args:
            transfer: A transfer object to append to the group.
        
        Raises:
            ValueError: If the transfer has an incompatible direction.
        """
        pass

class thread:
    """Represents a thread configuration for RDMA operations.
    
    This class encapsulates thread settings including core configuration,
    component settings, and associated transfer groups.
    """
    def __init__(self,
                 processor = -2,
                 priority_offset = 0, 
                 protocol = "", 
                 transfer_groups:list[transferGroup]=[]):
       self.processor = processor
       self.priority_offset = priority_offset
       self.component_settings = [component_settings(protocol)]
       self.transfer_groups = transfer_groups
                               
    def __str__(self):
        """Return a JSON string representation of this thread.
        
        Returns:
            str: JSON formatted thread configuration.
        """
        return json.dumps(self.thread.getDict(), indent=4)

    def getDict(self):
        """Get the dictionary representation of this thread.
        
        Returns:
            dict: The thread configuration dictionary.
        """
        dict = {"core" : {
                                        "processor" : self.processor,
                                        "priority offset" : self.priority_offset
                                        },
                                "component settings" : [cs.getDict() for cs in self.component_settings],
                                "transfer groups" : [tg.getDict() for tg in self.transfer_groups]
                                }
        return dict

class plugin:
    def __init__(self, 
                 name = "",
                 protocol = "",
                 priority = 10000,
                 decimation = 1,
                 offset = 0,
                 threads:list[thread] = []):
     self.name = name
     self.components = [protocol]
     self.priority = priority
     self.decimation = decimation
     self.offset = offset
     self.threads = threads
     self.component_settings = [component_settings(protocol)]
     
    def __str__(self):
        return json.dumps(self.plugin.getDict(), indent=4)

    def getDict(self):
        self.plugin = {"core" : {
                                "name" : self.name,
                                "components" : self.components,
                                "cycle timing" : {
                                                "priority" : self.priority,
                                                "decimation" : self.decimation,
                                                "offset" : self.offset
                                                },
                                },
                        "component settings" : [cs.getDict() for cs in self.component_settings],
                        "threads" : [th.getDict() for th in self.threads]
                      }
        return self.plugin

class RDMA_Configuration:

    def __init__(self, 
                 plugins:list[plugin] = [],
                 dsfversion ={"major": 1,"minor": 4,"fix": 0,"build": ""},
                 version = {"major": 1, "minor": 0, "fix": 0,"build": ""}):
         """Initialize an RDMA configuration object.

         Args:
             plugins (list[plugin], optional): The plugins to include in the
                 configuration. Defaults to an empty list.
             dsfversion (dict, optional): The DSF format version metadata for the
                 configuration. Defaults to {"major": 1, "minor": 4, "fix": 0,
                 "build": ""}.
             version (dict, optional): The RDMA specification version metadata.
                 Defaults to {"major": 1, "minor": 0, "fix": 0, "build": ""}.
         """
         self.dsfversion = dsfversion
         self.version = version
         self.plugins = plugins

    def getDict(self):
         """Return the RDMA configuration as a dictionary suitable for JSON export.

         The dictionary includes the DSF format version, the RDMA specification
         version, and the serialized plugin definitions contained in this
         configuration.
         """
         dict = {
                "dsfversion": self.dsfversion,
                "version": self.version,
                "configuration": {
                                 "plugins": [pl.getDict() for pl in self.plugins] 
                                 }
                }
         return dict

    def __str__(self):
        """Return the configuration as an indented JSON string."""
        return json.dumps(self.getDict(), indent=4)

def get_version():
    """Return the current RDMA definition format version."""
    return {"major": 2, "minor": 0, "fix": 0, "build": ""}

if __name__ == "__main__":
    print(f"RDMA definition format version: {get_version()}")