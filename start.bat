@echo off
cd /d "%~dp0"

where python >nul 2>&1 || (echo Python not found. Please install Python 3.9+ && pause & exit /b 1)

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -q -r requirements.txt

echo.
echo Starting Auto Ticket Filler at http://localhost:5000
echo Press Ctrl+C to stop.
echo.
python app.py
pause
