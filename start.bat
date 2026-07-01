@echo off
title Fund-Stock Analyzer

echo ========================================
echo  Fund-Stock Analyzer
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] Starting backend...
start "Fund-Backend" cmd /c "cd /d "%~dp0backend" & python run.py"

timeout /t 3 /nobreak >nul

echo [2/2] Starting frontend...
start "Fund-Frontend" cmd /c "cd /d "%~dp0frontend" & npm run dev"

echo.
echo ========================================
echo.
echo  Backend: http://localhost:8000
echo  API:     http://localhost:8000/docs
echo  Frontend:http://localhost:5173
echo.
echo  Close Backend/Frontend windows to stop.
echo ========================================
echo.
pause
