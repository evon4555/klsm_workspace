@echo off
REM Stop all qa-harness services. The PowerShell implementation avoids fragile
REM batch line-continuation parsing.

setlocal
set "SCRIPT_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%stop-all.ps1"
exit /b %ERRORLEVEL%
