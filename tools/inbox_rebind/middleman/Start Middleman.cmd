@echo off
setlocal
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Middleman.ps1"
set "MiddlemanExit=%errorlevel%"
if /I not "%~1"=="--no-pause" pause
exit /b %MiddlemanExit%
