"""Hook 工具 - 权限审批、完成通知等 hook 的共享逻辑。

提供飞书消息发送、chat_id 解析、审批队列管理等能力。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    """读取 JSON 文件，不存在或为空时返回空结构。"""
    if path.exists():
        raw = path.read_text(encoding="utf-8", errors="replace").strip()
        if raw:
            return json.loads(raw)
    return {}


def save_json(path: Path, data: dict[str, Any]) -> None:
    """原子写入 JSON 文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def resolve_chat_id(state_path: Path, cwd: str) -> str:
    """从 bot state 反查飞书 chat_id（用于 hook 缺少环境变量时）。"""
    state = load_json(state_path)
    chats = state.get("chats", {})
    best_chat = ""
    best_ts = -1.0
    for chat_id, chat_state in chats.items():
        candidate_cwd = str(chat_state.get("cwd", ""))
        if cwd and candidate_cwd and cwd.lower() == candidate_cwd.lower():
            ts = float(chat_state.get("started_at") or 0)
            if ts > best_ts:
                best_ts = ts
                best_chat = chat_id
    if best_chat:
        return best_chat
    for chat_id, chat_state in chats.items():
        ts = float(chat_state.get("started_at") or chat_state.get("finished_at") or 0)
        if ts > best_ts:
            best_ts = ts
            best_chat = chat_id
    return best_chat


def send_feishu_text(app_id: str, app_secret: str, chat_id: str, text: str) -> None:
    """独立发送一条飞书文本消息（用于 hook 场景，不依赖 bot 主进程）。"""
    import lark_oapi as lark
    from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody, CreateMessageResponse

    client = lark.Client.builder().app_id(app_id).app_secret(app_secret).build()
    request = (
        CreateMessageRequest.builder()
        .receive_id_type("chat_id")
        .request_body(
            CreateMessageRequestBody.builder()
            .receive_id(chat_id)
            .msg_type("text")
            .content(json.dumps({"text": text}, ensure_ascii=False))
            .build()
        )
        .build()
    )
    response: CreateMessageResponse = client.im.v1.message.create(request)
    if not response.success():
        raise RuntimeError(f"send message failed: code={response.code} msg={response.msg}")


def read_hook_input() -> str:
    """读取 Claude/Codex hook 的 stdin JSON 输入（UTF-8 bytes 避免 Windows 乱码）。"""
    return sys.stdin.buffer.read().decode("utf-8", errors="replace")


def summarize_tool(tool_name: str, tool_input: Any) -> str:
    """生成工具请求的简短中文描述。"""
    if not isinstance(tool_input, dict):
        return f"{tool_name}: {str(tool_input)[:200]}"

    if tool_name == "bash":
        cmd = str(tool_input.get("command", ""))
        desc = str(tool_input.get("description", ""))
        return f"Bash: {desc or cmd[:200]}"
    if tool_name in ("edit", "multiedit"):
        return f"编辑文件: {tool_input.get('file_path', '')}"
    if tool_name in ("write", "notebookedit"):
        return f"写入文件: {tool_input.get('file_path') or tool_input.get('notebook_path', '')}"
    if tool_name == "read":
        return f"读取文件: {tool_input.get('file_path', '')}"
    return f"{tool_name}: {json.dumps(tool_input, ensure_ascii=False)[:200]}"


def build_allow_response() -> dict[str, Any]:
    """构建允许授权的 hook 响应。"""
    return {"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "allow"}}}


def build_deny_response(message: str) -> dict[str, Any]:
    """构建拒绝授权的 hook 响应。"""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {"behavior": "deny", "message": message, "interrupt": True},
        }
    }


def format_ts(value: Any) -> str:
    """Unix 时间戳格式化为本地可读时间。"""
    if not value:
        return "-"
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(value)))


def format_duration(started_at: Any, finished_at: Any) -> str:
    """格式化耗时。"""
    if not started_at or not finished_at:
        return "-"
    elapsed = max(0, int(float(finished_at) - float(started_at)))
    minutes, seconds = divmod(elapsed, 60)
    hours, minutes = divmod(minutes, 60)
    parts = []
    if hours:
        parts.append(f"{hours}小时")
    if minutes:
        parts.append(f"{minutes}分钟")
    if seconds or not parts:
        parts.append(f"{seconds}秒")
    return "".join(parts)
