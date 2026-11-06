from __future__ import annotations
import json
import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = APP_DIR / "config.json"
DEFAULTS = {
    "ollama_url": "http://127.0.0.1:11434", "planner_model": "qwen2.5:3b",
    "vision_model": "qwen2.5vl:3b", "max_steps": 20,
    "task_timeout_seconds": 600, "action_delay_seconds": 0.35,
    "workspace": "~/OmniPilotWorkspace", "language": "en",
    "screenshot_interval_ms": 1200, "remember_task_summaries": True,
}

def load_config() -> dict:
    data = DEFAULTS.copy()
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            user = json.load(f)
        if isinstance(user, dict):
            data.update({k: v for k, v in user.items() if k in DEFAULTS})
    except (OSError, json.JSONDecodeError):
        pass
    data["ollama_url"] = str(data["ollama_url"]).rstrip("/")
    data["workspace"] = os.path.abspath(os.path.expanduser(str(data["workspace"])))
    data["max_steps"] = max(1, min(50, int(data["max_steps"])))
    data["task_timeout_seconds"] = max(30, min(3600, int(data["task_timeout_seconds"])))
    return data

def save_config(data: dict) -> None:
    clean = {k: data.get(k, DEFAULTS[k]) for k in DEFAULTS}
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)
