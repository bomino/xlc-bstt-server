@echo off
REM BSTT Frontend Startup Script
REM This script starts the React frontend development server

echo ========================================
echo BSTT Frontend Server Startup
echo ========================================
echo.

cd /d "%~dp0frontend"

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing npm dependencies...
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install npm dependencies
        echo Make sure Node.js and npm are installed
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo Starting React Development Server
echo Frontend: http://localhost:3000
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the development server
call npm start
