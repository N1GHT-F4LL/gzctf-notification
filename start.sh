#!/bin/bash

# GZCTF Discord Notification Bot Startup Script

echo "🚀 Starting GZCTF Discord Notification Bot..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy env.example to .env and configure your settings."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed!"
    exit 1
fi

# Check if requirements are installed
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Test configuration
echo "🧪 Testing configuration..."
python test_config.py

if [ $? -eq 0 ]; then
    echo "✅ Configuration test passed!"
    echo "🤖 Starting bot..."
    python main.py
else
    echo "❌ Configuration test failed!"
    echo "Please check your .env file and try again."
    exit 1
fi 