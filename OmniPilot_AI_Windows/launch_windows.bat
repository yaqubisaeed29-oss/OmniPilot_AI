@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Environment not found. Run install_windows.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe main.py
if errorlevel 1 (
  echo OmniPilot exited with an error. See README.md and TROUBLESHOOTING.md.
  pause
)
