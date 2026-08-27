$ErrorActionPreference = "Stop"

$buildTools = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $buildTools
Set-Location $projectRoot

$python = "py"
& $python -3 --version *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.10 or newer is required for the release build. Install it and ensure the Python launcher can find it."
}

$pythonVersion = & $python -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$versionParts = $pythonVersion.Trim().Split('.')
if ([int]$versionParts[0] -lt 3 -or ([int]$versionParts[0] -eq 3 -and [int]$versionParts[1] -lt 10)) {
    throw "Python 3.10 or newer is required for the release build. Found $pythonVersion."
}

Write-Host "Running unit tests..."
& $python -3 -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Building DSF GUI executable..."
& $python -3 -m PyInstaller --noconfirm --clean (Join-Path $buildTools "DSF_GUI.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE. Installer creation was skipped." }

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

Write-Host ""
Write-Host "Build complete:"
Write-Host (Join-Path $projectRoot "dist\DSF_GUI.exe")
Write-Host (Join-Path $projectRoot "dist\DSF_GUI_Setup.exe")