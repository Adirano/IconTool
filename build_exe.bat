@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

REM =============================================
REM IconTool one-click build script
REM Output: dist\IconTool.exe
REM =============================================

cd /d "%~dp0"
echo [INFO] Working directory: %CD%

REM 1) Prefer project virtual environment
set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
    echo [INFO] Using venv Python: "%PYTHON_EXE%"
) else (
    set "PYTHON_EXE=python"
    echo [INFO] .venv not found, fallback to system Python: "%PYTHON_EXE%"
)

REM 2) Check Python availability
%PYTHON_EXE% --version >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python or create .venv first.
    pause
    exit /b 1
)

REM 3) Install/update build dependencies
echo [INFO] Installing/updating PyInstaller and Pillow...
%PYTHON_EXE% -m pip install --upgrade pip
%PYTHON_EXE% -m pip install --upgrade pyinstaller pillow
if errorlevel 1 (
    echo [ERROR] Dependency installation failed. Please check network or pip source.
    pause
    exit /b 1
)

REM 4) Clean old artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist IconTool.spec del /f /q IconTool.spec

REM 5) Build executable
echo [INFO] Building IconTool.exe ...
%PYTHON_EXE% -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name IconTool ^
  --collect-submodules PIL ^
  --collect-data PIL ^
  --collect-binaries PIL ^
  main.py

if errorlevel 1 (
        echo [ERROR] Build failed. Check the log above.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Build completed.
echo [SUCCESS] Executable: %CD%\dist\IconTool.exe
echo [TIP] Copy dist\IconTool.exe to another Windows PC to run.
echo.
pause
exit /b 0
