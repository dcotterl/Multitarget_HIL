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

    def importFromDict(self, dict):
        """Import the key-value pair from a dictionary."""
        self.key = dict.get("key")
        self.value = dict.get("value")

class component_settings:
    """Store component-specific settings for an object."""

    def __init__(self, component = "", initial_elements:list[element] = []):
        """Create settings for ``component`` with optional initial values."""
        self.component = component
        self.elements = initial_elements

    def __str__(self):
         """Return the settings as formatted JSON."""
         return json.dumps(self.getDict(), indent=4)

    def getDict(self):
            """Return the component settings dictionary."""
            return {"component": self.component, "values": [v.getDict() for v in self.elements]}

    def importFromDict(self, dict):
            """Import the component settings from a dictionary."""
            self.component = dict.get("component", "")
            self.elements = [element(v.get("key"), v.get("value")) for v in dict.get("values", [])]

    def getComponent(self):
         """Return the component name for these settings."""
         return self.component
    def setComponent(self, component):
         """Set the component name for these settings."""
         self.component = component

    def getElements(self):
         """Return the list of key-value pairs for these settings."""
         return self.elements  
    def setElements(self, elements:list[element]):
         """Set the elements for these settings."""
         self.elements = elements

    def addElement(self, key, value):
         """Add a key-value pair to the settings."""
         e = element(key, value)
         self.elements.append(e)

