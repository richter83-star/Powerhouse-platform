@echo off
title Commercial-Grade System Testing
color 0A
echo =============================================
echo   COMMERCIAL-GRADE SYSTEM TEST SUITE
echo =============================================
echo.
echo This script will test ALL commercial features:
echo.
echo Phase 1 (Critical):
echo   - License Key Activation System
echo   - Usage Limits Enforcement
echo   - Email Notification System
echo   - Customer Support Integration
echo.
echo Phase 2 (Post-Launch):
echo   - Onboarding Flow
echo   - SLA Monitoring & Reporting
echo   - Advanced Error Recovery
echo   - Compliance & Certifications
echo.
echo Phase 3 (Enhancements):
echo   - White-Label Options
echo   - SSO/SAML Integration
echo   - Advanced Security Features
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

REM Run comprehensive test script
echo Running comprehensive commercial-grade tests...
echo.
python backend\scripts\test_commercial_grade.py

echo.
echo =============================================
echo   TESTING COMPLETE
echo =============================================
echo.
echo Review the test results above.
echo.
echo Next steps:
echo 1. Review any failed tests
echo 2. Fix critical issues
echo 3. Test manually using the test guides
echo 4. Deploy to production
echo.
pause

