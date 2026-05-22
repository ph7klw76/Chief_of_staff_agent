@echo off
title Building Chief of Staff Agent .exe
cd /d "%~dp0"
echo =============================================================
echo   Chief of Staff Agent — Build Windows .exe
echo   Working dir: %cd%
echo =============================================================
echo.

:: Verify required source files exist in current directory
if not exist "chief_of_staff_agent.py" (
    echo ERROR: chief_of_staff_agent.py not found in %cd%
    echo This .bat must be in the same folder as the source files.
    echo Current folder contents:
    dir /b *.py 2>nul
    echo.
    pause & exit /b 1
)
if not exist "chief_of_staff_gui.py" (
    echo WARNING: chief_of_staff_gui.py not found — GUI build will be skipped.
)
if not exist "chief_of_staff_core.py" (
    echo ERROR: chief_of_staff_core.py not found — cannot build without it.
    pause & exit /b 1
)

echo Files found. Proceeding with build...
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install from https://python.org
    pause & exit /b 1
)
python --version

echo.
echo [1/3] Installing PyInstaller...
pip install pyinstaller --quiet --disable-pip-version-check

echo.
echo [2/3] Building GUI application (ChiefOfStaff.exe)...
python -m PyInstaller chief_of_staff_gui.spec --noconfirm --clean --distpath dist 2>&1
if %errorlevel% neq 0 (
    echo WARNING: GUI build via spec failed. Trying direct build...
    python -m PyInstaller --onefile --windowed --name ChiefOfStaff chief_of_staff_gui.py 2>&1
)
if exist dist\ChiefOfStaff.exe (
    echo   ^>^> dist\ChiefOfStaff.exe built successfully!
    for %%f in (dist\ChiefOfStaff.exe) do echo   Size: %%~zf bytes
) else (
    echo   GUI build failed. Check errors above.
)

echo.
echo [3/3] Building CLI application (ChiefOfStaff-CLI.exe)...
python -m PyInstaller chief_of_staff_cli.spec --noconfirm --clean --distpath dist 2>&1
if %errorlevel% neq 0 (
    echo WARNING: CLI build via spec failed. Trying direct build...
    python -m PyInstaller --onefile --console --name ChiefOfStaff-CLI chief_of_staff_agent.py 2>&1
)
if exist dist\ChiefOfStaff-CLI.exe (
    echo   ^>^> dist\ChiefOfStaff-CLI.exe built successfully!
    for %%f in (dist\ChiefOfStaff-CLI.exe) do echo   Size: %%~zf bytes
) else (
    echo   CLI build failed. Check errors above.
)

echo.
echo =============================================================
echo   Build complete! Executables in dist\ folder:
echo     dist\ChiefOfStaff.exe       — GUI window application
echo     dist\ChiefOfStaff-CLI.exe   — Command-line tool
echo =============================================================
echo.
echo To distribute: copy dist\*.exe to any Windows machine.
echo No Python installation needed on the target machine.
echo.
pause
