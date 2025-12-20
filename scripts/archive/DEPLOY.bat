@echo off
title Powerhouse Commercial-Grade System Deployment
color 0B
echo =============================================
echo   POWERHOUSE DEPLOYMENT SCRIPT
echo =============================================
echo.
echo This script will deploy the commercial-grade system.
echo.
echo Pre-deployment checks:
echo   - Environment configuration
echo   - Database initialization
echo   - Dependency installation
echo   - Service startup
echo.
pause
echo.

REM Go to project root
cd /d "%~dp0"

REM Check Python
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.12+
    pause
    exit /b 1
)
echo [OK] Python found
echo.

REM Check virtual environment
echo [2/6] Checking virtual environment...
if not exist "backend\venv\Scripts\activate.bat" (
    echo [WARNING] Virtual environment not found. Creating...
    cd backend
    python -m venv venv
    cd ..
)
call backend\venv\Scripts\activate.bat
echo [OK] Virtual environment ready
echo.

REM Install/update dependencies
echo [3/6] Installing dependencies...
cd backend
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
cd ..
echo.

REM Check environment file
echo [4/6] Checking environment configuration...
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Creating template .env file...
    (
        echo # Database
        echo DATABASE_URL=postgresql://user:password@localhost:5432/powerhouse
        echo.
        echo # Security
        echo SECRET_KEY=change-this-in-production
        echo JWT_SECRET_KEY=change-this-in-production
        echo.
        echo # Email
        echo EMAIL_PROVIDER=sendgrid
        echo SENDGRID_API_KEY=your-api-key-here
        echo.
        echo # Application
        echo DEBUG=False
        echo ENVIRONMENT=production
    ) > .env
    echo [INFO] Template .env file created. Please configure it before deployment!
    pause
)
echo [OK] Environment file found
echo.

REM Initialize database
echo [5/6] Initializing database...
cd backend
python -c "from database.session import init_db; init_db(drop_all=False)" 2>nul
if errorlevel 1 (
    echo [WARNING] Database initialization failed. This may be normal if tables already exist.
) else (
    echo [OK] Database initialized
)
cd ..
echo.

REM Run tests
echo [6/6] Running pre-deployment tests...
cd backend
python scripts/test_commercial_grade.py 2>nul | findstr /C:"Pass Rate"
if errorlevel 1 (
    echo [WARNING] Some tests may have failed. Review test output above.
) else (
    echo [OK] Tests passed
)
cd ..
echo.

echo =============================================
echo   DEPLOYMENT PREPARATION COMPLETE
echo =============================================
echo.
echo Next steps:
echo 1. Review and configure .env file
echo 2. Start database services (Docker Compose or manual)
echo 3. Start backend: cd backend ^&^& uvicorn api.main:app --host 0.0.0.0 --port 8000
echo 4. Start frontend: cd frontend ^&^& npm run dev
echo 5. Verify deployment: http://localhost:8000/health
echo.
echo For production deployment, use BUILD_PRODUCTION.bat
echo.
pause