class channel:
     """Represent an RDMA channel definition and its serialized settings."""

     def __init__(self,
                  name="", 
                  unit = "",
                  engine_data_type = 2, 
                  string_data_type = 2, 
                  string_offset = 0,
                  protocol = "",):
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
            self.component_settings = [component_settings(protocol)]

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

     def importFromDict(self, dict):
            """Import the channel definition from a dictionary."""
            core = dict.get("core", {})
            self.name = core.get("name", "")
            self.unit = core.get("units", "")
            self.engine_data_type = core.get("engine data type", 2)
            self.string_data_type = core.get("string data type", 2)
            self.string_offset = core.get("string offset", 0)
            self.component_settings = []
            for cs in dict.get("component settings", []):
                 csapp = component_settings()
                 csapp.importFromDict(cs)
                 self.component_settings.append(csapp)

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
     def __init__(self, 
                  direction: Direction = Direction.TX, 
                  protocol="",
                  name="", 
                  channels:list[channel]=[], 
                  local_address="", 
                  local_port=0, 
                  destination_address="", 
                  destination_port=0):
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
               self.component_settings[0].addElement("destination address",str(destination_address))
               self.component_settings[0].addElement("destination port", str(destination_port))
    
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

     def importFromDict(self, dict):
        """Import the transfer configuration from a dictionary."""
        core = dict.get("core", {})
        self.name = core.get("name", "")
        self.component_settings = []
        for cs in dict.get("component settings", []):
            csapp = component_settings()
            csapp.importFromDict(cs)
            self.component_settings.append(csapp)
        self.channels = []
        for ch in dict.get("channels", []):
            chapp = channel()
            chapp.importFromDict(ch)
            self.channels.append(chapp)
        elements = self.component_settings[0].getElements()
        if "destination address" in [e.getKey() for e in elements]:
            self.direction = Direction.TX
        else:
            self.direction = Direction.RX


     def getDirection(self):
        """Return the transfer direction."""
        return self.direction
     def setDirection(self, direction):
        """Set the transfer direction."""
        self.direction = direction

     def getName(self):
        """Return the transfer name."""
        return self.name
     def setName(self, name):
        """Set the transfer name."""
        self.name = name

     def getChannels(self):
        """Return the channels assigned to the transfer."""
        return self.channels
     def setChannels(self, channels):
        """Set the channels assigned to the transfer."""
        self.channels = channels
     def addChannel(self, channel:channel):
        """Add a channel to the transfer's channel list."""
        self.channels.append(channel)

     def getComponentSettings(self):
        """Return the transfer component settings."""
        return self.component_settings
     def setComponentSettings(self, component_settings):
        """Set the transfer component settings."""
        self.component_settings = component_settings
     def addElement (self, key, value):
        """Add a key-value pair to the transfer's component settings."""
        if self.component_settings:
            self.component_settings[0].elements.append(element(key, value))
        else:
            logger.warning("No component settings available to add element.")
     def addComponentSetting(self, component_setting:component_settings):
        """Add a component setting to the transfer's component settings list."""
        self.component_settings.append(component_setting)

     def __str__(self):
          """Return a formatted JSON string representation of the transfer.
          
          Returns:
               str: JSON-formatted transfer configuration.
          """
          dict = self.getDict()
          dict["channels"] = "[EMPTY]" if not self.channels else f"[...{len(self.channels)} channels...]"
          return json.dumps(dict, indent=4)

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
            name: Human-readable name for the transfer group.
            direction: Transfer direction for all grouped transfers, typically
                Direction.TX or Direction.RX.
            priority: Scheduling priority used in the group cycle timing.
            decimation: Sample decimation factor for the group.
            offset: Time offset for the group cycle timing.
            timeout_behaviour: Timeout handling behavior configuration.
            enable_conversion: Whether data conversion is enabled.
            protocol: Protocol name used for initial component settings.
            transfers: List of transfer instances assigned to the group.
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
        dict = self.getDict()
        dict["transfers"] = "[EMPTY]" if not self.transfers else f"[...{len(self.transfers)} transfers...]"
        return json.dumps(dict, indent=4)

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

    def importFromDict(self, dict):
        """Import the transfer group configuration from a dictionary."""
        core = dict.get("core", {})
        self.name = core.get("name", "")
        self.direction = Direction(core.get("direction", 0))
        cycle_timing = core.get("cycle timing", {})
        self.priority = cycle_timing.get("priority", 100)
        self.decimation = cycle_timing.get("decimation", 1)
        self.offset = cycle_timing.get("offset", 0)
        self.timeout_behaviour = core.get("timeout behavior", 0)
        self.enable_conversion = core.get("enable conversion", False)

        self.component_settings = []
        for cs in dict.get("component settings", []):
            csapp = component_settings()
            csapp.importFromDict(cs)
            self.component_settings.append(csapp)

        self.transfers = []
        for t in dict.get("transfers", []):
            tapp = transfer()
            tapp.importFromDict(t)
            self.transfers.append(tapp)

    def getName(self):
        """Return the transfer group name."""
        return self.name
    def setName(self, name):
        """Set the transfer group name.

        Args:
            name: New name for the transfer group.
        """
        self.name = name

    def getDirection(self):
        """Return the transfer group direction."""
        return self.direction
    def setDirection(self, direction):
        """Set the transfer group direction.

        Args:
            direction: Direction enum value for the group.
        """
        self.direction = direction

    def getPriority(self):
        """Return the transfer group priority."""
        return self.priority
    def setPriority(self, priority):
        """Set the transfer group priority."""
        self.priority = priority

    def getDecimation(self):
        """Return the transfer group decimation."""
        return self.decimation
    def setDecimation(self, decimation):
        """Set the transfer group decimation."""
        self.decimation = decimation

    def getOffset(self):
        """Return the transfer group offset."""
        return self.offset
    def setOffset(self, offset):
        """Set the transfer group offset."""
        self.offset = offset

    def getTimeoutBehaviour(self):
        """Return the transfer group timeout behavior."""
        return self.timeout_behaviour
    def setTimeoutBehaviour(self, timeout_behaviour):
        """Set the transfer group timeout behavior."""
        self.timeout_behaviour = timeout_behaviour

    def getEnableConversion(self):
        """Return whether conversion is enabled for the group."""
        return self.enable_conversion
    def setEnableConversion(self, enable_conversion:bool):
        """Set whether conversion is enabled for the group."""
        self.enable_conversion = enable_conversion

    def getComponentSettings(self):
        """Return the transfer group component settings."""
        return self.component_settings
    def setComponentSettings(self, component_settings:component_settings):
        """Set the transfer group component settings."""
        self.component_settings = component_settings

    def getTransfers(self):
        """Return the transfers in the group."""
        return self.transfers
    def setTransfers(self, transfers:list[transfer]):
        """Set the transfers in the group."""
        self.transfers = transfers
    def addTransfer(self, transfer:transfer):
        """Add a transfer to the group."""
        self.transfers.append(transfer)

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
        dict = self.getDict()
        dict["transfer groups"] = "[EMPTY]" if not self.transfer_groups else f"[...{len(self.transfer_groups)} transfer groups...]"
        return json.dumps(dict, indent=4)

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
    def importFromDict(self, dict):
        """Import the thread configuration from a dictionary."""
        core = dict.get("core", {})
        self.processor = core.get("processor", -2)
        self.priority_offset = core.get("priority offset", 0)

        self.component_settings = []
        for cs in dict.get("component settings", []):
            csapp = component_settings()
            csapp.importFromDict(cs)
            self.component_settings.append(csapp)

        self.transfer_groups = []
        for tg in dict.get("transfer groups", []):
            tgapp = transferGroup()
            tgapp.importFromDict(tg)
            self.transfer_groups.append(tgapp)

    def getProcessor(self):
        """Return the processor assigned to the thread."""
        return self.processor
    def setProcessor(self, processor):
        """Set the processor assigned to the thread."""
        self.processor = processor

    def getPriorityOffset(self):
        """Return the thread priority offset."""
        return self.priority_offset
    def setPriorityOffset(self, priority_offset):
        """Set the thread priority offset."""
        self.priority_offset = priority_offset

    def getComponentSettings(self):
        """Return the thread component settings."""
        return self.component_settings
    def setComponentSettings(self, component_settings:list[component_settings]):
        """Set the thread component settings."""
        self.component_settings = component_settings

    def getTransferGroups(self):
        """Return the transfer groups assigned to the thread."""
        return self.transfer_groups
    def setTransferGroups(self, transfer_groups:list[transferGroup]):
        """Set the transfer groups assigned to the thread."""
        self.transfer_groups = transfer_groups
    def addTransferGroup(self, transfer_group:transferGroup):
        """Add a transfer group to the thread's list of transfer groups."""
        self.transfer_groups.append(transfer_group)

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
        dict = self.getDict()
        dict["threads"] = "[EMPTY]" if not self.threads else f"[...{len(self.threads)} threads...]"
        return json.dumps(dict, indent=4)

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
    def importFromDict(self, dict):
        core = dict.get("core", {})
        self.name = core.get("name", "")
        self.components = core.get("components", [])
        cycle_timing = core.get("cycle timing", {})
        self.priority = cycle_timing.get("priority", 10000)
        self.decimation = cycle_timing.get("decimation", 1)
        self.offset = cycle_timing.get("offset", 0)

        self.component_settings = []
        for cs in dict.get("component settings", []):
            csapp = component_settings()
            csapp.importFromDict(cs)
            self.component_settings.append(csapp)

        self.threads = []
        for th in dict.get("threads", []):
            thapp = thread()
            thapp.importFromDict(th)
            self.threads.append(thapp)

    def getName(self):
        """Return the plugin name."""
        return self.name
    def setName(self, name):
        """Set the plugin name."""
        self.name = name

    def getComponents(self):
        """Return the plugin component names."""
        return self.components
    def setComponents(self, components):
        """Set the plugin component names."""
        self.components = components

    def getPriority(self):
        """Return the plugin priority."""
        return self.priority
    def setPriority(self, priority):
        """Set the plugin priority."""
        self.priority = priority

    def getDecimation(self):
        """Return the plugin decimation."""
        return self.decimation
    def setDecimation(self, decimation):
        """Set the plugin decimation."""
        self.decimation = decimation

    def getOffset(self):
        """Return the plugin offset."""
        return self.offset
    def setOffset(self, offset):
        """Set the plugin offset."""
        self.offset = offset

    def getThreads(self):
        """Return the threads assigned to the plugin."""
        return self.threads
    def setThreads(self, threads):
        """Set the threads assigned to the plugin."""
        self.threads = threads
    def addThread(self, thread:thread):
        """Add a thread to the plugin's list of threads."""
        self.threads.append(thread)

    def getComponentSettings(self):
        """Return the plugin component settings."""
        return self.component_settings
    def setComponentSettings(self, component_settings):
        """Set the plugin component settings."""
        self.component_settings = component_settings

