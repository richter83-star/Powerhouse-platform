@echo off
title Quick Deploy - Powerhouse
color 0E
echo =============================================
echo   QUICK DEPLOY - POWERHOUSE
echo =============================================
echo.
echo This will quickly deploy the system for testing.
echo.
pause

cd /d "%~dp0"

REM Activate venv
if exist "backend\venv\Scripts\activate.bat" (
    call backend\venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt --quiet
    cd ..
)

REM Initialize database
echo Initializing database...
cd backend
python scripts/init_database.py
cd ..

REM Start services
echo.
echo Starting services...
echo.
call START_PRODUCTION.bat

