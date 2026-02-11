#!/bin/bash
# Quick start script for Linux/macOS

echo "============================================================"
echo "  AI Agentic Honeypot System - Quick Start"
echo "============================================================"
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run setup first: python3 setup.py"
    echo
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "[ERROR] .env file not found!"
    echo "Please run setup first: python3 setup.py"
    echo
    exit 1
fi

echo "[1/3] Activating virtual environment..."
source venv/bin/activate

echo "[2/3] Checking configuration..."
python -c "from config import settings; print(f'  - API Key: {settings.API_KEY[:10]}...'); print(f'  - LLM Provider: {settings.LLM_PROVIDER}'); print(f'  - Port: {settings.PORT}')" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "[ERROR] Configuration error! Please check your .env file."
    exit 1
fi

echo "[3/3] Starting server..."
echo
echo "Server will start at http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo
echo "============================================================"
echo

python main.py
