#!/usr/bin/env python3
"""飞书 Codex 助手机器人。

通过飞书聊天控制 OpenAI Codex CLI，支持后台任务执行、状态查询、目录切换。
"""

from __future__ import annotations

import argparse
import json
import os
import site
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

INTEGRATION_ROOT = Path(__file__).resolve().parents[1]
CODEX_ROOT = INTEGRATION_ROOT.parents[1]
APP_ROOT = Path(__file__).resolve().parent

# 确保公共模块可导入（feishu_bot_common 在 integrations/ 下）
integrations_root = CODEX_ROOT / "integrations"
if str(integrations_root) not in sys.path:
    sys.path.insert(0, str(integrations_root))
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

try:
    vendor = str(INTEGRATION_ROOT / "vendor")
    if os.path.isdir(vendor) and vendor not in sys.path:
        sys.path.append(vendor)
    user_site = site.getusersitepackages()
    if user_site and user_site not in sys.path:
        sys.path.append(user_site)
    import lark_oapi as lark
except ImportError:
    raise SystemExit("Missing 'lark-oapi'. Install: python -m pip install lark-oapi")

from feishu_bot_common import FeishuGateway, IncomingTextMessage, BotStateManager
from feishu_bot_common.hook_utils import format_ts, format_duration
from feishu_bot_common.state_manager import LogManager
from feishu_bot_common.feishu_gateway import create_gateway


DEFAULT_OUTPUT_ROOT = CODEX_ROOT / "outputs" / "feishu-codex"
DEFAULT_STATE_PATH = DEFAULT_OUTPUT_ROOT / "state" / "feishu-codex-bot-state.json"
DEFAULT_LOG_PATH = DEFAULT_OUTPUT_ROOT / "logs" / "feishu-codex-bot.log"


@dataclass
class BotConfig:
    """飞书 Codex 机器人配置。"""
    app_id: str
    app_secret: str
    codex_path: str = "codex"
    default_cwd: str = ""
    cwd_aliases: dict[str, str] = field(default_factory=dict)
    allowed_chat_ids: list[str] = field(default_factory=list)
    default_model: str = ""
    additional_args: list[str] = field(default_factory=list)
    state_path: str = str(DEFAULT_STATE_PATH)
    log_path: str = str(DEFAULT_LOG_PATH)
    reply_max_chars: int = 3500

    @classmethod
    def load(cls, path: Path) -> "BotConfig":
        return cls(**json.loads(path.read_text(encoding="utf-8")))


