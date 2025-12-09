@echo off
REM BSTT First-Time Setup Script
REM Run this script once to set up the application

echo ========================================
echo BSTT First-Time Setup
echo ========================================
echo.

cd /d "%~dp0"

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)
python --version

REM Check Node.js installation
echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 16+ from https://nodejs.org/
    pause
    exit /b 1
)
node --version
npm --version

echo.
echo ========================================
echo Setting up Backend
echo ========================================
echo.

cd backend

REM Create virtual environment
if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate and install dependencies
echo Installing Python dependencies...
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

REM Setup database
echo Setting up database...
python manage.py migrate
if errorlevel 1 (
    echo ERROR: Database migration failed
    pause
    exit /b 1
)

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

echo.
echo ========================================
echo Creating Admin User
echo ========================================
echo.
echo Please create an admin user for the Django admin panel:
python manage.py createsuperuser

cd ..

echo.
echo ========================================
echo Setting up Frontend
echo ========================================
echo.

cd frontend

REM Install npm dependencies
echo Installing npm dependencies (this may take a few minutes)...
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install npm dependencies
    pause
    exit /b 1
)

cd ..

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo  1. Run 'start-all.bat' to start both servers
echo  2. Access frontend at http://localhost:3000
echo  3. Access admin panel at http://localhost:8000/admin/
echo  4. Upload data files in the admin panel
echo.
echo Optional: Configure frontend API endpoint
echo  - Edit frontend\src\api\client.ts
echo  - Update API_BASE_URL if needed (default: http://localhost:8000/api)
echo.
pause
