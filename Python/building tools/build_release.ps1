$ErrorActionPreference = "Stop"

$buildTools = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $buildTools
Set-Location $projectRoot

Write-Host "Running unit tests..."
py -m unittest discover -s tests -v

Write-Host "Building RDMA GUI executable..."
py -m PyInstaller --noconfirm --clean (Join-Path $buildTools "RDMA_GUI.spec")

$isccCandidates = @(
    (Join-Path ${env:LOCALAPPDATA} "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles} "Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe")
)
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $iscc) {
    throw "Inno Setup was not found. Install it from https://jrsoftware.org/isinfo.php and run this script again."
}

Write-Host "Building RDMA GUI installer..."
& $iscc (Join-Path $buildTools "installer.iss")

Write-Host ""
Write-Host "Build complete:"
Write-Host (Join-Path $projectRoot "dist\RDMA_GUI.exe")
Write-Host (Join-Path $projectRoot "dist\RDMA_GUI_Setup.exe")