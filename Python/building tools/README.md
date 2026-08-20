# RDMA GUI Build Tools

This folder contains the files needed to rebuild the Windows executable and installer:

- `build_release.ps1`: rebuilds the executable and installer.
- `RDMA_GUI.spec`: PyInstaller configuration for the executable.
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

1. Open PowerShell.
2. Change to the project root, not this folder:

```powershell
cd "C:\Users\xxx\Documents\Multitarget_HIL\Python"
```

3. Run the build script:

```powershell
powershell -ExecutionPolicy Bypass -File ".\building tools\build_release.ps1"
```

The script will:

1. Rebuild the executable with PyInstaller.
2. Locate Inno Setup.
3. Build the installer.
4. Put both outputs in the root `dist` folder.

## Build outputs

After a successful build, the files are:

```text
dist\RDMA_GUI.exe
dist\RDMA_GUI_Setup.exe
```

Send `RDMA_GUI_Setup.exe` to a colleague for testing. They do not need Python, PyInstaller, or Inno Setup installed.

## Troubleshooting

- If `py` is not recognized, install Python and enable the Python launcher.
- If PyInstaller is missing, run `py -m pip install pyinstaller`.
- If Inno Setup is not found, install Inno Setup 6 and run the script again.
- If PowerShell blocks the script, use the command shown above with `-ExecutionPolicy Bypass`.
