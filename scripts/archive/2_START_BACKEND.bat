@echo off
title Powerhouse - Backend API
color 0B
echo ========================================
echo   POWERHOUSE BACKEND API
echo ========================================
echo.
cd backend

REM -----------------------------------------------------------------
REM 1) Check that python is available
REM -----------------------------------------------------------------
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo Please install Python 3.12 and try again.
    echo.
    pause
    exit /b 1
)

REM -----------------------------------------------------------------
REM 2) Create virtual environment if it does not exist
REM -----------------------------------------------------------------
if not exist "venv\Scripts\python.exe" (
    echo [INFO] Python virtual environment not found. Creating one at .\venv ...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        echo Check your Python install and try again.
        echo.
        pause
        exit /b 1
    )
)

REM -----------------------------------------------------------------
REM 3) Activate virtual environment
REM -----------------------------------------------------------------
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM -----------------------------------------------------------------
REM 4) Install backend dependencies if needed
REM    (we just test for FastAPI as a proxy)
REM -----------------------------------------------------------------
python -c "import fastapi" >nul 2>nul
if errorlevel 1 (
    echo [INFO] Backend dependencies not detected. Installing from requirements.txt...
    echo.
    python -m pip install --upgrade pip
    if errorlevel 1 (
        echo [ERROR] Failed to upgrade pip.
        echo.
        pause
        exit /b 1
    )
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install backend dependencies.
        echo Check requirements.txt and your internet connection.
        echo.
        pause
        exit /b 1
    )
)

REM -----------------------------------------------------------------
REM 5) Start the backend server
REM -----------------------------------------------------------------
echo.
echo [INFO] Starting backend server on port 8001...
echo       Health check: http://localhost:8001/health
echo.

uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload

echo.
echo Backend server stopped.
pause
