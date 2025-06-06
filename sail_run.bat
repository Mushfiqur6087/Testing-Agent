@echo off
setlocal enabledelayedexpansion

:: =============================================
:: SAIL (Smart Automation for Intelligent LLM-powered Testing)
:: =============================================
:: This script starts the SAIL integration with proper environment setup
:: Author: Your Name
:: Last Updated: 2024
:: =============================================

echo.
echo 🎯 SAIL (Smart Automation for Intelligent LLM-powered Testing)
echo ============================================================
echo.

:: Check if we're in the correct directory structure
if not exist "agent_interface" (
    echo ❌ Error: agent_interface directory not found
    echo Please run this script from your Testing-Agent root directory
    pause
    exit /b 1
)

if not exist "web_interface" (
    echo ❌ Error: web_interface directory not found
    echo Please run this script from your Testing-Agent root directory
    pause
    exit /b 1
)

:: Start the agent interface
echo 🚀 Starting Agent Interface...
start cmd /k "cd agent_interface && agent_run.bat"

:: Start the web interface
echo 🌐 Starting Web Interface...
start cmd /k "cd web_interface && npm run dev"

echo.
echo ✅ Both interfaces are starting...
echo 📝 Agent Interface will be available at: http://localhost:5000
echo 📝 Web Interface will be available at: http://localhost:3000
echo.
echo ⚠️  Press any key to stop all services
pause

:: Kill both processes
taskkill /F /IM node.exe
taskkill /F /IM python.exe

echo.
echo ✅ All services stopped
pause 