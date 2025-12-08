@echo off
title Powerhouse - Diagnostics
color 0F
echo ================================================================
echo   POWERHOUSE DIAGNOSTICS
echo ================================================================
echo.
echo This will check your system setup and folder structure
echo.
pause

echo.
echo [1] Current Location
echo ================================================================
echo Batch file location: %~dp0
echo Current directory: %CD%
echo.

echo.
echo [2] Folder Structure
echo ================================================================
echo Checking if required folders exist...
echo.

if exist "backend" (
    echo [OK] backend folder EXISTS
    echo     Location: %CD%\backend
) else (
    echo [ERROR] backend folder NOT FOUND
    echo     Expected: %CD%\backend
)

if exist "frontend" (
    echo [OK] frontend folder EXISTS
    echo     Location: %CD%\frontend
) else (
    echo [ERROR] frontend folder NOT FOUND
    echo     Expected: %CD%\frontend
)

if exist "docker-compose.yml" (
    echo [OK] docker-compose.yml EXISTS
) else (
    echo [ERROR] docker-compose.yml NOT FOUND
)

echo.
echo Current folder contents:
dir /b

echo.
echo.
echo [3] System Requirements
echo ================================================================
echo.

echo Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
) else (
    echo [OK] Python is available
    echo Location:
    where python
)

echo.
echo Checking Node.js...
node --version
if errorlevel 1 (
    echo [ERROR] Node.js not found in PATH
) else (
    echo [OK] Node.js is available
    echo Location:
    where node
)

echo.
echo Checking npm...
npm --version
if errorlevel 1 (
    echo [ERROR] npm not found in PATH
) else (
    echo [OK] npm is available
)

echo.
echo Checking Docker...
docker --version
if errorlevel 1 (
    echo [ERROR] Docker not found in PATH
) else (
    echo [OK] Docker is installed
    docker ps >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker Desktop is NOT running
    ) else (
        echo [OK] Docker Desktop is running
    )
)

echo.
echo.
echo [4] Testing Folder Access
echo ================================================================
echo.

echo Testing backend folder access...
cd backend >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Cannot enter backend folder
) else (
    echo [OK] Successfully entered backend folder
    echo Current directory: %CD%
    cd ..
)

echo.
echo Testing frontend folder access...
cd frontend >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Cannot enter frontend folder
) else (
    echo [OK] Successfully entered frontend folder
    echo Current directory: %CD%
    cd ..
)

echo.
echo.
echo [5] Backend Status
echo ================================================================
echo.

if exist "backend\venv" (
    echo [OK] Python virtual environment EXISTS
    echo     Backend is installed
) else (
    echo [INFO] Python virtual environment NOT FOUND
    echo     Backend needs to be installed
)

if exist "backend\requirements.txt" (
    echo [OK] requirements.txt EXISTS
) else (
    echo [ERROR] requirements.txt NOT FOUND
)

echo.
echo.
echo [6] Frontend Status
echo ================================================================
echo.

if exist "frontend\app\node_modules" (
    echo [OK] Node modules EXISTS
    echo     Frontend is installed
) else (
    echo [INFO] Node modules NOT FOUND
    echo     Frontend needs to be installed
)

if exist "frontend\app\package.json" (
    echo [OK] package.json EXISTS
) else (
    echo [ERROR] package.json NOT FOUND
)

echo.
echo.
echo ================================================================
echo   DIAGNOSTICS COMPLETE
echo ================================================================
echo.
echo If you see any [ERROR] messages above, those need to be fixed
echo before installation can succeed.
echo.
echo Common fixes:
echo - Extract the ZIP file to a simple path like C:\Powerhouse
echo - Run as Administrator
echo - Make sure Python and Node.js are in PATH
echo - Start Docker Desktop before installing
echo.
pause
