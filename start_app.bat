@echo off
cd /d "%~dp0"
echo Starting BrickLink Storage Location Auto-Populator...
python main_app.py
if errorlevel 1 (
    echo.
    echo Error: Python or required packages not found!
    echo Please ensure Python and CustomTkinter are installed.
    echo.
    pause
)