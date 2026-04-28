@echo off
title AI Content Protection System - Launcher
echo ============================================================
echo   AI Content Protection System
echo ============================================================
echo.
echo   Backend  : http://localhost:8000
echo   Frontend : http://localhost:3000
echo   API Docs : http://localhost:8000/docs
echo.
echo   Starting servers...
echo ============================================================

:: Start backend in a new window
start "CPS Backend (port 8000)" cmd /k "cd /d d:\AI_Solution\backend && .\venv\Scripts\python.exe app.py"

:: Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

:: Start frontend in a new window
start "CPS Frontend (port 3000)" cmd /k "cd /d d:\AI_Solution\frontend && python -m http.server 3000"

:: Wait a moment then open browser
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo.
echo   Both servers started! Browser opening...
echo   Close this window anytime - servers run independently.
echo.
pause
