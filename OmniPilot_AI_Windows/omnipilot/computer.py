from __future__ import annotations
import os, platform, shutil, subprocess, time, webbrowser
from pathlib import Path
from urllib.parse import urlparse

class ActionError(RuntimeError):
    pass

class Computer:
    """Bounded desktop I/O and sandboxed workspace file operations."""
    KEY_ALLOWLIST = {"enter", "tab", "esc", "escape", "space", "backspace", "delete", "home", "end", "pageup", "pagedown", "up", "down", "left", "right", "ctrl", "alt", "shift", "win", "f1", "f2", "f3", "f4", "f5", "f6", "f10", "f11", "f12"}
    COMBOS = {"ctrl+l", "ctrl+c", "ctrl+v", "ctrl+x", "ctrl+a", "ctrl+z", "ctrl+y", "ctrl+s", "ctrl+f", "ctrl+t", "ctrl+w", "ctrl+shift+t", "alt+f4", "alt+tab", "win+e", "win+r", "ctrl+o", "ctrl+n", "ctrl+p"}
    APPS = {"notepad": ["notepad.exe"], "calculator": ["calc.exe"], "explorer": ["explorer.exe"], "edge": ["msedge.exe"], "chrome": ["chrome.exe"], "paint": ["mspaint.exe"], "wordpad": ["write.exe"]}
    def __init__(self, workspace: str, delay: float = .35):
        self.workspace = Path(workspace).expanduser().resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.delay = max(0.0, min(2.0, float(delay)))
        self._pyautogui = None
        self.last_image_size = (0, 0)
        self.last_screen_size = (0, 0)
    def _gui(self):
        if platform.system() != "Windows":
            raise ActionError("Mouse/keyboard automation is supported on Windows 11 only. File tasks still work on this platform.")
        if self._pyautogui is None:
            try:
                import pyautogui
                pyautogui.FAILSAFE = True
                pyautogui.PAUSE = .08
                self._pyautogui = pyautogui
            except Exception as e:
                raise ActionError(f"Desktop automation is unavailable: {e}") from e
        return self._pyautogui
    def screenshot(self) -> bytes:
        if platform.system() != "Windows":
            raise ActionError("Screen capture is available when running on Windows 11.")
        try:
            from PIL import ImageGrab
            import io
            image = ImageGrab.grab()
            self.last_screen_size = image.size
            image.thumbnail((1440, 900))
            self.last_image_size = image.size
            out = io.BytesIO(); image.save(out, format="JPEG", quality=82)
            return out.getvalue()
        except Exception as e:
            raise ActionError(f"Screenshot capture failed: {e}") from e
    def screen_size(self) -> tuple[int, int]:
        g = self._gui(); return g.size()
    def _path(self, rel: str) -> Path:
        if not isinstance(rel, str) or not rel.strip() or len(rel) > 500:
            raise ActionError("A relative workspace path is required.")
        p = Path(rel)
        if p.is_absolute() or ".." in p.parts:
            raise ActionError("File actions must use paths inside the configured OmniPilot workspace (no absolute paths or '..').")
        target = (self.workspace / p).resolve()
        try:
            target.relative_to(self.workspace)
        except ValueError as e:
            raise ActionError("Path escapes the OmniPilot workspace.") from e
        return target
    def perform(self, action: dict) -> str:
        kind = str(action.get("type", "")).lower()
        if kind == "wait":
            seconds = max(.2, min(5, float(action.get("seconds", 1))))
            time.sleep(seconds); return f"Waited {seconds:g} seconds."
        if kind == "click":
            g=self._gui(); x=int(action.get("x",-1)); y=int(action.get("y",-1)); w,h=g.size()
            if not (0 <= x < w and 0 <= y < h): raise ActionError(f"Click coordinates outside screen ({w}x{h}).")
            button=str(action.get("button","left"))
            if button not in ("left", "right"): raise ActionError("Only left and right clicks are allowed.")
            g.click(x,y,button=button); time.sleep(self.delay); return f"Clicked {button} at ({x}, {y})."
        if kind == "move":
            g=self._gui(); x=int(action.get("x",-1)); y=int(action.get("y",-1)); w,h=g.size()
            if not (0 <= x < w and 0 <= y < h): raise ActionError("Pointer coordinates outside screen.")
            g.moveTo(x,y,duration=.2); return f"Moved pointer to ({x}, {y})."
        if kind == "type":
            text=action.get("text", "")
            if not isinstance(text,str) or len(text)>4000: raise ActionError("Text must be a string of at most 4000 characters.")
            try:
                import pyperclip
                pyperclip.copy(text); self._gui().hotkey("ctrl","v")
            except Exception as e:
                raise ActionError(f"Clipboard typing failed (install pyperclip and ensure clipboard access): {e}") from e
            time.sleep(self.delay); return f"Typed {len(text)} characters using the local clipboard."
        if kind == "key":
            key=str(action.get("key", "")).lower().replace(" ", "")
            if "+" in key:
                if key not in self.COMBOS: raise ActionError(f"Keyboard shortcut '{key}' is not allowlisted.")
                self._gui().hotkey(*key.split("+"))
            else:
                if key not in self.KEY_ALLOWLIST: raise ActionError(f"Key '{key}' is not allowlisted.")
                self._gui().press("esc" if key=="escape" else key)
            time.sleep(self.delay); return f"Pressed {key}."
        if kind == "scroll":
            amount=max(-8,min(8,int(action.get("amount",0))))
            self._gui().scroll(amount); return f"Scrolled {amount} notches."
        if kind == "open_app":
            name=str(action.get("name","")).lower().strip()
            if name not in self.APPS: raise ActionError(f"App '{name}' is not in the safe launcher allowlist: {', '.join(self.APPS)}")
            if platform.system() != "Windows": raise ActionError("Application launch requires Windows 11.")
            subprocess.Popen(self.APPS[name], shell=False, close_fds=True)
            return f"Launched {name}."
        if kind == "open_url":
            url=str(action.get("url", "")).strip(); parsed=urlparse(url)
            if parsed.scheme not in {"http","https"} or not parsed.netloc or len(url)>2000:
                raise ActionError("Only valid http:// or https:// URLs can be opened.")
            webbrowser.open(url, new=2); return f"Opened {url} in the default browser."
        if kind == "list_files":
            folder=self._path(action.get("path", ".")); folder.mkdir(parents=True, exist_ok=True)
            rows=[]
            for p in sorted(folder.iterdir(), key=lambda x:x.name.casefold())[:100]:
                rows.append(("[DIR] " if p.is_dir() else "[FILE] ")+p.name)
            return "Workspace entries:\n"+("\n".join(rows) if rows else "(empty)")
        if kind == "read_file":
            p=self._path(action.get("path", ""))
            if not p.is_file(): raise ActionError("File does not exist inside the workspace.")
            if p.stat().st_size > 100_000: raise ActionError("File exceeds the 100 KB read limit.")
            try: return "File content:\n"+p.read_text(encoding="utf-8")
            except UnicodeError as e: raise ActionError("Only UTF-8 text files can be read by the agent.") from e
        if kind == "create_file":
            p=self._path(action.get("path", "")); content=action.get("content", "")
            if not isinstance(content,str) or len(content)>100_000: raise ActionError("File content must be text up to 100 KB.")
            p.parent.mkdir(parents=True, exist_ok=True)
            if p.exists(): raise ActionError("File already exists; use edit_file to change it.")
            p.write_text(content, encoding="utf-8"); return f"Created workspace file {p.relative_to(self.workspace)} ({len(content)} characters)."
        if kind == "edit_file":
            p=self._path(action.get("path", "")); content=action.get("content", "")
            if not p.is_file(): raise ActionError("File does not exist. Use create_file for a new file.")
            if not isinstance(content,str) or len(content)>100_000: raise ActionError("File content must be text up to 100 KB.")
            p.write_text(content, encoding="utf-8"); return f"Updated workspace file {p.relative_to(self.workspace)}."
        if kind == "move_file":
            src=self._path(action.get("path", "")); dst=self._path(action.get("destination", ""))
            if not src.exists(): raise ActionError("Source does not exist.")
            if dst.exists(): raise ActionError("Destination already exists; refusing to overwrite.")
            dst.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(src),str(dst)); return f"Moved {src.name} to {dst.relative_to(self.workspace)}."
        if kind == "delete_file":
            p=self._path(action.get("path", ""))
            if not p.is_file(): raise ActionError("Only individual files can be deleted; folders are not deleted.")
            p.unlink(); return f"Deleted workspace file {p.relative_to(self.workspace)}."
        raise ActionError(f"Unsupported action type: {kind or '(missing)'}")
