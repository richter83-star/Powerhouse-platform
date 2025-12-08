@echo off
title Python Test
color 0F
echo ================================================================
echo   PYTHON TEST
echo ================================================================
echo.

echo Testing Python installation...
echo.

echo Python version:
python --version
echo.

echo Python location:
where python
echo.

echo Pip version:
pip --version
echo.

echo Testing venv creation...
cd backend
if exist "test_venv\" rmdir /s /q test_venv
python -m venv test_venv
if exist "test_venv\" (
    echo [OK] Virtual environment created successfully!
    rmdir /s /q test_venv
) else (
    echo [ERROR] Failed to create virtual environment
)
cd ..

echo.
echo Test complete!
echo.
pause
