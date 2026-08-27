# DSF GUI Build Tools

This folder contains the files needed to rebuild the Windows executable and installer:

- `build_release.bat`: one-click batch launcher to build the executable and installer.
- `build_release.ps1`: PowerShell build script.
- `DSF_GUI.spec`: PyInstaller configuration for the executable.
- `installer.iss`: Inno Setup configuration for the installer.

## One-time setup

Install Python for Windows with the `py` launcher. Then install PyInstaller:

```powershell
py -m pip install pyinstaller
```

Install Inno Setup 6. The build script searches for `ISCC.exe` in these locations:

```text
%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
C:\Program Files\Inno Setup 6\ISCC.exe
C:\Program Files (x86)\Inno Setup 6\ISCC.exe
```

## Rebuild the executable and installer

Simply double-click `build_release.bat` in File Explorer inside this `building tools/` folder.

Alternatively, run from PowerShell at the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File ".\building tools\build_release.ps1"
```

The build script will:

1. Run all unit tests (`py -m unittest discover -s tests -v`).
2. Rebuild the executable with PyInstaller (`dist\DSF_GUI.exe`).
3. Locate Inno Setup.
4. Build the installer (`dist\DSF_GUI_Setup.exe`).
5. Put both outputs in the root `dist\` folder.

## Build outputs

After a successful build, the files are:

```text
dist\DSF_GUI.exe
dist\DSF_GUI_Setup.exe
```

Send `DSF_GUI_Setup.exe` to a colleague for testing. They do not need Python, PyInstaller, or Inno Setup installed.

The PyInstaller spec also bundles `data\Simple_c1.dsf` as a local reference sample. It is not selected automatically by the file dialogs. The installer uses a per-user install directory so executable-local logging configuration can be written without administrator permissions.

The release script stops immediately when Python 3.10 or newer is unavailable, unit tests fail,
PyInstaller fails, or Inno Setup fails. This prevents an installer from being created
from stale executable output.

## Troubleshooting

- If `py` is not recognized, install Python and enable the Python launcher.
- If PyInstaller is missing, install the build extra with `py -3 -m pip install -e ".[build]"`.
- If Inno Setup is not found, install Inno Setup 6 and run the script again.
- If PowerShell blocks the script, use the command shown above with `-ExecutionPolicy Bypass`.
