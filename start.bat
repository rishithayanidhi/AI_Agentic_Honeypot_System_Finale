@echo off
REM Quick start script for Windows

echo ============================================================
echo   AI Agentic Honeypot System - Quick Start
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup first: python setup.py
    echo.
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please run setup first: python setup.py
    echo.
    pause
    exit /b 1
)

echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

echo [2/3] Checking configuration...
python -c "from config import settings; print(f'  - API Key: {settings.API_KEY[:10]}...'); print(f'  - LLM Provider: {settings.LLM_PROVIDER}'); print(f'  - Port: {settings.PORT}')" 2>nul

if errorlevel 1 (
    echo [ERROR] Configuration error! Please check your .env file.
    pause
    exit /b 1
)

echo [3/3] Starting server...
echo.
echo Server will start at http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
echo ============================================================
echo.

python main.py

pause
