@echo off
chcp 65001 > nul
setlocal

cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-bot.ps1"

echo.
echo Fenster kann geschlossen werden.
pause
