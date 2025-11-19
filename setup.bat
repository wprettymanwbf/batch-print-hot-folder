@echo off
REM Setup script for Batch Print Hot Folder on Windows

echo ========================================
echo Batch Print Hot Folder - Setup
echo ========================================
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed. Please install Python 3.7 or higher.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%
echo.

REM Install dependencies
echo Installing dependencies...
echo Upgrading pip to latest available for this Python...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo Warning: pip upgrade failed or was not necessary. Continuing with the current pip.
) else (
    echo pip upgraded successfully
)

echo Installing Python dependencies from requirements.txt...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Create config from example if it doesn't exist
if not exist config.json (
    echo Creating config.json from example...
    copy config.example.json config.json
    echo Created config.json
    echo.
    echo WARNING: Please edit config.json to configure your hot folders and printers
    echo.
) else (
    echo config.json already exists
    echo.
)

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit config.json to configure your hot folders
echo 2. Run the service with: run.bat or python batch_print.py
echo.
echo For help finding printer names, run: wmic printer get name
echo.
pause
