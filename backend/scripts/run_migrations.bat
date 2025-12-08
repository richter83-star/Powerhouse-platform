@echo off
REM Run database migrations using Alembic

cd /d "%~dp0\.."

echo Running database migrations...

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run migrations
python -m alembic upgrade head

if %ERRORLEVEL% EQU 0 (
    echo Migrations completed successfully!
) else (
    echo Migration failed!
    exit /b %ERRORLEVEL%
)

