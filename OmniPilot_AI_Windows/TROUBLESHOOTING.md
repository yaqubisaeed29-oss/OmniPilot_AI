# Troubleshooting

## App says it cannot connect to Ollama

1. Open the Ollama app or start its normal Windows service.
2. In PowerShell, run `ollama list` and `ollama --version`.
3. Confirm **Settings → Ollama URL** is `http://127.0.0.1:11434` (default Ollama API). Do not expose the API to a public network.
4. If the service is stopped, restart Ollama from the Start menu. Check local firewall/security software if the loopback API is blocked.

## Planner or vision model is missing

Run `ollama pull qwen2.5:3b` and `ollama pull qwen2.5vl:3b`; then verify names with `ollama list`. Use the exact names (including tags) shown by that command in OmniPilot Settings. The vision model must support image inputs. First model load can take a while; allow enough RAM and disk space.

## Slow responses, memory pressure, or model load failure

Close other high-memory apps. The 3B vision model is designed to be modest but still uses substantial RAM. Ollama can use CPU and supported integrated-GPU backends without NVIDIA. If needed, select a smaller compatible vision model supported by your installed Ollama version. Reduce the task's scope, or use the workspace file actions instead of many visual steps. Do not lower the action/time limits expecting better model quality.

## Screenshot is blank or desktop controls do not work

- Run on the unlocked, interactive Windows 11 desktop; this app is not a Linux/macOS remote controller.
- Windows UAC secure desktop, lock screen, protected screens, and elevated apps are not accessible; respond to those prompts yourself.
- Check Windows privacy/security software and display capture permissions. Close remote desktop overlays or unsupported capture tools and restart the app.
- Try one monitor / the primary display, and avoid moving windows while OmniPilot is acting.
- Move the pointer to a screen corner to trigger PyAutoGUI's failsafe if control becomes unsafe. Use the app's STOP button as well.

## Clipboard typing fails, especially for Persian

OmniPilot pastes text through the local clipboard so Unicode scripts work. Make sure no other clipboard utility is blocking clipboard access, and confirm the `pyperclip` package installed inside `.venv`. Retry after focusing the intended text field yourself. Do not use this for passwords.

## `install_windows.bat` cannot find Python

Install Python 3.11+ from python.org, enable the Python Launcher, reopen the command prompt, and rerun the script. Check with `py -3.11 --version`. If your organization manages Python, use its approved Python distribution and create the environment with `python -m venv .venv`.

## Dependencies fail to install

Check internet access and run `install_windows.bat` again. From this folder, activate `.venv\Scripts\activate` and run `python -m pip install --upgrade pip` then `python -m pip install -r requirements.txt`. If corporate policy blocks packages, install the listed packages only through an approved package source.

## Files are not created or paths are rejected

File actions are restricted to the workspace shown in **Settings**. Use a relative path such as `notes/meeting.txt`, not a drive path or `..`. `create_file` will not overwrite; use an edit request for an existing file. Only UTF-8 text up to 100 KB can be read/edited. The workspace is not an unrestricted file manager.

## Task stops or keeps repeating

Review the visible task log and screen. Make the task specific, avoid combining unrelated goals, and mention the target application. A repeated failure triggers a safe stop; a maximum step/time limit also stops an unverified task. If it asks for clarification, resubmit the task with the missing detail. For a misleading or unsafe action proposal, decline confirmation, press STOP, and do not retry unattended.

## Clear local task history

Close OmniPilot, then delete `omnipilot_memory.sqlite3` from the project folder. Do not delete while a task is running.
