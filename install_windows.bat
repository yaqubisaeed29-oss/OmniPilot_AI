@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher not found. Install Python 3.11 or newer from https://www.python.org/downloads/windows/ and enable the launcher.
  exit /b 1
)
py -3.11 --version >nul 2>nul
if errorlevel 1 (
  echo Python 3.11 was not found. Install Python 3.11+ and enable the Python Launcher.
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -3.11 -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo.
echo Python dependencies installed.
where ollama >nul 2>nul
if errorlevel 1 (
  echo Ollama was not detected. Install it from https://ollama.com/download/windows
  echo Then open a terminal and run: ollama pull qwen2.5:3b
  echo And: ollama pull qwen2.5vl:3b
) else (
  echo Ollama detected. To prepare models, run:
  echo   ollama pull qwen2.5:3b
  echo   ollama pull qwen2.5vl:3b
)
echo Then run launch_windows.bat
exit /b 0
:fail
echo Installation failed. See the error above.
exit /b 1
