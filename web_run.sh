#!/bin/bash
# ===================================================
# runWeb.sh - Script to start the web interface (Next.js)
# ===================================================
# This script navigates to the web_interface directory,
# installs dependencies if needed, and starts the Next.js dev server.
# ===================================================

# Web Interface Startup Script
echo "🚀 Starting Web Interface..."

# Check if we're in the right directory
if [ ! -d "web_interface" ]; then
    echo "❌ Please run this script from your Testing-Agent root directory"
    exit 1
fi

# Navigate to web_interface directory
cd web_interface

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "🔧 Setting up environment variables..."
    cat > .env.local << EOF
# SAIL Configuration
NEXT_PUBLIC_APP_NAME=SAIL
NEXT_PUBLIC_APP_DESCRIPTION="Smart Automation for Intelligent LLM-powered Testing"
EOF
    echo "⚠️ Please update .env.local with your OpenAI API key"
fi

# Start the development server
echo "🌐 Starting development server..."
npm run dev

# Note: The server will be available at http://localhost:3000
# Press Ctrl+C to stop the server when done. 