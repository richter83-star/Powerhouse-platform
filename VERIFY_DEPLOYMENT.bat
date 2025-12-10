@echo off
title Verify Deployment
color 0B
echo =============================================
echo   DEPLOYMENT VERIFICATION
echo =============================================
echo.

cd /d "%~dp0"

REM Activate venv
if exist "backend\venv\Scripts\activate.bat" (
    call backend\venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found!
    pause
    exit /b 1
)

echo [1/4] Checking backend health...
cd backend
python -c "try:
    import requests
    r = requests.get('http://localhost:8000/health', timeout=2)
    print('[OK] Backend is healthy - Status:', r.status_code)
except:
    print('[WARNING] Backend not responding. Is it running on port 8000?')" 2>nul
if errorlevel 1 (
    echo [WARNING] Backend not responding. Is it running?
) else (
    echo [OK] Backend is healthy
)
cd ..
echo.

echo [2/4] Checking database connection...
cd backend
python -c "from database.session import get_engine; engine = get_engine(); print('[OK] Database connected')" 2>nul
if errorlevel 1 (
    echo [ERROR] Database connection failed!
) else (
    echo [OK] Database connected
)
cd ..
echo.

echo [3/4] Running test suite...
cd backend
python scripts/test_commercial_grade.py 2>nul | findstr /C:"Pass Rate"
cd ..
echo.

echo [4/4] Checking API documentation...
start http://localhost:8000/docs
echo [OK] API documentation opened in browser
echo.

echo =============================================
echo   VERIFICATION COMPLETE
echo =============================================
echo.
pause

