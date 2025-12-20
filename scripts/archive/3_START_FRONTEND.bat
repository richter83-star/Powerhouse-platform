@echo off
title Powerhouse - Frontend
color 0C
echo ========================================
echo   POWERHOUSE FRONTEND
echo ========================================
echo.
cd frontend\app

REM If dependencies are missing, install them automatically
if not exist "node_modules\" (
    echo [INFO] Frontend dependencies not found. Installing now...
    echo.
    call npm install --legacy-peer-deps
    if errorlevel 1 (
        echo [ERROR] npm install failed. Check the error above.
        pause
        exit /b 1
    )
)

echo.
echo Starting Next.js development server...
echo.
echo Frontend will be available at:
echo   http://localhost:3000  (Next.js will auto-bump to 3001, 3002, etc if needed)
echo.

npm run dev

echo.
echo Frontend dev server stopped.
pause
