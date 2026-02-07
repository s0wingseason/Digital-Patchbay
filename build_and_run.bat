@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: MB-76 Digital Patchbay Controller
:: Build, Install & Run Script
:: ============================================================================

title MB-76 Patchbay Controller

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

cls
echo.
echo  ============================================================
echo       MB-76 DIGITAL PATCHBAY CONTROLLER
echo  ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   ERROR: Python not found!
    echo   Download from: https://www.python.org/downloads/
    echo   Make sure to check "Add Python to PATH"
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do echo   Python %%v found

:: Create/update virtual environment
if not exist "venv" (
    echo   Creating virtual environment...
    python -m venv venv
)

:: Activate and install dependencies
call venv\Scripts\activate.bat
echo   Installing dependencies...
pip install -r requirements.txt --quiet 2>nul

:: Install REAPER scripts if REAPER found
set "REAPER_DIR="
if exist "%APPDATA%\REAPER\Scripts" set "REAPER_DIR=%APPDATA%\REAPER\Scripts"
if defined REAPER_DIR (
    if not exist "%REAPER_DIR%\MB-76" mkdir "%REAPER_DIR%\MB-76" 2>nul
    xcopy /Y /Q "reaper_scripts\*.lua" "%REAPER_DIR%\MB-76\" >nul 2>&1
    echo   REAPER scripts installed
)

:: Create desktop shortcut
set "SHORTCUT=%USERPROFILE%\Desktop\MB-76 Patchbay.lnk"
if not exist "%SHORTCUT%" (
    echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\mk.vbs"
    echo Set oLink = oWS.CreateShortcut("%SHORTCUT%") >> "%TEMP%\mk.vbs"
    echo oLink.TargetPath = "%SCRIPT_DIR%build_and_run.bat" >> "%TEMP%\mk.vbs"
    echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%TEMP%\mk.vbs"
    echo oLink.Save >> "%TEMP%\mk.vbs"
    cscript //nologo "%TEMP%\mk.vbs" >nul 2>&1
    del "%TEMP%\mk.vbs" >nul 2>&1
    echo   Desktop shortcut created
)

echo.
echo  ============================================================
echo   Starting server at http://127.0.0.1:5000
echo   Press Ctrl+C to stop
echo  ============================================================
echo.

python app.py

pause
