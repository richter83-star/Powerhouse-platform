@echo off
setlocal enabledelayedexpansion
REM ============================================================================
REM Powerhouse - Clean Reinstall Script
REM ============================================================================
REM This script performs a complete uninstall followed by a fresh installation.
REM Use this when you want to completely reset Powerhouse.
REM ============================================================================

for %%I in ("%~dp0\..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"

REM Logging helper function
set "LOG_FILE=%ROOT%\.cursor\debug.log"
powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:ENTRY';message='Script entry';data=@{cd='%~dp0'};sessionId='debug-session';runId='run1';hypothesisId='A'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

REM Change to repo root
powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:16';message='After cd';data=@{currentDir='%CD%'};sessionId='debug-session';runId='run1';hypothesisId='A'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

echo.
echo [DEBUG] Script started at: %DATE% %TIME%
echo [DEBUG] Current directory: %CD%
echo.
echo ============================================================================
echo Powerhouse - Clean Reinstall
echo ============================================================================
echo.
echo This will:
echo 1. Uninstall Powerhouse completely
echo 2. Clean up all artifacts
echo 3. Perform a fresh installation
echo.
echo WARNING: This will delete all database data unless you choose to preserve it!
echo.

:confirm_loop
powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:35';message='Before confirm prompt';data=@{step='confirm_loop'};sessionId='debug-session';runId='run1';hypothesisId='B'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
set /p CONFIRM="Are you sure you want to proceed? (yes/no): "
powershell -Command "$logPath = '%LOG_FILE%'; $confirm = '%CONFIRM%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:37';message='User input received';data=@{confirm=$confirm};sessionId='debug-session';runId='run1';hypothesisId='B'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

if "%CONFIRM%"=="" (
    powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:40';message='Empty input detected';data=@{action='loop_again'};sessionId='debug-session';runId='run1';hypothesisId='B'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    echo Please enter 'yes' or 'no'
    goto confirm_loop
)

if /i "%CONFIRM%"=="yes" (
    powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:46';message='User confirmed yes';data=@{action='goto_proceed'};sessionId='debug-session';runId='run1';hypothesisId='B'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    goto proceed
)
if /i "%CONFIRM%"=="no" (
    powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:50';message='User cancelled';data=@{action='exit'};sessionId='debug-session';runId='run1';hypothesisId='B'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    echo Reinstall cancelled.
    pause
    exit /b 0
)

powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:56';message='Invalid input';data=@{confirm='%CONFIRM%';action='loop_again'};sessionId='debug-session';runId='run1';hypothesisId='B'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
echo Invalid input. Please enter 'yes' or 'no'
goto confirm_loop

:proceed
powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:61';message='Entered proceed section';data=@{step='uninstall'};sessionId='debug-session';runId='run1';hypothesisId='A'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

REM ============================================================================
REM Step 1: Uninstall
REM ============================================================================

echo.
echo ============================================================================
echo Step 1: Uninstalling Powerhouse...
echo ============================================================================
echo.
echo This will:
echo - Stop all services
echo - Remove Docker containers
echo - Uninstall Python packages
echo - Remove Node.js packages
echo - Clean up artifacts
echo.

:preserve_data_loop
powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:81';message='Before preserve_data prompt';data=@{step='preserve_data_loop'};sessionId='debug-session';runId='run1';hypothesisId='C'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
set /p PRESERVE_DATA_OPTION="Do you want to preserve database data? (yes/no - default: no): "
powershell -Command "$logPath = '%LOG_FILE%'; $preserve = '%PRESERVE_DATA_OPTION%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:83';message='Preserve data input received';data=@{preserveDataOption=$preserve};sessionId='debug-session';runId='run1';hypothesisId='C'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

if "%PRESERVE_DATA_OPTION%"=="" (
    powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:86';message='Empty preserve input, using default';data=@{action='set_default_no'};sessionId='debug-session';runId='run1';hypothesisId='C'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    echo Using default: no (database data will be deleted)
    set "PRESERVE_DATA_OPTION=no"
)

powershell -Command "$logPath = '%LOG_FILE%'; $preserve = '%PRESERVE_DATA_OPTION%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:91';message='Before conditional check';data=@{preserveDataOption=$preserve};sessionId='debug-session';runId='run1';hypothesisId='C'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

if /i "%PRESERVE_DATA_OPTION%"=="yes" (
    powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:93';message='Conditional: going to preserve_yes';data=@{action='goto_preserve_yes'};sessionId='debug-session';runId='run1';hypothesisId='C'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    goto preserve_yes
)
if /i "%PRESERVE_DATA_OPTION%"=="no" (
    powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:96';message='Conditional: going to preserve_no';data=@{action='goto_preserve_no'};sessionId='debug-session';runId='run1';hypothesisId='C'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    goto preserve_no
)

powershell -Command "$logPath = '%LOG_FILE%'; $preserve = '%PRESERVE_DATA_OPTION%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:99';message='Invalid input detected';data=@{preserveDataOption=$preserve;action='loop_again'};sessionId='debug-session';runId='run1';hypothesisId='C'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
echo Invalid input. Please enter 'yes' or 'no' (or press Enter for default: no)
goto preserve_data_loop

:preserve_yes
powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:98';message='Branch: preserve_yes';data=@{action='call_uninstall_preserve'};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
echo.
echo [INFO] Calling uninstall with data preservation...
echo [INFO] Command: UNINSTALL.bat auto preserve_data
echo.
powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:110';message='About to call UNINSTALL.bat preserve';data=@{beforeCall='true'};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

REM Save current directory before calling UNINSTALL.bat
set "SAVED_DIR=%CD%"

REM Call UNINSTALL.bat and capture error code
REM Always continue execution even if UNINSTALL.bat fails
call "%ROOT%\UNINSTALL.bat" auto preserve_data
set "UNINSTALL_RESULT=!ERRORLEVEL!"
if "!UNINSTALL_RESULT!"=="" set "UNINSTALL_RESULT=0"

REM Ensure we're still in the right directory
cd /d "!SAVED_DIR!" 2>nul

REM Set default if ERRORLEVEL was not captured
if "!UNINSTALL_RESULT!"=="" set "UNINSTALL_RESULT=0"
if "!UNINSTALL_RESULT!"=="-1073741510" set "UNINSTALL_RESULT=1"

powershell -Command "$logPath = '%LOG_FILE%'; $result = '!UNINSTALL_RESULT!'; $currentDir = '%CD%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:118';message='After UNINSTALL.bat call';data=@{errorLevel=$result;uninstallResult=$result;preserveData='yes';currentDir=$currentDir};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

if !UNINSTALL_RESULT! NEQ 0 (
    powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:121';message='UNINSTALL.bat returned error';data=@{errorLevel='!UNINSTALL_RESULT!'};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    echo [WARN] UNINSTALL.bat returned error code !UNINSTALL_RESULT!
    echo [WARN] Continuing with reinstall anyway...
)

echo [DEBUG] UNINSTALL.bat completed, continuing...
goto uninstall_done

:preserve_no
powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:112';message='Branch: preserve_no';data=@{action='call_uninstall_delete'};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
echo.
echo [INFO] Calling uninstall (data will be deleted)...
echo [INFO] Command: UNINSTALL.bat auto
echo.
powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:118';message='Before echo statements';data=@{step='before_call'};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:125';message='About to call UNINSTALL.bat';data=@{beforeCall='true'};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

REM Save current directory before calling UNINSTALL.bat
set "SAVED_DIR=%CD%"

REM Call UNINSTALL.bat and capture error code
REM Always continue execution even if UNINSTALL.bat fails
call "%ROOT%\UNINSTALL.bat" auto
set "UNINSTALL_RESULT=!ERRORLEVEL!"
if "!UNINSTALL_RESULT!"=="" set "UNINSTALL_RESULT=0"

REM Ensure we're still in the right directory
cd /d "!SAVED_DIR!" 2>nul

REM Set default if ERRORLEVEL was not captured
if "!UNINSTALL_RESULT!"=="" set "UNINSTALL_RESULT=0"
if "!UNINSTALL_RESULT!"=="-1073741510" set "UNINSTALL_RESULT=1"

powershell -Command "$logPath = '%LOG_FILE%'; $result = '!UNINSTALL_RESULT!'; $currentDir = '%CD%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:135';message='After UNINSTALL.bat call';data=@{errorLevel=$result;uninstallResult=$result;preserveData='no';currentDir=$currentDir};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

if !UNINSTALL_RESULT! NEQ 0 (
    powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:138';message='UNINSTALL.bat returned error';data=@{errorLevel='!UNINSTALL_RESULT!'};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    echo [WARN] UNINSTALL.bat returned error code !UNINSTALL_RESULT!
    echo [WARN] Continuing with reinstall anyway...
)

echo [DEBUG] UNINSTALL.bat completed, continuing...

:uninstall_done
powershell -Command "$logPath = '%LOG_FILE%'; $result = '!UNINSTALL_RESULT!'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:119';message='Uninstall done';data=@{uninstallResult=$result};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
echo.
echo ============================================================================
echo [INFO] Uninstall script finished. Return code: %UNINSTALL_RESULT%
echo ============================================================================
echo.

if !UNINSTALL_RESULT! NEQ 0 (
    powershell -Command "$logPath = '%LOG_FILE%'; $result = '!UNINSTALL_RESULT!'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:127';message='Uninstall error detected';data=@{errorCode=$result;action='pause'};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    echo [ERROR] Uninstall returned error code !UNINSTALL_RESULT!
    echo The uninstall may have had issues, but continuing anyway...
    echo.
    pause
)

REM Error checking moved to after the call, using UNINSTALL_RESULT variable

REM ============================================================================
REM Step 2: Pull Latest Code (if using Git)
REM ============================================================================

echo.
echo ============================================================================
echo Step 2: Updating code...
echo ============================================================================
echo.

if exist ".git" (
    powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:147';message='Git repo found';data=@{action='git_pull'};sessionId='debug-session';runId='run1';hypothesisId='E'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    echo [INFO] Pulling latest code from Git...
    git pull origin main
    set "GIT_RESULT=!ERRORLEVEL!"
    powershell -Command "$logPath = '%LOG_FILE%'; $result = '%GIT_RESULT%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:151';message='After git pull';data=@{errorLevel=$result};sessionId='debug-session';runId='run1';hypothesisId='E'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    
    if errorlevel 1 (
        echo [WARN] Git pull failed. Continuing with current code...
        echo [WARN] This is OK if you're already up to date or not connected to remote.
    ) else (
        echo [OK] Git pull successful.
    )
) else (
    powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:160';message='No git repo';data=@{action='skip_git'};sessionId='debug-session';runId='run1';hypothesisId='E'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    echo [INFO] No Git repository found. Using current code...
)

echo [OK] Step 2 complete.
echo.

REM ============================================================================
REM Step 3: Build and start via Docker
REM ============================================================================

echo.
echo ============================================================================
echo Step 3: Installing Powerhouse...
echo ============================================================================
echo.

if not exist "%ROOT%\docker-quickstart.bat" (
    powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:178';message='docker-quickstart.bat not found';data=@{currentDir='%CD%';action='exit'};sessionId='debug-session';runId='run1';hypothesisId='E'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    echo [ERROR] docker-quickstart.bat not found!
    echo [ERROR] Please make sure you're in the Powerhouse repo root.
    echo [ERROR] Current directory: %CD%
    pause
    exit /b 1
)

powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:186';message='Before docker-quickstart call';data=@{action='call_docker_quickstart'};sessionId='debug-session';runId='run1';hypothesisId='E'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
echo [INFO] Building images and starting services...
echo [INFO] This may take 5-10 minutes...
echo.

call "%ROOT%\docker-quickstart.bat" --build
set "START_RESULT=!ERRORLEVEL!"
if "!START_RESULT!"=="" set "START_RESULT=0"
powershell -Command "$logPath = '%LOG_FILE%'; $result = '!START_RESULT!'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:253';message='After docker-quickstart call';data=@{errorLevel=$result};sessionId='debug-session';runId='run1';hypothesisId='E'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

echo.
echo [INFO] Startup script finished. Return code: !START_RESULT!
echo.

if !START_RESULT! NEQ 0 (
    echo [ERROR] Startup returned error code !START_RESULT!
    echo [ERROR] Please check the errors above.
    echo.
    echo Do you want to continue anyway? (yes/no)
    set /p CONTINUE_ANYWAY="> "
    if /i not "!CONTINUE_ANYWAY!"=="yes" (
        pause
        exit /b 1
    )
    echo [WARN] Continuing despite installation errors...
)

REM ============================================================================
REM Step 4: Optional restart
REM ============================================================================

echo.
echo ============================================================================
echo Step 4: Optional restart...
echo ============================================================================
echo.

:start_services_loop
powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:222';message='Before start_services prompt';data=@{step='start_services_loop'};sessionId='debug-session';runId='run1';hypothesisId='B'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
set /p START_SERVICES="Restart Powerhouse services now? (yes/no): "
powershell -Command "$logPath = '%LOG_FILE%'; $start = '%START_SERVICES%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:224';message='Start services input received';data=@{startServices=$start};sessionId='debug-session';runId='run1';hypothesisId='B'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

if "%START_SERVICES%"=="" (
    powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:227';message='Empty start_services input';data=@{action='loop_again'};sessionId='debug-session';runId='run1';hypothesisId='B'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    echo Please enter 'yes' or 'no'
    goto start_services_loop
)

if /i "%START_SERVICES%"=="yes" (
    echo.
    echo Restarting Powerhouse...
    call "%ROOT%\docker-quickstart.bat"
    goto services_done
)

if /i "%START_SERVICES%"=="no" (
    echo.
    echo Services already started in Step 3.
    goto services_done
)

echo Invalid input. Please enter 'yes' or 'no'
goto start_services_loop

:services_done
powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='CLEAN_REINSTALL.bat:249';message='Script completion';data=@{action='success'};sessionId='debug-session';runId='run1';hypothesisId='A'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

echo.
echo ============================================================================
echo Clean Reinstall Complete!
echo ============================================================================
echo.
echo Powerhouse has been:
echo - Uninstalled completely
echo - Reinstalled with latest code
echo - All dependencies updated
echo.
echo All 10 advanced AI features are enabled by default!
echo.
echo Access Powerhouse at:
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:8001
echo - API Docs: http://localhost:8001/docs
echo.
echo ============================================================================

pause

