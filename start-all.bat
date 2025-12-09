@echo off
REM BSTT Complete Application Startup Script
REM This script starts both backend and frontend servers in separate windows

echo ========================================
echo BSTT Application Startup
echo ========================================
echo.
echo Starting backend and frontend servers...
echo.

cd /d "%~dp0"

REM Start backend in new window
start "BSTT Backend Server" cmd /k "%~dp0start-backend.bat"

REM Wait 3 seconds for backend to initialize
timeout /t 3 /nobreak >nul

REM Start frontend in new window
start "BSTT Frontend Server" cmd /k "%~dp0start-frontend.bat"

echo.
echo ========================================
echo Both servers are starting...
echo.
echo Backend API: http://localhost:8000/api/
echo Admin Panel: http://localhost:8000/admin/
echo Frontend:    http://localhost:3000
echo.
echo Two command windows will open:
echo  - BSTT Backend Server
echo  - BSTT Frontend Server
echo.
echo Close those windows to stop the servers
echo ========================================
echo.

pause
