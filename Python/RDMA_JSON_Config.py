"""
RDMA JSON Configuration Module

This module provides configuration management for RDMA (Remote Direct Memory Access)
devices using JSON-based templates and structures. It defines the base configuration
template for RDMA plugins, transfer groups, and data channels.

Key Components:
    - Direction: Enum for transfer direction (TX/RX)
    - RDMA_JSON_Template: Base JSON template for RDMA configuration with plugin,
      thread, transfer group, and channel settings
"""

from copy import deepcopy
import json
from enum import Enum
import os
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

class Direction(Enum):
	TX = 0
	RX = 1

RDMA_JSON_Template = {
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
		"plugins": [
			{
				"core": {
					"name": "Plugin",
					"components": ["RDMA"],
					"cycle timing": {
						"priority": 10000,
						"decimation": 1,
						"offset": 0,
					},
				},
				"component settings": [],
				"threads": [
					{
						"core": {
							"processor": -2,
							"priority offset": 0,
						},
						"component settings": [],
						"transfer groups": [
							{
								"core": {
									"name": "GroupTX",
									"direction": 0,
									"cycle timing": {
										"priority": 100,
										"decimation": 1,
										"offset": 0,
									},
									"timeout behavior": 0,
									"enable conversion": False,
								},
								"component settings": [],
								"transfers": [
									{
										"core": {
											"name": "TransferTx",
										},
										"component settings": [
											{
												"component": "RDMA",
												"values": [
													{
														"key": "local address",
														"value": "",
													},
													{
														"key": "local port",
														"value": "",
													},
													{
														"key": "destination address",
														"value": "",
													},
													{
														"key": "destination port",
														"value": "",
													},
												],
											}
										],
										"channels": [
											{
												"core": {
													"name": "",
													"units": "",
													"engine data type": 2,
													"string data type": 2,
													"string offset": 0,
												},
												"component settings": [],
											}
										],
									}
								],
							},
							{
								"core": {
									"name": "GroupRx",
									"direction": 1,
									"cycle timing": {
										"priority": 100,
										"decimation": 1,
										"offset": 0,
									},
									"timeout behavior": 0,
									"enable conversion": False,
								},
								"component settings": [],
								"transfers": [
									{
										"core": {
											"name": "TransferRx",
										},
										"component settings": [
											{
												"component": "RDMA",
												"values": [
													{
														"key": "local address",
														"value": "",
													},
													{
														"key": "local port",
														"value": "",
													},
												],
											}
										],
										"channels": [
											{
												"core": {
													"name": "",
													"units": "",
													"engine data type": 2,
													"string data type": 2,
													"string offset": 0,
												},
												"component settings": [],
											}
										],
									}
								],
							},
						],
					}
				],
			}
		]
	},
}

Base_File_Specification_Template = {
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
            "plugins": []
        }
    }

Pluging_Specification_Template = {
                "core": {
                    "name": "Plugin",
                    "components": ["RDMA"],
                    "cycle timing": {
                        "priority": 10000,
                        "decimation": 1,
                        "offset": 0,
                    },
                },
                "component settings": [
										{
											"component": "RDMA",
											"values": []
										}
				],
                "threads": [],
            }

Thread_Specification_Template = {
                        "core": {
                            "processor": -2,
                            "priority offset": 0,
                        },
                        "component settings": [
                            					{
													"component": "RDMA",
													"values": []
												}
						],
                        "transfer groups": [],
                    }

Transfer_Group_Specification_Template = {
                                "core": {
                                    "name": "",
                                    "direction": 0, # 0=Tx, 1=Rx
                                    "cycle timing": {
                                        "priority": 100,
                                        "decimation": 1,
                                        "offset": 0,
                                    },
                                    "timeout behavior": 0,
                                    "enable conversion": False,
                                },
                                "component settings": [
														{
															"component": "RDMA",
															"values": []
														}],
                                "transfers": [],
                            }

Tx_Transfer_Specification_Template = {
                                        "core": {
                                            "name": "",
                                        },
                                        "component settings": [
                                            {
                                                "component": "RDMA",
                                                "values": [
													{
                                                        "key": "local address",
                                                        "value": "",
                                                    },
                                                    {
                                                        "key": "local port",
                                                        "value": "",
                                                    },
                                                    {
                                                        "key": "destination address",
                                                        "value": "",
                                                    },
                                                    {
                                                        "key": "destination port",
                                                        "value": "",
                                                    },
                                                ],
                                            }
                                        ],
                                        "channels": []
                                    }

