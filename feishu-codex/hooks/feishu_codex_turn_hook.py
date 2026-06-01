#!/usr/bin/env python3
"""Codex Stop/StopFailure Hook - 任务完成通知。"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

INTEGRATION_ROOT = Path(__file__).resolve().parents[1]
CODEX_ROOT = INTEGRATION_ROOT.parents[1]

integrations_root = CODEX_ROOT / "integrations"
if str(integrations_root) not in sys.path:
    sys.path.insert(0, str(integrations_root))

from feishu_bot_common.hook_utils import (
    load_json, save_json, resolve_chat_id, send_feishu_text,
    read_hook_input, format_ts, format_duration,
)

DEFAULT_CONFIG_PATH = INTEGRATION_ROOT / "config" / "feishu_codex_bot.json"
DEFAULT_HOOK_LOG_PATH = CODEX_ROOT / "outputs" / "feishu-codex" / "logs" / "feishu-codex-turn-hook.log"


def log_event(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def summarize_text(text: str, limit: int = 1200) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return "(无摘要)"
    return cleaned[:limit] if len(cleaned) <= limit else cleaned[:limit].rstrip() + "\n...(已截断)"


def main() -> int:
    raw_input = read_hook_input()
    if not raw_input.strip():
        return 0

    hook_input = json.loads(raw_input)
    hook_event = str(hook_input.get("hook_event_name", ""))
    if hook_event not in {"Stop", "StopFailure", "SessionEnd"}:
        return 0

    if os.environ.get("FEISHU_CODEX_BOT_EXECUTION_MODE", "").strip().lower() == "background":
        return 0

    config_path = Path(os.environ.get("FEISHU_CODEX_BOT_CONFIG_PATH", str(DEFAULT_CONFIG_PATH)))
    if not config_path.exists():
        return 0

    config = load_json(config_path)
    log_path = Path(config.get("turn_hook_log_path") or DEFAULT_HOOK_LOG_PATH)
    state_path = Path(config.get("state_path", ""))
    cwd = str(hook_input.get("cwd", ""))

    chat_id = os.environ.get("FEISHU_CODEX_BOT_CHAT_ID", "").strip()
    if not chat_id:
        chat_id = resolve_chat_id(state_path, cwd)
    if not chat_id:
        log_event(log_path, f"skip {hook_event}: missing chat_id")
        return 0

    finished_at = time.time()
    state = load_json(state_path)
    existing = state.get("chats", {}).get(chat_id, {})
    started_at = existing.get("started_at")

    if hook_event in ("Stop", "SessionEnd"):
        summary = summarize_text(hook_input.get("last_assistant_message", ""))
        lines = [
            "任务完成",
            f"目录：{existing.get('cwd') or cwd}",
            f"耗时：{format_duration(started_at, finished_at)}",
            "", "结果：", summary,
            "", "回复「运行 <任务>」继续",
        ]
        send_feishu_text(config["app_id"], config["app_secret"], chat_id, "\n".join(lines))
        # 更新状态
        chats = state.setdefault("chats", {})
        chat = chats.setdefault(chat_id, {})
        chat.update({"status": "done", "finished_at": finished_at, "last_result": summary, "last_error": ""})
        save_json(state_path, state)
        log_event(log_path, f"sent {hook_event} chat={chat_id}")
        return 0

    error = summarize_text(hook_input.get("error_details") or hook_input.get("error") or "未知错误")
    lines = [
        "任务失败",
        f"目录：{existing.get('cwd') or cwd}",
        f"耗时：{format_duration(started_at, finished_at)}",
        "", "错误：", error,
        "", "回复「运行 <任务>」重试",
    ]
    send_feishu_text(config["app_id"], config["app_secret"], chat_id, "\n".join(lines))
    chats = state.setdefault("chats", {})
    chat = chats.setdefault(chat_id, {})
    chat.update({"status": "failed", "finished_at": finished_at, "last_error": error})
    save_json(state_path, state)
    log_event(log_path, f"sent StopFailure chat={chat_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
