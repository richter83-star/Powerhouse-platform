@echo off
title Powerhouse Enterprise - Launcher
color 0B

echo ============================================
echo        POWERHOUSE ENTERPRISE - LAUNCHER
echo ============================================
echo.

REM Go to project root
cd /d "%~dp0"

REM ---- 1. Start database ---------------------------------------
echo [1/3] Starting PostgreSQL database...

if exist "1_START_DATABASE.bat" (
    call "1_START_DATABASE.bat"
) else (
    echo [WARN] 1_START_DATABASE.bat not found, assuming DB is already running...
)

echo Waiting 8 seconds for database to be ready...
timeout /t 8 /nobreak >nul

REM ---- 2. Start backend ----------------------------------------
echo.
echo [2/3] Starting backend (FastAPI)...

if exist "2_START_BACKEND.bat" (
    start "" "2_START_BACKEND.bat"
) else (
    echo [ERROR] 2_START_BACKEND.bat not found!
    echo Backend will NOT start automatically.
)

echo Waiting 6 seconds for backend to come up...
timeout /t 6 /nobreak >nul

REM ---- 3. Start frontend ---------------------------------------
echo.
echo [3/3] Starting frontend (Next.js)...

if exist "3_START_FRONTEND.bat" (
    start "" "3_START_FRONTEND.bat"
) else (
    echo [ERROR] 3_START_FRONTEND.bat not found!
    echo Frontend will NOT start automatically.
)

echo.
echo ============================================
echo   Powerhouse Enterprise launch complete.
echo   If your browser didn't open automatically,
echo   open:  http://localhost:3000
echo ============================================
echo.

pause
