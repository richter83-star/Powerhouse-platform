@echo off
title Build Powerhouse Installer
color 0B
echo =============================================
echo   BUILD POWERHOUSE INSTALLER
echo =============================================
echo.
echo This will create:
echo   - Powerhouse Setup 1.0.0.exe (Installer)
echo   - Powerhouse.exe (Application Launcher)
echo.
echo Output location: electron-app\dist\
echo.
pause
echo.

cd /d "%~dp0"

REM Check prerequisites
echo [1/5] Checking prerequisites...
where node >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    pause
    exit /b 1
)
echo [OK] Node.js found

where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] npm not found!
    pause
    exit /b 1
)
echo [OK] npm found
echo.

REM Create icon if missing
echo [1.5/5] Checking for icon file...
cd electron-app
if not exist "build\icon.ico" (
    echo [INFO] Creating placeholder icon...
    if exist "create-icon.js" (
        node create-icon.js
        if exist "build\icon.ico" (
            echo [OK] Icon created successfully
        ) else (
            echo [WARNING] Icon creation failed
        )
    ) else (
        echo [WARNING] create-icon.js not found
        echo [INFO] You may need to create build\icon.ico manually
    )
) else (
    echo [OK] Icon file already exists
)
cd ..

REM Install Electron dependencies
echo [2/5] Installing Electron dependencies...
cd electron-app
if not exist "node_modules" (
    echo Installing packages...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        cd ..
        pause
        exit /b 1
    )
)
echo [OK] Dependencies installed
echo.

REM Build frontend (if needed)
echo [3/5] Checking frontend build...
cd ..\frontend\app
if not exist ".next" (
    echo [INFO] Frontend not built. Building now...
    call npm install --silent
    call npm run build
    if errorlevel 1 (
        echo [WARNING] Frontend build failed. Continuing anyway...
    )
)
cd ..\..
echo.

REM Build Electron app
echo [4/5] Building Electron installer...
cd electron-app
echo This may take 10-15 minutes...
echo.
call npm run dist-win
if errorlevel 1 (
    echo [ERROR] Build failed!
    cd ..
    pause
    exit /b 1
)
cd ..
echo.

REM Verify output
echo [5/5] Verifying build output...
set INSTALLER_PATH=electron-app\dist\Powerhouse Setup 1.0.0.exe
set LAUNCHER_PATH=electron-app\dist\win-unpacked\Powerhouse.exe

if exist "%INSTALLER_PATH%" (
    echo.
    echo =============================================
    echo   BUILD SUCCESSFUL!
    echo =============================================
    echo.
    echo Installer created:
    echo   %INSTALLER_PATH%
    for %%A in ("%INSTALLER_PATH%") do (
        set /a SIZE_MB=%%~zA/1048576
        echo   Size: ~!SIZE_MB! MB
    )
    echo.
) else (
    echo [WARNING] Installer not found at expected location
    echo Expected: %INSTALLER_PATH%
    echo.
    echo Checking dist directory...
    dir electron-app\dist\*.exe 2>nul
    echo.
)

if exist "%LAUNCHER_PATH%" (
    echo Launcher created:
    echo   %LAUNCHER_PATH%
    for %%A in ("%LAUNCHER_PATH%") do (
        set /a SIZE_MB=%%~zA/1048576
        echo   Size: ~!SIZE_MB! MB
    )
    echo.
) else (
    echo [WARNING] Launcher not found at expected location
    echo Expected: %LAUNCHER_PATH%
    echo.
)

echo =============================================
echo   BUILD COMPLETE
echo =============================================
echo.
echo Files are in: electron-app\dist\
echo.
echo To test:
echo   1. Run the installer: %INSTALLER_PATH%
echo   2. Or run launcher directly: %LAUNCHER_PATH%
echo.
pause

