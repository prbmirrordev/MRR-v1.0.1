@echo off
REM MRR English Installer
REM Usage: ing.bat

echo MRR English mode installer

setx MRR_LANG en >nul
if %ERRORLEVEL% EQU 0 (
    echo English mode enabled for MRR.
    echo Restart your terminal or command prompt to apply changes.
) else (
    echo Failed to set environment variable. Try running this script as Administrator.
)
pause
