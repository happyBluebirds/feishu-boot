"""JSON 状态文件管理 - 按 chat 持久化会话状态。

提供原子写入、会话管理、日志轮转等共享能力。
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any


class BotStateManager:
    """按飞书 chat 持久化的会话状态管理器。

    每个 chat 维护独立的 sessions 字典，支持多会话。
    """

    DEFAULT_SESSION: dict[str, Any] = {
        "last_command": "",
        "last_result": "",
        "status": "idle",
        "started_at": None,
        "finished_at": None,
        "last_error": "",
        "active_pid": None,
        "pending_action": "",
        "pending_prompt": "",
        "last_exit_code": None,
    }

    def __init__(self, state_path: Path) -> None:
        self.path = state_path
        self.lock = threading.Lock()
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if self.path.exists():
            raw = self.path.read_text(encoding="utf-8", errors="replace").strip()
            if raw:
                return json.loads(raw)
        return {"chats": {}}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def get_chat(self, chat_id: str, default_cwd: str) -> dict[str, Any]:
        chats = self.data.setdefault("chats", {})
        if chat_id not in chats:
            chats[chat_id] = {
                "cwd": default_cwd,
                "permission_mode": "",
                "model": "",
                "sessions": {},
                "active_session": "",
            }
        chat = chats[chat_id]
        sessions = chat.setdefault("sessions", {})
        active = chat.get("active_session", "")
        if not active or active not in sessions:
            sid = f"s{len(sessions) + 1}"
            sessions[sid] = dict(self.DEFAULT_SESSION)
            chat["active_session"] = sid
        return chat

    def get_active_session(self, chat_id: str, default_cwd: str) -> dict[str, Any]:
        chat = self.get_chat(chat_id, default_cwd)
        sid = chat.get("active_session", "")
        return chat.get("sessions", {}).get(sid, dict(self.DEFAULT_SESSION))

    def update_session(self, chat_id: str, updates: dict[str, Any], default_cwd: str) -> dict[str, Any]:
        with self.lock:
            chat = self.get_chat(chat_id, default_cwd)
            sid = chat.get("active_session", "")
            session = chat.setdefault("sessions", {}).setdefault(sid, dict(self.DEFAULT_SESSION))
            session.update(updates)
            self.save()
            return session

    def update_chat_field(self, chat_id: str, field: str, value: Any, default_cwd: str) -> None:
        with self.lock:
            chat = self.get_chat(chat_id, default_cwd)
            chat[field] = value
            self.save()


class LogManager:
    """日志管理器，支持轮转。"""

    def __init__(self, log_path: Path, max_bytes: int = 1024 * 1024, backup_count: int = 3) -> None:
        self.path = log_path
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.lock = threading.Lock()

    def log(self, message: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._rotate_if_needed()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        with self.lock:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line)

    def _rotate_if_needed(self) -> None:
        try:
            if not self.path.exists() or self.path.stat().st_size < self.max_bytes:
                return
            oldest = self.path.with_name(f"{self.path.name}.{self.backup_count}")
            if oldest.exists():
                oldest.unlink(missing_ok=True)
            for i in range(self.backup_count - 1, 0, -1):
                src = self.path.with_name(f"{self.path.name}.{i}")
                dst = self.path.with_name(f"{self.path.name}.{i + 1}")
                if src.exists():
                    src.replace(dst)
            self.path.replace(self.path.with_name(f"{self.path.name}.1"))
        except OSError:
            pass


