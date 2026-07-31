from copy import deepcopy
import json
from enum import Enum

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
	return deepcopy(RDMA_JSON_Template)

def get_base_file():
    """Return a deep-copied template so callers can safely modify it."""
    return deepcopy(Base_File_Specification_Template)

def get_plugin():
    """Return a deep-copied template so callers can safely modify it."""
    return deepcopy(Pluging_Specification_Template)

def get_thread():
    """Return a deep-copied template so callers can safely modify it."""
    return deepcopy(Thread_Specification_Template)

def get_transfergroup():
    """Return a deep-copied template so callers can safely modify it."""
    return deepcopy(Transfer_Group_Specification_Template)

def get_tx_transfer():
    """Return a deep-copied template so callers can safely modify it."""
    return deepcopy(Tx_Transfer_Specification_Template)

def get_rx_transfer():
    """Return a deep-copied template so callers can safely modify it."""
    return deepcopy(Rx_Transfer_Specification_Template)

def get_channel():
    """Return a deep-copied template so callers can safely modify it."""
    return deepcopy(Channel_Specification_Template)

# Hierarchy of templates:
#    config file
#        plugin [1..n]
#            thread [1..n]
#                transfer group [1..n]
#                    transfer [1..n]
#                        channel [1..n]

def makeChannels(nCh):
	# Building n channels
	channels = []
	for i in range(nCh):
		channel = get_channel()
		channel["core"]["name"] = f"Channel{i+1}"
		channel["core"]["units"] = ""
		channels.append(channel)
	return channels

def makeTransfers(direction:Direction, localIP, localPort, channels, destIP=None, destPort=None):
    if direction == Direction.TX:
        transfer = get_tx_transfer()
        transfer["core"]["name"] = "TransferTx"
        transfer["channels"] = channels
        transfer["component settings"][0]["values"][0]["value"] = localIP
        transfer["component settings"][0]["values"][1]["value"] = localPort
        transfer["component settings"][0]["values"][2]["value"] = destIP
        transfer["component settings"][0]["values"][3]["value"] = destPort
    elif direction == Direction.RX:
        transfer = get_rx_transfer()
        transfer["core"]["name"] = "TransferRx"
        transfer["channels"] = channels
        transfer["component settings"][0]["values"][0]["value"] = localIP
        transfer["component settings"][0]["values"][1]["value"] = localPort
    return transfer

def makeTransferGroups(direction:Direction, transfers, groupName="Group"):
    group = get_transfergroup()
    if direction == Direction.TX:
         group["core"]["name"] = groupName + "Tx"
    elif direction == Direction.RX:
        group["core"]["name"] = groupName + "Rx"

    group["core"]["direction"] = direction.value
    group["transfers"] = transfers
    return group

def makeThreads(groups):
	thread = get_thread()
	thread["transfer groups"] = groups
	return thread

def makePlugins(threads, name="Plugin"):
	plugin = get_plugin()
	plugin["core"]["name"] = name
	plugin["threads"] = threads
	return plugin

def makeConfigFile(plugins):
	configFile = get_base_file()
	configFile["configuration"]["plugins"] = plugins
	return configFile

if __name__ == "__main__":
    
    # Building channels
    channels = makeChannels(2)
    
    # Building transfers
    transfer_tx = makeTransfers(Direction.TX, "169.254.49.44", "5000", channels, "169.254.23.111", "5001")
    transfer_rx = makeTransfers(Direction.RX, "169.254.23.111", "5001", channels)
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

    print(json.dumps(configFile, indent=4))
    
    # Write config file to JSON
    with open("config_simple_c1_generated.dsf", "w") as outfile:
        json.dump(configFile, outfile, indent=4)

	