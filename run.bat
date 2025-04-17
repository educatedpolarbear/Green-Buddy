@echo off
setlocal enabledelayedexpansion

set "BASE_DIR=%CD%"
echo Starting application...

cd "%BASE_DIR%\backend"
start python app.py
if %ERRORLEVEL% neq 0 (
    echo Backend failed to start with exit code %ERRORLEVEL%
    cd "%BASE_DIR%"
    pause
    exit /b 1
)

echo Backend started successfully!

cd "%BASE_DIR%\frontend"
echo Building frontend...
call npm run build
if %ERRORLEVEL% neq 0 (
    echo Frontend build failed with exit code %ERRORLEVEL%
    cd "%BASE_DIR%"
    pause
    exit /b 1
)

echo Frontend built successfully!
cls

echo Starting frontend...
call npm run start
if %ERRORLEVEL% neq 0 (
    echo Frontend failed to start with exit code %ERRORLEVEL%
    cd "%BASE_DIR%"
    pause
    exit /b 1
)

echo Frontend started successfully!
cd "%BASE_DIR%"
pause
endlocal 