@echo off
REM BSTT Application Stop Script
REM This script stops all running backend and frontend processes

echo ========================================
echo BSTT Application Shutdown
echo ========================================
echo.

REM Kill Django/Python processes running on port 8000
echo Stopping backend server (port 8000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING"') do (
    echo Killing process %%a
    taskkill /PID %%a /F >nul 2>&1
)

REM Kill Node/React processes running on port 3000
echo Stopping frontend server (port 3000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING"') do (
    echo Killing process %%a
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo All servers stopped.
echo.
pause