Rx_Transfer_Specification_Template = {
                                        "core": {
                                            "name": "",
                                        },
                                        "component settings": [
                                            {
                                                "component": "RDMA",
                                                "values": [
                                                    {
                                                        "key": "local address",
                                                        "value": "",
                                                    },
                                                    {
                                                        "key": "local port",
                                                        "value": "",
                                                    },
                                                ],
                                            }
                                        ],
                                        "channels": []
                                    }

Channel_Specification_Template = {
                                    "core": {
                                        "name": "",
                                        "units": "",
                                        "engine data type": 2,
                                        "string data type": 2,
                                        "string offset": 0,
                                    },
                                    "component settings": [
                                        			{
														"component": "RDMA",
														"values": []
													}],
                                }

def get_rdma_json():
	"""Return a deep-copied template so callers can safely modify it."""
	logger.debug("Returning a deep copy of the RDMA JSON template.")
	return deepcopy(RDMA_JSON_Template)

def get_base_file():
    """Return a deep-copied template so callers can safely modify it."""
    logger.debug("Returning a deep copy of the base file specification template.")
    return deepcopy(Base_File_Specification_Template)

def get_plugin():
    """Return a deep-copied template so callers can safely modify it."""
    logger.debug("Returning a deep copy of the plugin specification template.")
    return deepcopy(Pluging_Specification_Template)

def get_thread():
    """Return a deep-copied template so callers can safely modify it."""
    logger.debug("Returning a deep copy of the thread specification template.")
    return deepcopy(Thread_Specification_Template)

def get_transfergroup():
    """Return a deep-copied template so callers can safely modify it."""
    logger.debug("Returning a deep copy of the transfer group specification template.")
    return deepcopy(Transfer_Group_Specification_Template)

def get_tx_transfer():
    """Return a deep-copied template so callers can safely modify it."""
    logger.debug("Returning a deep copy of the TX transfer specification template.")
    return deepcopy(Tx_Transfer_Specification_Template)

def get_rx_transfer():
    """Return a deep-copied template so callers can safely modify it."""
    logging.debug("Returning a deep copy of the RX transfer specification template.")
    return deepcopy(Rx_Transfer_Specification_Template)

def get_channel():
    """Return a deep-copied template so callers can safely modify it."""
    logging.debug("Returning a deep copy of the channel specification template.")
    return deepcopy(Channel_Specification_Template)

# Hierarchy of templates:
#    config file
#        plugin [1..n]
#            thread [1..n]
#                transfer group [1..n]
#                    transfer [1..n]
#                        channel [1..n]

def makeChannels(nCh):
	"""Create a list of channel specifications.
	
	Args:
		nCh (int): Number of channels to create.
	
	Returns:
		list: A list of channel specification dictionaries, each with a unique name.
	"""
	# Building n channels
	channels = []
	for i in range(nCh):
		channel = get_channel()
		channel["core"]["name"] = f"Channel{i+1}"
		channel["core"]["units"] = ""
		channels.append(channel)
		logger.debug(f"Created channel specification: {channel['core']['name']} with units:{channel['core']['units']}")
	return channels

def makeTransfers(direction:Direction, localIP, localPort, channels, destIP=None, destPort=None):
	"""Create a transfer specification with the given parameters.
	
	Args:
		direction (Direction): Transfer direction (TX or RX).
		localIP (str): Local IP address for the transfer.
		localPort (int): Local port number for the transfer.
		channels (list): List of channel specifications for the transfer.
		destIP (str, optional): Destination IP address. Required for TX transfers. Defaults to None.
		destPort (int, optional): Destination port number. Required for TX transfers. Defaults to None.
	
	Returns:
		dict: A transfer specification dictionary configured for the given direction.
	"""
	if direction == Direction.TX:
		transfer = get_tx_transfer()
		transfer["core"]["name"] = "TransferTx"
		transfer["channels"] = channels
		transfer["component settings"][0]["values"][0]["value"] = localIP
		transfer["component settings"][0]["values"][1]["value"] = localPort
		transfer["component settings"][0]["values"][2]["value"] = destIP
		transfer["component settings"][0]["values"][3]["value"] = destPort
		logger.debug(f"Created TX transfer specification: {transfer['core']['name']} with localIP:{localIP}, localPort:{localPort}, destIP:{destIP}, destPort:{destPort}")
	elif direction == Direction.RX:
		transfer = get_rx_transfer()
		transfer["core"]["name"] = "TransferRx"
		transfer["channels"] = channels
		transfer["component settings"][0]["values"][0]["value"] = localIP
		transfer["component settings"][0]["values"][1]["value"] = localPort
		logger.debug(f"Created RX transfer specification: {transfer['core']['name']} with localIP:{localIP}, localPort:{localPort}")
	return transfer

