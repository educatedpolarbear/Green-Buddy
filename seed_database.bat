@echo off
echo Seeding database...
cd backend\database\seed
python seed_database.py
if %ERRORLEVEL% neq 0 (
    echo Command failed with exit code %ERRORLEVEL%
    exit /b 1
)

echo Database seeded successfully!
pause 