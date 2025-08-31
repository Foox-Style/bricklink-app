@echo off
cd /d "%~dp0"
echo Starting BrickLink Tools Suite...
python main_app_new.py
if errorlevel 1 (
    echo.
    echo Error: Python or required packages not found!
    echo Please ensure Python and CustomTkinter are installed.
    echo.
    pause
)