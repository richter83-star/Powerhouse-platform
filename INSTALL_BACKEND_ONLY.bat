@echo off
title Powerhouse - Backend Dependency Installer
color 0A
echo ========================================
echo   Installing Backend (Python) Environment
echo ========================================
echo.

cd backend

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [SUCCESS] Backend is ready!
echo You can now run 1_START_DATABASE.bat
echo.
pause
