@echo off
:: ============================================================================
:: MB-76 Digital Patchbay Controller - Uninstaller
:: ============================================================================

title MB-76 Patchbay Controller - Uninstall

echo.
echo  ============================================================
echo     MB-76 Patchbay Controller - Uninstaller
echo  ============================================================
echo.
echo   This will remove:
echo   - Python virtual environment (venv folder)
echo   - Desktop shortcut
echo   - Saved presets (optional)
echo.
echo   Project files will be kept.
echo.

set /p CONFIRM="Are you sure you want to uninstall? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo   Uninstall cancelled.
    pause
    exit /b
)

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo   Removing virtual environment...
if exist "venv" (
    rmdir /s /q "venv"
    echo   - Virtual environment removed
) else (
    echo   - Virtual environment not found
)

echo.
echo   Removing desktop shortcut...
set "SHORTCUT=%USERPROFILE%\Desktop\MB-76 Patchbay.lnk"
if exist "%SHORTCUT%" (
    del "%SHORTCUT%"
    echo   - Desktop shortcut removed
) else (
    echo   - Desktop shortcut not found
)

echo.
set /p DEL_PRESETS="Delete saved presets? (Y/N): "
if /i "%DEL_PRESETS%"=="Y" (
    if exist "presets" (
        rmdir /s /q "presets"
        mkdir "presets"
        echo   - Presets deleted
    )
) else (
    echo   - Presets kept
)

echo.
echo  ============================================================
echo     Uninstall Complete
echo  ============================================================
echo.
echo   To reinstall, run install.bat
echo.
pause
