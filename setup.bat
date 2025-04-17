@echo off
setlocal enabledelayedexpansion

set "BASE_DIR=%CD%"
echo Setting up backend...
cd "%BASE_DIR%\backend"
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Backend setup failed with exit code %ERRORLEVEL%
    cd "%BASE_DIR%"
    pause
    exit /b 1
)

echo Setting up frontend...
cd "%BASE_DIR%\frontend"
echo Running npm install...
call npm install
if %ERRORLEVEL% neq 0 (
    echo Frontend setup failed with exit code %ERRORLEVEL%
    cd "%BASE_DIR%"
    pause
    exit /b 1
)

echo Setup completed successfully!

echo Seeding database...
cd "%BASE_DIR%\backend\database\seed"
python seed_database.py
if %ERRORLEVEL% neq 0 (
    echo Database seeding failed with exit code %ERRORLEVEL%
    cd "%BASE_DIR%"
    pause
    exit /b 1
)

echo Database seeded successfully!

echo This window will close in 3 seconds...
timeout /t 3 >nul
endlocal
exit
