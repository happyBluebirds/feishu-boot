#!/usr/bin/env python3
"""Codex PermissionRequest Hook - 权限请求转发到飞书。"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

INTEGRATION_ROOT = Path(__file__).resolve().parents[1]
CODEX_ROOT = INTEGRATION_ROOT.parents[1]

# 确保公共模块可导入
integrations_root = CODEX_ROOT / "integrations"
if str(integrations_root) not in sys.path:
    sys.path.insert(0, str(integrations_root))

from feishu_bot_common.hook_utils import (
    load_json, save_json, resolve_chat_id, send_feishu_text,
    read_hook_input, summarize_tool, build_allow_response, build_deny_response,
)

DEFAULT_CONFIG_PATH = INTEGRATION_ROOT / "config" / "feishu_codex_bot.json"
DEFAULT_TIMEOUT_SECONDS = 8 * 60 * 60
DEFAULT_HOOK_LOG_PATH = CODEX_ROOT / "outputs" / "feishu-codex" / "logs" / "feishu-codex-permission-hook.log"


def log_event(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def main() -> int:
    raw_input = read_hook_input()
    if not raw_input.strip():
        return 0

    hook_input = json.loads(raw_input)
    if hook_input.get("hook_event_name") != "PermissionRequest":
        return 0

    config_path = Path(os.environ.get("FEISHU_CODEX_BOT_CONFIG_PATH", str(DEFAULT_CONFIG_PATH)))
    if not config_path.exists():
        return 0

    config = load_json(config_path)
    log_path = Path(config.get("permission_hook_log_path") or DEFAULT_HOOK_LOG_PATH)
    approvals_path = Path(config.get("approvals_path", ""))
    cwd = str(hook_input.get("cwd", ""))

    chat_id = os.environ.get("FEISHU_CODEX_BOT_CHAT_ID", "").strip()
    if not chat_id:
        chat_id = resolve_chat_id(Path(config.get("state_path", "")), cwd)
    if not chat_id:
        log_event(log_path, f"skip: missing chat_id cwd={cwd}")
        return 0

    tool_name = str(hook_input.get("tool_name", "-"))
    tool_input = hook_input.get("tool_input")
    created_at = time.time()
    request_id = f"{int(created_at)}"

    state = load_json(approvals_path)
    state.setdefault("requests", {})[request_id] = {
        "chat_id": chat_id, "cwd": cwd,
        "tool_name": tool_name, "tool_input": tool_input,
        "status": "pending", "created_at": created_at,
    }
    save_json(approvals_path, state)

    summary = summarize_tool(tool_name, tool_input)
    message = f"权限请求\n工具：{tool_name}\n动作：{summary}\n目录：{cwd}\n\n回复「同意」或「拒绝」"
    send_feishu_text(config["app_id"], config["app_secret"], chat_id, message)
    log_event(log_path, f"queued request_id={request_id} tool={tool_name}")

    deadline = created_at + DEFAULT_TIMEOUT_SECONDS
    while time.time() < deadline:
        state = load_json(approvals_path)
        request = state.get("requests", {}).get(request_id, {})
        if request.get("status") == "approved":
            print(json.dumps(build_allow_response(), ensure_ascii=False))
            return 0
        if request.get("status") == "denied":
            print(json.dumps(build_deny_response("飞书已拒绝。"), ensure_ascii=False))
            return 0
        time.sleep(2)

    print(json.dumps(build_deny_response("授权超时。"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
