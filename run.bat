@echo off
echo ======================================================================
echo  IMAIRA FairScore — One-Click Launcher for Windows
echo ======================================================================

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found! Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

:: Check if virtual environment exists, if not create one
if not exist "venv" (
    echo [1/3] Creating Python virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo [2/3] Activating virtual environment and checking dependencies...
call venv\Scripts\activate.bat

:: Install/verify dependencies
pip install -r requirements.txt --quiet

:: Run pre-flight check
python check_setup.py

echo.
echo [3/3] Starting IMAIRA FairScore server...
echo Platform will be available at: http://localhost:8002
echo (Keep this window open while using the app. Press Ctrl+C to stop)
echo.

python -m api.main
pause