def makeTransferGroups(direction:Direction, transfers, groupName="Group"):
	"""
	Creates a transfer group specification with the given configuration.
	
	Args:
		direction (Direction): The direction of the transfer group (TX or RX).
		transfers (list): List of transfer specifications to include in the group.
		groupName (str, optional): Base name for the group. "Tx" or "Rx" suffix is appended based on direction. Defaults to "Group".
	
	Returns:
		dict: A transfer group specification dictionary configured for the given direction.
	"""
	group = get_transfergroup()
	if direction == Direction.TX:
		group["core"]["name"] = groupName + "Tx"
	elif direction == Direction.RX:
		group["core"]["name"] = groupName + "Rx"

	group["core"]["direction"] = direction.value
	group["transfers"] = transfers
	logger.debug(f"Created transfer group specification: {group['core']['name']} with direction:{direction.name} and {len(transfers)} transfers.")
	return group

def makeThreads(groups):
	"""
	Creates a thread specification with the given transfer groups.
	
	Args:
		groups (list): List of transfer group specifications to include in the thread.
	
	Returns:
		dict: A thread specification dictionary configured with the provided transfer groups.
	"""
	thread = get_thread()
	thread["transfer groups"] = groups
	logger.debug(f"Created thread specification with {len(groups)} transfer groups.")
	return thread

def makePlugins(threads, name="Plugin"):
	"""
	Creates a plugin specification with the given threads.
	
	Args:
		threads (list): List of thread specifications to include in the plugin.
		name (str, optional): Name for the plugin. Defaults to "Plugin".
	
	Returns:
		dict: A plugin specification dictionary configured with the provided threads and name.
	"""
	plugin = get_plugin()
	plugin["core"]["name"] = name
	plugin["threads"] = threads
	logger.debug(f"Created plugin specification: {plugin['core']['name']} with {len(threads)} threads.")
	return plugin

def makeConfigFile(plugins):
	"""
	Creates a configuration file with the given plugins.
	
	Args:
		plugins (list): List of plugin specifications to include in the configuration.
	
	Returns:
		dict: A configuration file dictionary with the provided plugins.
	"""
	configFile = get_base_file()
	configFile["configuration"]["plugins"] = plugins
	logger.debug(f"Created configuration file with {len(plugins)} plugins.")
	return configFile

if __name__ == "__main__":
	
	# Building channels
	channels = makeChannels(2)
	
	# Building transfers
	transfer_tx = makeTransfers(Direction.TX, "169.254.49.44", 5000, channels, "169.254.23.111", 5001)
	transfer_rx = makeTransfers(Direction.RX, "169.254.23.111", 5001, channels)
	transfers = [transfer_tx]

	# Building Transfer Groups
	group_tx = makeTransferGroups(Direction.TX, transfers, "Group")
	groups = [group_tx]

	# Building threads
	thread = makeThreads(groups)
	threads = [thread]

	# Building plugins
	plugin = makePlugins(threads, "Plugin")
	plugins = [plugin]

	# Building config file
	configFile = makeConfigFile(plugins)

	# print JSON to console
	logger.debug(json.dumps(configFile, indent=4))

	# save the config file to the output folder
	output_folder = "output"
	os.makedirs(output_folder, exist_ok=True)
	output_path = os.path.join(output_folder, "config_simple_c1_generated.dsf")

	logger.debug(f"Writing config file to: {output_path}")

	# Write config file to JSON
	with open(output_path, "w") as outfile:
		json.dump(configFile, outfile, indent=4)

	logger.debug("Config file written successfully.")