# Examples (`examples/`)

## High-Level Purpose

This directory contains standalone Python example scripts demonstrating how to use the `data_sharing_framework_config_api` package programmatically without the GUI. They demonstrate how to construct configurations, add channels and transfers, and import/export `.dsf` files.

---

## File Overview

- **`rdma_configuration_example.py`**
  - Demonstrates programmatic construction of an RDMA configuration from scratch (bottom-up), serializing it to JSON/DSF, and saving it to disk.

- **`udp_configuration_example.py`**
  - Demonstrates programmatic construction of a UDP configuration, configuring IP addresses, ports, and channel metadata.

- **`import_config_example.py`**
  - Demonstrates loading an existing `.dsf` file from disk (`definitions.Configuration.from_dict()`), inspecting its object hierarchy, and re-exporting it.

- **`testdef.py`**
  - Scratchpad script used for testing internal API definitions during development.

---

## Subdirectories

- **[`output/`](output/README.md)**
  - Default output directory where example scripts write generated `.dsf` files.
