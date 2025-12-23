@echo off
title Powerhouse Production Server
color 0A
echo =============================================
echo   POWERHOUSE PRODUCTION SERVER
echo =============================================
echo.
echo Starting production services...
echo.

REM Go to project root
cd /d "%~dp0"

REM Activate virtual environment
if exist "backend\venv\Scripts\activate.bat" (
    call backend\venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found!
    echo Please run DEPLOY.bat first.
    pause
    exit /b 1
)

REM Check if database is accessible
echo Checking database connection...
cd backend
python -c "from database.session import get_engine; engine = get_engine(); print('Database connected')" 2>nul
if errorlevel 1 (
    echo [WARNING] Database connection failed. Please check your .env configuration.
    echo Continuing anyway...
)
cd ..

REM Start backend server
echo.
echo Starting backend server on http://localhost:8000
echo Press Ctrl+C to stop
echo.
cd backend
start "Powerhouse Backend" cmd /k "uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"
cd ..

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend (if built)
if exist "frontend\.next" (
    echo Starting frontend server...
    cd frontend
    start "Powerhouse Frontend" cmd /k "npm start"
    cd ..
) else (
    echo [INFO] Frontend not built. Run 'npm run build' in frontend directory first.
)

echo.
echo =============================================
echo   SERVICES STARTED
echo =============================================
echo.
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Health: http://localhost:8000/health
echo.
echo Frontend: http://localhost:3000 (if started)
echo.
echo Services are running in separate windows.
echo Close those windows to stop the services.
echo.
pause

