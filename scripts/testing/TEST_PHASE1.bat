@echo off
title Phase 1 Testing
color 0A
echo =============================================
echo   PHASE 1 COMMERCIAL FEATURES TESTING
echo =============================================
echo.
echo This script will test:
echo 1. License Key Activation System
echo 2. Usage Limits Enforcement
echo 3. Email Notification System
echo 4. Customer Support Integration
echo.
pause
echo.

REM Go to project root
for %%I in ("%~dp0\..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"

REM Activate virtual environment
if exist "backend\venv\Scripts\activate.bat" (
    call backend\venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found. Using system Python.
)

REM Run test script
echo Running Phase 1 tests...
echo.
python backend\scripts\test_phase1.py

echo.
echo =============================================
echo   TESTING COMPLETE
echo =============================================
echo.
echo Review the test results above.
echo.
echo Next steps:
echo 1. Check for any failed tests
echo 2. Review warnings
echo 3. Test manually using PHASE1_TEST_GUIDE.md
echo.
pause

