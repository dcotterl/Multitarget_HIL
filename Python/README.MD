# Python Tooling

This directory contains the Python package, GUI, examples, tests, and build assets used to create RDMA data-sharing configurations for multitarget HIL systems.

## Contents

- `/home/runner/work/Multitarget_HIL/Multitarget_HIL/Python/multitarget_hil`
  - Packaged Python source for the RDMA model and GUI.
- `/home/runner/work/Multitarget_HIL/Multitarget_HIL/Python/HMI/rdma_gui.py`
  - Compatibility launcher for the packaged GUI.
- `/home/runner/work/Multitarget_HIL/Multitarget_HIL/Python/RDMA_Definitions.py`
  - Compatibility wrapper for the packaged model module.
- `/home/runner/work/Multitarget_HIL/Multitarget_HIL/Python/examples`
  - Example scripts for configuration creation and import/export validation.
- `/home/runner/work/Multitarget_HIL/Multitarget_HIL/Python/tests`
  - Automated regression coverage for the model and GUI session logic.
- `/home/runner/work/Multitarget_HIL/Multitarget_HIL/Python/data`
  - Sample and reference DSF files used by the GUI, tests, and examples.
- `/home/runner/work/Multitarget_HIL/Multitarget_HIL/Python/building tools`
  - Windows packaging assets for the standalone GUI executable and installer.

## Package structure

### `multitarget_hil.rdma_definitions`

Provides:

- the RDMA configuration object model
- import/export helpers for DSF and JSON content
- validation for nested object types and transfer-direction invariants
- backwards-compatible aliases for the original class names

### `multitarget_hil.gui`

Provides:

- a Tkinter editor for configuration trees
- centralized session and file handling
- inline editing with unsaved-change prompts
- a default sample DSF lookup for local source and packaged builds

## Running the tests

From `/home/runner/work/Multitarget_HIL/Multitarget_HIL/Python`:

```bash
python -m unittest discover -s tests -v
```

## Basic validation and style checks

Syntax validation:

```bash
python -m compileall multitarget_hil tests examples
```

Optional lint/format checks if Ruff is installed:

```bash
ruff check .
ruff format --check .
```

The shared Ruff settings live in `/home/runner/work/Multitarget_HIL/Multitarget_HIL/Python/pyproject.toml`.

## Running the GUI

From `/home/runner/work/Multitarget_HIL/Multitarget_HIL/Python`:

```bash
python HMI/rdma_gui.py
```

The GUI can load or save `.dsf` and `.json` files. It defaults to the sample file at `/home/runner/work/Multitarget_HIL/Multitarget_HIL/Python/data/Simple_c1.dsf` when available.

## Running the examples

```bash
python -m examples.import_config_example
python -m examples.rdma_configuration_example
```

## Building the Windows application

```powershell
py -m pip install pyinstaller
powershell -ExecutionPolicy Bypass -File ".\\building tools\\build_release.ps1"
```

The build script now runs the unit tests before packaging. After a successful build, the expected outputs are:

- `dist\\RDMA_GUI.exe`
- `dist\\RDMA_GUI_Setup.exe`
