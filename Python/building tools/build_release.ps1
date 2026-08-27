$ErrorActionPreference = "Stop"

$buildTools = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $buildTools
Set-Location $projectRoot

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $python = "py"
    $pythonArgs = @("-3")
    & $python @pythonArgs -m venv (Join-Path $projectRoot ".venv")
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the project virtual environment. Install Python 3.10 or newer."
    }
}
$python = $venvPython
$pythonArgs = @()

& $python --version *> $null
if ($LASTEXITCODE -ne 0) {
    throw "The project virtual environment is not usable. Recreate .venv with Python 3.10 or newer."
}

$pythonVersion = & $python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$versionParts = $pythonVersion.Trim().Split('.')
if ([int]$versionParts[0] -lt 3 -or ([int]$versionParts[0] -eq 3 -and [int]$versionParts[1] -lt 10)) {
    throw "Python 3.10 or newer is required for the release build. Found $pythonVersion."
}

& $python -m pip install -e ".[build]"
if ($LASTEXITCODE -ne 0) {
    throw "Could not install the project build dependencies."
}

Write-Host "Running unit tests..."
& $python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -c "import PyInstaller" *> $null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is not installed in the selected Python environment. Install it with: $python -m pip install -e `".[build]`""
}

Write-Host "Building DSF GUI executable..."
Remove-Item -Recurse -Force (Join-Path $projectRoot "build\DSF_GUI"), (Join-Path $projectRoot "dist\DSF_GUI.exe") -ErrorAction SilentlyContinue
& $python -m PyInstaller --noconfirm --clean (Join-Path $buildTools "DSF_GUI.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE. Installer creation was skipped." }

$executablePath = Join-Path $projectRoot "dist\DSF_GUI.exe"
if (-not (Test-Path $executablePath)) {
    throw "PyInstaller completed without producing $executablePath. Installer creation was skipped."
}

$isccCandidates = @(
    (Join-Path ${env:LOCALAPPDATA} "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles} "Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe")
)
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $iscc) {
    throw "Inno Setup was not found. Install it from https://jrsoftware.org/isinfo.php and run this script again."
}

Write-Host "Building DSF GUI installer..."
& $iscc (Join-Path $buildTools "installer.iss")
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed with exit code $LASTEXITCODE." }

$installerPath = Join-Path $projectRoot "dist\DSF_GUI_Setup.exe"
if (-not (Test-Path $installerPath)) {
    throw "Inno Setup completed without producing $installerPath."
}

Write-Host ""
Write-Host "Build complete:"
Write-Host (Join-Path $projectRoot "dist\DSF_GUI.exe")
Write-Host (Join-Path $projectRoot "dist\DSF_GUI_Setup.exe")