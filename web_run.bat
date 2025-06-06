@echo off
REM ===================================================
REM web_run.bat - Script to start the web interface (Next.js)
REM ===================================================
REM This script navigates to the web_interface directory,
REM installs dependencies if needed, and starts the Next.js dev server.
REM ===================================================

echo 🚀 Starting Web Interface...

REM Check if we're in the right directory
if not exist "web_interface" (
    echo ❌ Please run this script from your Testing-Agent root directory
    exit /b 1
)

REM Navigate to web_interface directory
cd web_interface

REM Check if node_modules exists
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install
)

REM Check if .env.local exists
if not exist ".env.local" (
    echo 🔧 Setting up environment variables...
    (
        echo # SAIL Configuration
        echo NEXT_PUBLIC_APP_NAME=SAIL
        echo NEXT_PUBLIC_APP_DESCRIPTION="Smart Automation for Intelligent LLM-powered Testing"
    ) > .env.local
    echo ⚠️ Please update .env.local with your OpenAI API key
)

REM Start the development server
echo 🌐 Starting development server...
npm run dev

REM Note: The server will be available at http://localhost:3000
REM Press Ctrl+C to stop the server when done. 