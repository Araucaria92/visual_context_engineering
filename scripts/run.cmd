@echo off
REM Wrapper to run the PowerShell script from CMD
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" %*
endlocal

