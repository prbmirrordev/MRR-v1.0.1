@echo off
setlocal

:: Request Administrator privileges if not already running as admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Administrator privileges confirmed.
) else (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~dp0mainİnstall.bat\"' -Verb RunAs"
    exit /b
)

set SCRIPT_DIR=%~dp0
echo MRR Language Setup
echo ========================================

:: 1. Run the existing install.ps1 for PATH, PATHEXT, and Registry (Icons)
echo Running system integration (PATH and Icons)...
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install.ps1"

:: 2. Integrate with Code Editors
echo.
echo Integrating with Code Editors...
set EXT_SOURCE_DIR=%SCRIPT_DIR%vsix\MRR.Language
set EXT_NAME=mrr-lang.mrr-language-support-0.1.0

:: VS Code Detection and Installation
set VSCODE_EXT_DIR=%USERPROFILE%\.vscode\extensions
if exist "%USERPROFILE%\AppData\Local\Programs\Microsoft VS Code\Code.exe" (
    echo VS Code detected. Installing MRR extension...
    if not exist "%VSCODE_EXT_DIR%" mkdir "%VSCODE_EXT_DIR%"
    xcopy "%EXT_SOURCE_DIR%" "%VSCODE_EXT_DIR%\%EXT_NAME%" /E /I /Y /Q >nul
    echo MRR extension integrated into VS Code.
) else (
    echo VS Code not found.
)

:: Cursor Detection and Installation
set CURSOR_EXT_DIR=%USERPROFILE%\.cursor\extensions
if exist "%USERPROFILE%\AppData\Local\Programs\cursor\Cursor.exe" (
    echo Cursor detected. Installing MRR extension...
    if not exist "%CURSOR_EXT_DIR%" mkdir "%CURSOR_EXT_DIR%"
    xcopy "%EXT_SOURCE_DIR%" "%CURSOR_EXT_DIR%\%EXT_NAME%" /E /I /Y /Q >nul
    echo MRR extension integrated into Cursor.
) else (
    echo Cursor not found.
)

echo.
echo Installation complete! 
echo Please restart your terminal and any open code editors (VS Code / Cursor).
pause
