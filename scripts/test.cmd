@echo off
REM Wrapper to run the PowerShell test from CMD
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0test.ps1" %*
endlocal

