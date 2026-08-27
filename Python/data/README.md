# Sample & Reference DSF Files (`data/`)

## High-Level Purpose

This directory contains sample and reference **Data Sharing Framework (`.dsf`)** configuration files. These files serve as reference schemas, default files for the GUI editor, and input datasets for automated tests.

---

## File Overview

- **`Simple_c1.dsf`**
  - Default RDMA single-channel sample configuration file. Used as a baseline candidate when the GUI launches without a specified file path.

- **`udp_simpleloopback.dsf`**
  - Reference UDP loopback configuration containing transmit (TX) and receive (RX) transfer groups with integer IP address settings.

- **`config_multidirectional_1_Callea_to_Cotterle_generated.dsf`**
  - Complex multidirectional RDMA reference configuration used for benchmark import/export validation.
