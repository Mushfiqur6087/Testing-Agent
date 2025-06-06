#!/bin/bash
# ===================================================
# runSAIL.sh - Script to start both the web interface and agent interface
# ===================================================
# This script starts the web interface (Next.js) and the agent interface (Python/Flask)
# in separate terminal windows.
# ===================================================

# SAIL Startup Script
echo "🎯 SAIL (Smart Automation for Intelligent LLM-powered Testing)"
echo "============================================================"

# Check if we're in the right directory
if [ ! -d "src" ] || [ ! -d "web_interface" ]; then
    echo "❌ Please run this script from your Testing-Agent root directory"
    exit 1
fi

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start SAIL
echo "🚀 Starting SAIL Integration..."
python3 agent_interface/utils/integration_bridge.py start

# Note: The server will be available at http://localhost:5000
# Press Ctrl+C to stop the server when done

echo "Starting Testing Agent Project..."

# Start the web interface in a new terminal window
echo "Starting Web Interface..."
gnome-terminal -- bash -c "cd web_interface && npm run dev; exec bash"

# Start the agent interface in a new terminal window
echo "Starting Agent Interface..."
gnome-terminal -- bash -c "cd agent_interface && python main.py; exec bash"

echo "Both services are starting..."
echo "Web Interface will be available at: http://localhost:3000"
echo "Agent Interface will be available at: http://localhost:5000" 