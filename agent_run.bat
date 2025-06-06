@echo off
setlocal enabledelayedexpansion

:: =============================================
:: SAIL Testing Agent Interface Runner
:: =============================================
:: This script starts the agent interface with proper environment setup
:: Author: Your Name
:: Last Updated: 2024
:: =============================================

echo.
echo 🚀 Starting SAIL Testing Agent Interface...
echo.

:: Check if Python is installed
echo 🔍 Checking Python installation...
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

:: Check if pip is installed
echo 🔍 Checking pip installation...
where pip >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Error: pip is not installed or not in PATH
    echo Please install pip and try again
    pause
    exit /b 1
)

:: Navigate to agent_interface directory
echo 📂 Changing to agent_interface directory...
cd agent_interface
if %ERRORLEVEL% neq 0 (
    echo ❌ Error: Failed to change to agent_interface directory
    pause
    exit /b 1
)

:: Check if requirements.txt exists
if not exist requirements.txt (
    echo ❌ Error: requirements.txt not found in agent_interface directory
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo 🌱 Creating Python virtual environment...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo ❌ Error: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo 🔌 Activating virtual environment...
    call venv\Scripts\activate.bat
    echo ⬆️  Upgrading pip...
    python -m pip install --upgrade pip
    echo 📦 Installing dependencies...
    pip install -r requirements.txt
) else (
    echo 🔌 Activating virtual environment...
    call venv\Scripts\activate.bat
)

:: Start Flask server
echo.
echo 🚀 Starting Flask server...
echo 📝 Server will be available at: http://localhost:5000
echo ⚠️  Press Ctrl+C to stop the server
echo.

python main.py

:: Deactivate virtual environment on exit
call deactivate

echo.
echo ✅ Agent interface stopped
pause 