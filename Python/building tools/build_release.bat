@echo off
setlocal
cd /d "%~dp0.."

echo ===================================================
echo   DSF GUI Release Build (Executable + Installer)
echo ===================================================
echo.

powershell -ExecutionPolicy Bypass -File ".\building tools\build_release.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed! Check error messages above.
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] Build completed successfully!
echo Executable and Installer generated in: %~dp0..\dist\
echo.
pause
