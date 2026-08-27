$ErrorActionPreference = "Stop"

$buildTools = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $buildTools
Set-Location $projectRoot

$python = "py"
& $python -3.10 --version *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.10 is required for the release build. Install it and ensure the Python launcher can find it."
}

Write-Host "Running unit tests..."
& $python -3.10 -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Building DSF GUI executable..."
& $python -3.10 -m PyInstaller --noconfirm --clean (Join-Path $buildTools "DSF_GUI.spec")

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

Write-Host ""
Write-Host "Build complete:"
Write-Host (Join-Path $projectRoot "dist\DSF_GUI.exe")
Write-Host (Join-Path $projectRoot "dist\DSF_GUI_Setup.exe")