# OmniPilot AI

OmniPilot is a local-first Windows 11 desktop assistant with a dark Tkinter UI, local Ollama text/vision inference, bounded mouse and keyboard control, a workspace-confined file toolset, SQLite task history, and a user-visible emergency stop.

> **What this is—and is not:** this is runnable application source, not a mockup. Desktop automation is limited to visible UI operations and an allowlist. It is not a guarantee of reliable completion: vision models can misread screens, coordinates can be imprecise, and unsupported app workflows need user supervision. Keep the computer unlocked and visible while it works. Never use unattended for consequential actions.

## Requirements

- Windows 11, 64-bit.
- Python 3.11+ (the official Python installer with the Python Launcher is recommended).
- Ollama for Windows (free, local inference): <https://ollama.com/download/windows>.
- At least 16 GB system memory is recommended. The default models are a small text planner and a 3B vision-language model; they run on CPU/integrated graphics and do not require NVIDIA/CUDA. Model loading may be slow on CPU. Disk space is needed for both models.
- Internet is only needed to download Python packages/Ollama/models. Inference and task data remain local after installation.

## Install and run

1. Install Python 3.11+ and Ollama.
2. Double-click `install_windows.bat` from this folder. It creates `.venv` and installs the Python dependencies. This script does not install Ollama itself.
3. In a terminal, download the default models once:

   ```bat
   ollama pull qwen2.5:3b
   ollama pull qwen2.5vl:3b
   ```

   If either model is unavailable in your Ollama registry, choose compatible alternatives from Ollama's model library and enter their exact installed names under **Settings**. The vision model must accept images. A smaller compatible vision model can reduce RAM use at the cost of accuracy. Check the model's license and Ollama compatibility before substituting.
4. Ensure the Ollama app/service is running (default local API: `http://127.0.0.1:11434`).
5. Double-click `launch_windows.bat`.

No Docker, cloud account, paid API key, or NVIDIA GPU is required. PyAutoGUI's failsafe is on: moving the pointer to a screen corner interrupts a pending mouse action. The app's **STOP** button sets the agent's stop flag; a currently running local model request may take a short time to return before the thread exits.

## Using the assistant

- Enter one concrete task in Persian or English and select **Start task**. `Ctrl+Enter` also starts it.
- The planner produces a short plan. The vision model then sees a fresh screenshot before each desktop action, and the agent checks subsequent screenshots to decide whether to continue or stop.
- **Pause**, **Resume**, and **STOP** are available during a run. The default maximum is 20 actions and 10 minutes; both limits can be changed in **Settings** (hard caps are enforced).
- The screenshot pane shows a scaled preview. The model receives a screenshot resized to at most 1440×900; click coordinates are mapped back to the desktop's primary display.
- File tools operate only under the configured OmniPilot workspace (default `~/OmniPilotWorkspace`). Supported operations: list/read/create/edit/move files and delete individual files. File reads and writes are capped at 100 KB. No file operation can traverse outside the workspace or overwrite an existing file through create/move.
- Application launch is limited to Notepad, Calculator, Explorer, Edge, Chrome, Paint, and WordPad. `open_url` accepts only `http`/`https` and opens the default browser. Browser interaction after opening uses visible mouse/keyboard control.
- Change models, Ollama URL, workspace, timeout, and action limit in **Settings**. The app stores preferences/settings locally and uses `omnipilot_memory.sqlite3` for task history. The memory API deliberately rejects credential-like preference keys; passwords/tokens are not stored by the agent.

## Safety model

- The model cannot issue shell commands, scripts, PowerShell, arbitrary process launches, arbitrary key combinations, or unconstrained paths. There is no shell-execution action.
- Mouse actions must be within the desktop bounds. Keyboard keys/shortcuts and app names are allowlisted. Web links must be `http(s)`.
- Deleting a workspace file always requests confirmation. Sending/emailing, publishing, purchasing/payment, installing, security-setting, and other irreversible actions request a confirmation dialog when detected in the request/action; the model is also instructed to flag sensitive actions. **This is a best-effort guard, not a perfect semantic security boundary**: a visual click on a sensitive button can be misidentified. Review the screen and decline uncertain confirmations. OmniPilot never bypasses OS permissions or security controls.
- Keep secrets out of task text and files given to the agent. Do not ask it to handle passwords or authentication codes.
- Normal reversible clicks and typing do not require per-action approval. You can pause or stop at any time.

## Project structure

```text
main.py                         Tkinter entry point
config.json                     Local defaults (non-secret)
requirements.txt                Python dependencies
install_windows.bat             Creates venv and installs dependencies
launch_windows.bat              Starts the desktop app
omnipilot/config.py             Config load/save and bounds
omnipilot/ui.py                 Dark UI, settings, screenshot, event loop
omnipilot/agent.py              Planning, observe/act/verify loop, limits
omnipilot/computer.py           Desktop and workspace-safe action layer
omnipilot/ollama_client.py      Local Ollama HTTP client and JSON parsing
omnipilot/memory.py             Local SQLite history/preferences
TROUBLESHOOTING.md              Common setup and runtime problems
```

## Configuration

Edit `config.json` or use the Settings panel. `ollama_url` should normally remain `http://127.0.0.1:11434`; model values must exactly match `ollama list`. Model and timeout changes take effect on the next task. The workspace is created on launch/use if missing.

## Testing

Run the non-GUI unit tests from this directory:

```bat
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The test suite covers JSON response parsing and workspace/path safety. Desktop capture and input need a Windows interactive session, so they cannot be meaningfully exercised on a headless non-Windows host.

## Limitations

- Windows desktop capture/control requires an interactive Windows session. UAC secure desktop, lock screen, some elevated windows, protected apps, and permission prompts are intentionally not bypassed.
- UI understanding and clicking are probabilistic. High-DPI scaling, multiple monitors, dialogs, remote desktops, animation, and app-specific custom controls may reduce accuracy. It targets the primary display.
- This is not a browser DOM automation engine; pages are operated visually, and authentication/CAPTCHA flows remain user-controlled.
- `qwen2.5vl:3b` can be inaccurate or too slow on a given machine. Try a compatible smaller/larger Ollama vision model in Settings. A suitable vision model is required for desktop tasks; the workspace file tools can still be used without screen capture only when the host permits app startup and the task is file-focused.
- It does not run as a service or start hidden background processes. SQLite summaries contain user instructions and short results; delete `omnipilot_memory.sqlite3` to clear history.
