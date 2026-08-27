# Python Tooling

This directory contains the Python package, GUI, examples, tests, and build assets used to create data-sharing framework configurations for multitarget HIL systems.

## Documentation

- **[API & Codebase Reference Guide](API_DOCUMENTATION.md)** — Comprehensive guide covering who does what, complete class/method reference, and code examples for junior developers.
- **[Architecture Guide](ARCHITECTURE.md)** — Design architecture, package module layout, and extensibility instructions for adding new protocols.

## Contents

- `data_sharing_framework_config_api/`
  - Packaged Python source for the RDMA model and GUI.
- `examples/`
  - Example scripts for configuration creation and import/export validation.
- `tests/`
  - Automated regression coverage for the model and GUI session logic.
- `data/`
  - Sample and reference DSF files used by the GUI, tests, and examples.
- `building tools/`
  - Windows packaging assets for the standalone GUI executable and installer.

## Package structure

### `data_sharing_framework_config_api`

Provides:

- Base model definitions (`definitions.py`) for multi-protocol HIL configurations
- Protocol-specific extensions (`rdma_definitions.py` and `udp_definitions.py`)
- Extensible protocol creation factory (`protocol_factory.py`)
- Configurable logging system (`logger_config.py` and `logging_config.json`); if `logging_config.json` is missing at runtime, it is automatically generated with default settings (`INFO` level, file logging enabled to `app.log`). In packaged/executable runs, the config is created next to the executable so it is reused on subsequent launches.
- Import/export helpers for DSF and JSON files

### `data_sharing_framework_config_api.gui`

Provides:

- A Tkinter editor supporting multi-protocol configurations
- Centralized session state management (`ConfigurationSession`)
- Inline attribute editing with unsaved-change prompts and TX/RX direction adaptation
- Dynamic protocol selection and context menus
- A real-time Debug Log viewer window with automatic refresh and a Logger Config window

## Running the tests

From `Python/`:

```bash
python -m unittest discover -s tests -v
```

## Basic validation and style checks

Syntax validation:

```bash
python -m compileall data_sharing_framework_config_api tests examples
```

Optional lint/format checks if Ruff is installed:

```bash
ruff check .
ruff format --check .
```

The shared Ruff settings live in `pyproject.toml`.

## Running the GUI

From `Python/`:

```bash
python -m data_sharing_framework_config_api.gui.app
```

The GUI can load or save `.dsf` and `.json` files. File dialogs open in the last directory used by the session; before a file is loaded or saved, they open beside the executable.

## Running the examples

```bash
python -m examples.import_config_example
python -m examples.rdma_configuration_example
```

## Building the Windows application

Simply double-click `build_release.bat` inside the `building tools/` folder in File Explorer, or run from terminal:

```cmd
".\building tools\build_release.bat"
```

Or via PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File ".\building tools\build_release.ps1"
```

The build script runs the complete unit test suite before packaging. After a successful build, the expected outputs are:

- `dist\DSF_GUI.exe`
- `dist\DSF_GUI_Setup.exe`
