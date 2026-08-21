# Multitarget HIL

Tools and project assets for building, configuring, and validating multitarget HIL systems with VeriStand and RDMA-based data sharing.

## Repository layout

- `Python/`
  - Python package, GUI, examples, tests, and sample DSF files.
- `VeriStand/`
  - VeriStand projects, screens, and DSF assets used by the deployed HIL workflows.

## Architecture

The Python tooling is responsible for authoring and validating RDMA configuration files. Those `.dsf` outputs can then be consumed by the VeriStand-side assets in this repository.

Main Python components:

- `multitarget_hil.rdma_definitions`
  - Object model for plugins, threads, transfer groups, transfers, channels, and serialized component settings.
- `multitarget_hil.gui`
  - Tkinter editor for creating, loading, validating, and saving DSF/JSON configurations.
- `examples/`
  - Usage examples for building configurations and round-tripping serialized data.
- `tests/`
  - Regression tests for model validation and GUI session behavior.

## Supported toolchain

- VeriStand 2025 Q3
- Python 3.10+
- LabVIEW 2025 Q3

## Typical workflow

1. Create or edit a configuration in `Python/`.
2. Save the configuration as a `.dsf` file.
3. Use the generated DSF alongside the VeriStand project files under `VeriStand/`.
4. Validate behavior with the included Python tests before packaging or sharing updates.

## Python quick start

From `Python/`:

```bash
python -m unittest discover -s tests -v
python -m compileall multitarget_hil tests examples
python HMI/rdma_gui.py
python -m examples.import_config_example
python -m examples.rdma_configuration_example
```

Optional lint/format commands if Ruff is installed:

```bash
ruff check .
ruff format --check .
```

## Where the sample data lives

- `Python/data/Simple_c1.dsf`
  - Default GUI sample file.
- `Python/data/config_multidirectional_1_Callea_to_Cotterle_generated.dsf`
  - Regression/reference configuration used by examples and tests.
- `VeriStand/rdma configs/`
  - VeriStand-oriented DSF samples and generated configuration artifacts.

## Building the Windows GUI

See `Python/building tools/README.md`.
