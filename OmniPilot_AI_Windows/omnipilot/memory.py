from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

class LocalMemory:
    """Small local SQLite store; intentionally has no credential storage API."""
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS task_history (id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, instruction TEXT NOT NULL, summary TEXT NOT NULL, status TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    def _connect(self):
        return sqlite3.connect(self.path, timeout=5)
    def get_preferences(self) -> dict[str, str]:
        with self._connect() as db:
            return dict(db.execute("SELECT key, value FROM preferences"))
    def set_preference(self, key: str, value: str) -> None:
        if any(x in key.casefold() for x in ("password", "token", "secret", "credential", "api_key")):
            raise ValueError("Credentials and secrets must not be stored in OmniPilot memory.")
        with self._connect() as db:
            db.execute("INSERT INTO preferences(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key[:100], value[:1000]))
    def add_task(self, instruction: str, summary: str, status: str) -> None:
        with self._connect() as db:
            db.execute("INSERT INTO task_history(created_at,instruction,summary,status) VALUES(?,?,?,?)", (datetime.now(timezone.utc).isoformat(), instruction[:2000], summary[:2000], status[:40]))
    def recent_tasks(self, limit: int = 5) -> list[tuple[str, str, str]]:
        with self._connect() as db:
            return list(db.execute("SELECT instruction, summary, status FROM task_history ORDER BY id DESC LIMIT ?", (max(1, min(20, limit)),)))
