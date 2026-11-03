@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-local.ps1"
if errorlevel 1 (
  echo.
  echo Tamanna AI startup failed. Check the error above.
  pause
  exit /b 1
)
echo.
pause
