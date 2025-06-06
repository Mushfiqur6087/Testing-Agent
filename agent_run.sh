#!/bin/bash

# =============================================
# SAIL Testing Agent Interface Runner
# =============================================
# This script starts the agent interface with proper environment setup
# Author: Your Name
# Last Updated: 2024
# =============================================

# Function to handle errors
handle_error() {
    echo "❌ Error: $1"
    echo "Press Enter to continue..."
    read
    exit 1
}

# Check if Python is installed
echo "🔍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    handle_error "Python is not installed or not in PATH"
fi

# Check if pip is installed
echo "🔍 Checking pip installation..."
if ! command -v pip &> /dev/null; then
    handle_error "pip is not installed or not in PATH"
fi

# Navigate to agent_interface directory
echo "📂 Changing to agent_interface directory..."
cd agent_interface || handle_error "Failed to change to agent_interface directory"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    handle_error "requirements.txt not found in agent_interface directory"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🌱 Creating Python virtual environment..."
    python3 -m venv venv || handle_error "Failed to create virtual environment"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate || handle_error "Failed to activate virtual environment"

# Upgrade pip
echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip || handle_error "Failed to upgrade pip"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt || handle_error "Failed to install dependencies"

# Start Flask server
echo
echo "🚀 Starting Flask server..."
echo "📝 Server will be available at: http://localhost:5000"
echo "⚠️  Press Ctrl+C to stop the server"
echo

python main.py

# Deactivate virtual environment on exit
deactivate

echo
echo "✅ Agent interface stopped"
read -p "Press Enter to continue..." 