class RDMA_Configuration:

    def __init__(self, 
                 plugins:list[plugin] = [],
                 dsfversion ={"major": 1,"minor": 4,"fix": 0,"build": ""},
                 version = {"major": 1, "minor": 0, "fix": 0,"build": ""}):
         """Initialize the RDMA Configuration.
         
         Args:
             plugins: List of plugin objects. Defaults to empty list.
             dsfversion: Dictionary containing DSF format version metadata with keys
                        'major', 'minor', 'fix', and 'build'. Defaults to version 1.4.0.
             version: Dictionary containing RDMA specification version metadata with keys
                     'major', 'minor', 'fix', and 'build'. Defaults to version 1.0.0.
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
    def importFromDict(self, dict):
        """Import the RDMA configuration from a dictionary.

        This method populates the RDMA_Configuration instance with data from
        the provided dictionary, including DSF version, RDMA version, and
        plugin definitions.
        """
        self.dsfversion = dict.get("dsfversion", {"major": 1,"minor": 4,"fix": 0,"build": ""})
        self.version = dict.get("version", {"major": 1, "minor": 0, "fix": 0,"build": ""})
        configuration = dict.get("configuration", {})
        self.plugins = []
        for pl in configuration.get("plugins", []):
            plapp = plugin()
            plapp.importFromDict(pl)
            self.plugins.append(plapp)

    def getDsfVersion(self):
            """Return the DSF format version metadata."""
            return self.dsfversion
    def setDsfVersion(self, dsfversion):
            """Set the DSF format version metadata."""
            self.dsfversion = dsfversion

    def getVersion(self):
            """Return the RDMA specification version metadata."""
            return self.version
    def setVersion(self, version):
            """Set the RDMA specification version metadata."""
            self.version = version

    def getPlugins(self):
            """Return the plugins in the configuration."""
            return self.plugins
    def setPlugins(self, plugins):
            """Set the plugins in the configuration."""
            self.plugins = plugins
    def addPlugin(self, plugin:plugin):
        """Add a plugin to the configuration."""
        self.plugins.append(plugin)

    def __str__(self):
        """Return the configuration as an indented JSON string."""
        dict = self.getDict()
        dict["configuration"]["plugins"] = "[EMPTY]" if not self.plugins else f"[...{len(self.plugins)} plugins...]"
        return json.dumps(dict, indent=4)
    
def get_version():
    """Return the current RDMA definition format version."""
    return {"major": 2, "minor": 0, "fix": 0, "build": ""}

if __name__ == "__main__":
    print(f"RDMA definition format version: {get_version()}")