class FeishuCodexBot:
    """飞书 Codex 机器人主控。"""

    STATUS_LABELS = {
        "idle": "空闲",
        "running": "执行中",
        "done": "已完成",
        "failed": "失败",
        "stopped": "已停止",
    }

    HELP_TEXT = """可用命令：
运行 <任务>     执行 Codex 任务
停止            终止当前任务
状态            查询当前会话状态
目录 <路径>      切换工作目录
目录别名         显示已配置的目录别名
帮助            显示此帮助"""

    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.state = BotStateManager(Path(config.state_path))
        self.logger = LogManager(Path(config.log_path))
        self.active_chats: set[str] = set()
        self.active_lock = threading.Lock()
        self.jobs: dict[str, subprocess.Popen[str]] = {}
        self.jobs_lock = threading.Lock()

        self.gateway = create_gateway(
            app_id=config.app_id,
            app_secret=config.app_secret,
            integration_root=INTEGRATION_ROOT,
            log_fn=self.logger.log,
            reply_max_chars=config.reply_max_chars,
        )

    def send_text(self, chat_id: str, text: str) -> None:
        try:
            self.gateway.send_text(chat_id, text)
        except Exception as exc:
            self.logger.log(f"send failed chat={chat_id} error={exc}")

    def _resolve_cwd(self, text: str) -> tuple[str, str]:
        text = text.strip()
        if not text:
            return self.config.default_cwd, ""
        if text in self.config.cwd_aliases:
            return self.config.cwd_aliases[text], ""
        p = Path(text)
        if p.is_absolute() and p.is_dir():
            return str(p), ""
        if self.config.default_cwd:
            candidate = Path(self.config.default_cwd) / text
            if candidate.is_dir():
                return str(candidate), ""
        return "", f"目录不存在：{text}"

    def _get_cwd(self, chat_id: str) -> str:
        chat = self.state.get_chat(chat_id, self.config.default_cwd)
        return chat.get("cwd") or self.config.default_cwd

    def _execute_task(self, chat_id: str, prompt: str, cwd: str) -> None:
        """后台执行 Codex 任务。"""
        started_at = time.time()
        self.state.update_session(chat_id, {
            "status": "running",
            "started_at": started_at,
            "finished_at": None,
            "last_error": "",
            "last_command": prompt,
            "active_pid": None,
        }, cwd)

        args = [self.config.codex_path, "exec", "--dangerously-bypass-approvals-and-sandbox"]
        if self.config.default_model:
            args.extend(["--model", self.config.default_model])
        args.extend(self.config.additional_args)
        args.append(prompt)

        try:
            proc = subprocess.Popen(
                args, cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace",
            )
            with self.jobs_lock:
                self.jobs[chat_id] = proc
            self.state.update_session(chat_id, {"active_pid": proc.pid}, cwd)
            self.logger.log(f"codex started chat={chat_id} pid={proc.pid} cwd={cwd}")

            stdout, stderr = proc.communicate(timeout=600)
            finished_at = time.time()
            exit_code = proc.returncode

            result = stdout.strip() if stdout else ""
            error = stderr.strip() if stderr else ""
            status = "done" if exit_code == 0 else "failed"

            lines = [
                f"任务{'完成' if exit_code == 0 else '失败'}",
                f"目录：{cwd}",
                f"耗时：{int(finished_at - started_at)}秒",
                "",
                result[:self.config.reply_max_chars] or "(无输出)",
            ]
            if error and exit_code != 0:
                lines.extend(["", "错误：", error[:500]])

            self.send_text(chat_id, "\n".join(lines))
            self.state.update_session(chat_id, {
                "status": status,
                "finished_at": finished_at,
                "last_result": result,
                "last_error": error,
                "last_exit_code": exit_code,
                "active_pid": None,
            }, cwd)

        except subprocess.TimeoutExpired:
            proc.kill()
            self.send_text(chat_id, "任务超时（10分钟），已终止。")
            self.state.update_session(chat_id, {
                "status": "failed", "finished_at": time.time(),
                "last_error": "timeout", "active_pid": None,
            }, cwd)
        except FileNotFoundError:
            self.send_text(chat_id, f"Codex 未找到：{self.config.codex_path}")
            self.state.update_session(chat_id, {
                "status": "failed", "finished_at": time.time(),
                "last_error": "codex not found", "active_pid": None,
            }, cwd)
        except Exception as exc:
            self.send_text(chat_id, f"异常：{exc}")
            self.state.update_session(chat_id, {
                "status": "failed", "finished_at": time.time(),
                "last_error": str(exc), "active_pid": None,
            }, cwd)
        finally:
            with self.jobs_lock:
                self.jobs.pop(chat_id, None)
            with self.active_lock:
                self.active_chats.discard(chat_id)

    def _stop_task(self, chat_id: str) -> None:
        with self.jobs_lock:
            proc = self.jobs.get(chat_id)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            self.send_text(chat_id, "任务已终止。")
        else:
            self.send_text(chat_id, "当前没有正在运行的任务。")
        cwd = self._get_cwd(chat_id)
        self.state.update_session(chat_id, {
            "status": "stopped", "finished_at": time.time(), "active_pid": None,
        }, cwd)
        with self.active_lock:
            self.active_chats.discard(chat_id)

    def _show_status(self, chat_id: str) -> None:
        cwd = self._get_cwd(chat_id)
        session = self.state.get_active_session(chat_id, cwd)
        status = self.STATUS_LABELS.get(session.get("status", "idle"), "未知")

        lines = [f"状态：{status}", f"目录：{cwd}"]
        if session.get("last_command"):
            lines.append(f"上次任务：{session['last_command'][:80]}")
        if session.get("started_at"):
            lines.append(f"开始：{format_ts(session['started_at'])}")
        if session.get("finished_at"):
            lines.append(f"结束：{format_ts(session['finished_at'])}（{format_duration(session.get('started_at'), session['finished_at'])}）")
        if session.get("last_error"):
            lines.append(f"错误：{session['last_error'][:200]}")
        if session.get("active_pid"):
            lines.append(f"PID：{session['active_pid']}")
        self.send_text(chat_id, "\n".join(lines))

    def _show_aliases(self, chat_id: str) -> None:
        if not self.config.cwd_aliases:
            self.send_text(chat_id, "未配置目录别名。")
            return
        lines = ["目录别名："]
        for alias, path in self.config.cwd_aliases.items():
            lines.append(f"  {alias} → {path}")
        self.send_text(chat_id, "\n".join(lines))

    def _start_task(self, chat_id: str, prompt: str, cwd: str) -> None:
        with self.active_lock:
            if chat_id in self.active_chats:
                self.send_text(chat_id, "已有任务在执行中，请等待或发送「停止」。")
                return
            self.active_chats.add(chat_id)
        self.send_text(chat_id, f"开始执行，目录：{cwd}")
        threading.Thread(target=self._execute_task, args=(chat_id, prompt, cwd), daemon=True).start()

    def handle_command(self, chat_id: str, text: str) -> None:
        text = text.strip()
        if not text:
            return

        if text in ("帮助", "/help", "help"):
            self.send_text(chat_id, self.HELP_TEXT)
            return
        if text in ("状态", "/status", "status"):
            self._show_status(chat_id)
            return
        if text in ("停止", "/stop", "stop"):
            self._stop_task(chat_id)
            return
        if text in ("目录别名", "别名"):
            self._show_aliases(chat_id)
            return

        if text.startswith("目录 ") or text.startswith("目录\t"):
            dir_text = text[2:].strip()
            resolved, error = self._resolve_cwd(dir_text)
            if error:
                self.send_text(chat_id, error)
                return
            self.state.update_chat_field(chat_id, "cwd", resolved, self.config.default_cwd)
            self.send_text(chat_id, f"已切换到：{resolved}")
            return

        if text.startswith("运行 ") or text.startswith("run "):
            prompt = text.split(" ", 1)[1].strip()
            if not prompt:
                self.send_text(chat_id, "请提供任务内容。")
                return
            self._start_task(chat_id, prompt, self._get_cwd(chat_id))
            return

        # 默认作为任务执行
        self._start_task(chat_id, text, self._get_cwd(chat_id))

    def run(self) -> None:
        self.logger.log("bot starting")
        self.logger.log(f"codex_path={self.config.codex_path} default_cwd={self.config.default_cwd}")

        def on_text(msg: IncomingTextMessage) -> None:
            if self.config.allowed_chat_ids and msg.chat_id not in self.config.allowed_chat_ids:
                self.send_text(msg.chat_id, "当前聊天未加入允许列表。")
                return
            self.logger.log(f"recv chat={msg.chat_id} text={msg.text}")
            self.handle_command(msg.chat_id, msg.text)

        def on_non_text(chat_id: str, msg_type: str) -> None:
            self.send_text(chat_id, "仅支持文本消息。发送「帮助」查看命令。")

        def on_empty_text(chat_id: str) -> None:
            self.send_text(chat_id, "收到空消息。发送「帮助」查看命令。")

        self.gateway.start_text_listener(on_text, on_non_text, on_empty_text)


def main() -> int:
    parser = argparse.ArgumentParser(description="飞书 Codex 助手机器人")
    parser.add_argument("--config", type=str, default=str(INTEGRATION_ROOT / "config" / "feishu_codex_bot.json"))
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"配置不存在：{config_path}")
        return 1

    config = BotConfig.load(config_path)
    bot = FeishuCodexBot(config)
    bot.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
