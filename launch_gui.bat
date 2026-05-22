@echo off
title Chief of Staff Agent
cd /d "%~dp0"
echo Starting Chief of Staff Agent v10...
echo.

:: Try python3 first, then python
python3 chief_of_staff_gui.py 2>nul
if %errorlevel% neq 0 (
    python chief_of_staff_gui.py 2>nul
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Python not found or tkinter not installed.
        echo.
        echo Make sure Python 3.12+ is installed from https://python.org
        echo During installation, check "Add Python to PATH"
        echo tkinter is included with the standard Python installer.
        echo.
        echo Alternatively, use the CLI version:
        echo   python chief_of_staff_agent.py --demo
        echo.
        pause
    )
)
