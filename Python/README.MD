# Python Folder

This folder contains the Python-based components used by the Multitarget HIL project. It is intended to hold the object definitions, scripts, and supporting code required to interface with the system, process data, and support simulation or hardware-in-the-loop workflows.

## Purpose
This is specificly aimed at giving the user a convinient sets of API and GIU to create a data sharing framework configuration to implement RDMA data sharing between targets.

## RDMA_Definition.py

`RDMA_Definition.py` is typically the Python module that defines the data structures, configuration constants, and interface elements related to the RDMA communications used by the Multitarget HIL system. In a project like this, it often contains:

- class definitions for RDMA-related objects, 
- constants for addresses, packet formats, protocol identifiers, and timing values
- helper functions for encoding/decoding data or validating payloads
- connection configuration for communication with hardware or simulated targets
- reusable definitions shared by scripts, test code, and higher-level automation logic

This file is usually the foundation for other Python modules because it centralizes the meaning of the data exchanged between the controller, simulation, and hardware components.

## Example Folder

The `Example` folder contains two example Python files that demonstrate how to use the RDMA definitions in practice. The first example focuses on creating and configuring a data-sharing setup, while the second shows how to connect to the configured targets and exchange RDMA data; together, they provide a starting point for building and testing Multitarget HIL applications.

### rdma_configuration_example.py

`rdma_configuration_example.py` demonstrates how to set up and configure a data-sharing framework for RDMA communications. This example shows how to instantiate RDMA configuration objects, define the data structures that will be shared between targets, specify memory addresses and buffer sizes, and establish the initial configuration parameters needed before any data exchange occurs. It serves as a template for users who need to create custom RDMA configurations for their specific hardware or simulation targets.

### import_config_example.py

`import_config_example.py` demonstrates how to load an existing RDMA configuration and use it to establish connections with configured targets for active data exchange. This example shows how to import a previously saved configuration, connect to the targets, and perform read/write operations to exchange RDMA data. It provides practical guidance on how to leverage a configuration created with `rdma_configuration_example.py` to implement real data-sharing workflows in a Multitarget HIL system.

## HMI

### rdma_gui.py

`rdma_gui.py` provides a graphical interface for interacting with the RDMA configuration and target connections. This module is intended to make the setup and monitoring of shared-memory data flows easier for users by exposing configuration controls, connection status, and runtime information through a GUI. It typically supports loading or creating RDMA definitions, selecting targets, viewing communication state, and validating data-sharing settings before execution. The GUI serves as a user-friendly layer on top of the lower-level Python objects and scripts, helping simplify setup and troubleshooting for Multitarget HIL workflows.

## Building the Windows application

Install Python with the `py` launcher, install PyInstaller, and install Inno Setup once. Then run this from the Python folder:

```powershell
py -m pip install pyinstaller
.\building tools\build_release.ps1
```

The script creates `dist\RDMA_GUI.exe` and the distributable installer `dist\RDMA_GUI_Setup.exe`.

