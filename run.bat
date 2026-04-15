@echo off
REM ADSA Compression System - Windows Setup and Run

echo ==========================================
echo   ADSA File Compression System
echo   Frontend ^& Backend Setup (Windows)
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

echo Python found: 
python --version
echo.

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Error: Failed to install Python dependencies
    pause
    exit /b 1
)

echo ✓ Python dependencies installed
echo.

REM Start Flask backend
echo Starting Flask backend server...
echo Backend will run on: http://localhost:5000
start cmd /k python app.py

REM Small delay to let Flask start
timeout /t 2 /nobreak

REM Open frontend in browser
echo.
echo ==========================================
echo ✓ Backend Started!
echo.
echo Frontend opening in browser...
echo.
echo If browser doesn't open:
echo - Open index.html directly in your browser, or
echo - Use Python's built-in server:
echo   python -m http.server 8000
echo   Then go to: http://localhost:8000/index.html
echo.
echo API Endpoints:
echo   GET  /api/health                 - Health check
echo   GET  /api/algorithms             - List algorithms
echo   POST /api/compress               - Compress file
echo   POST /api/decompress             - Decompress file
echo   POST /api/analyze                - Analyze file
echo.
echo Press Ctrl+C in backend window to stop
echo ==========================================
echo.

REM Open the HTML file
start index.html

pause
