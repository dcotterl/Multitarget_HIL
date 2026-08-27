# Test Suite (`tests/`)

## High-Level Purpose

This directory contains the automated unit and integration test suite for the `data_sharing_framework_config_api` package. Tests verify model round-trip serialization, IP address conversion, and fixture file compatibility.

---

## Running the Tests

Execute all tests from the repository root (`Python/`):

```bash
python -m unittest discover -s tests -v
```

---

## File Overview

- **`test_rdma_definitions.py`**
  - Unit tests covering RDMA model objects, round-trip serialization (`getDict()` / `from_dict()`), and fixture import validation against benchmark files.

- **`test_upd_definitions.py`**
  - Unit tests covering UDP model objects, IP string conversion functions (`ip_to_string`, `string_to_ip`), and UDP benchmark fixture imports.

- **`udp_simpleloopback.dsf`**
  - Test fixture configuration file used by `test_upd_definitions.py`.

- **`config_multidirectional_1_Callea_to_Cotterle_generated.dsf`**
  - Test fixture configuration file used by `test_rdma_definitions.py`.
