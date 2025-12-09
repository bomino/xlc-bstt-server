@echo off
REM BSTT Backend Startup Script
REM This script starts the Django backend server

echo ========================================
echo BSTT Backend Server Startup
echo ========================================
echo.

cd /d "%~dp0backend"

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if dependencies are installed
echo Checking dependencies...
pip show django >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Run migrations
echo Running database migrations...
python manage.py migrate

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

echo.
echo ========================================
echo Starting Django Development Server
echo Backend API: http://localhost:8000/api/
echo Admin Panel: http://localhost:8000/admin/
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server (accessible from network)
python manage.py runserver 0.0.0.0:8000
