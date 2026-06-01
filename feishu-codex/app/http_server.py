"""HTTP 回调模式 - FastAPI 服务入口。

提供飞书事件回调接口，支持：
- 健康检查 GET /health
- 飞书事件回调 POST /feishu/events
- Challenge 校验
- 消息事件处理
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# 确保模块可导入
INTEGRATION_ROOT = Path(__file__).resolve().parents[1]
CODEX_ROOT = INTEGRATION_ROOT.parents[1]
integrations_root = CODEX_ROOT / "integrations"
if str(integrations_root) not in sys.path:
    sys.path.insert(0, str(integrations_root))

from feishu_bot_common import FeishuGateway, IncomingTextMessage, BotStateManager
from feishu_bot_common.state_manager import LogManager
from feishu_bot_common.feishu_gateway import create_gateway

from .ai_client import AIClient
from .feishu_codex_bot import BotConfig, FeishuCodexBot


def get_logger(name: str):
    """获取 Python 标准日志器。"""
    import logging
    return logging.getLogger(name)


logger = get_logger(__name__)


class FeishuEventHandler:
    """飞书事件处理器 - 用于 HTTP 回调模式。"""

    def __init__(self, verification_token: str = "", encrypt_key: str = "") -> None:
        self.verification_token = verification_token
        self.encrypt_key = encrypt_key
        self._processed_events: set[str] = set()
        self._max_cache_size = 1000

    def verify_token(self, token: str) -> bool:
        """验证 token 是否匹配。"""
        if not self.verification_token:
            return True  # 未配置则跳过验证
        return token == self.verification_token

    def handle_challenge(self, data: dict[str, Any]) -> dict[str, str] | None:
        """处理 URL 校验 challenge 请求。"""
        if data.get("type") == "url_verification":
            challenge = data.get("challenge")
            if challenge:
                logger.info("Handling URL verification challenge")
                return {"challenge": challenge}
        return None

    def is_duplicate_event(self, event_id: str) -> bool:
        """检查事件是否已处理。"""
        if event_id in self._processed_events:
            return True
        self._processed_events.add(event_id)
        if len(self._processed_events) > self._max_cache_size:
            self._processed_events.clear()
        return False

    def parse_event(self, data: dict[str, Any]) -> dict[str, Any] | None:
        """解析飞书事件。"""
        # challenge 请求
        challenge_resp = self.handle_challenge(data)
        if challenge_resp:
            return {"type": "challenge", "response": challenge_resp}

        # 事件回调
        header = data.get("header", {})
        event_type = header.get("event_type", "")
        event_id = header.get("event_id", "")

        if event_id and self.is_duplicate_event(event_id):
            logger.info(f"Duplicate event ignored: {event_id}")
            return None

        if event_type == "im.message.receive_v1":
            return self._parse_message_event(data.get("event", {}), header)

        logger.info(f"Unhandled event type: {event_type}")
        return None

    def _parse_message_event(self, event: dict[str, Any], header: dict[str, Any]) -> dict[str, Any] | None:
        """解析消息事件。"""
        message = event.get("message", {})
        sender = event.get("sender", {})

        chat_id = message.get("chat_id", "")
        message_id = message.get("message_id", "")
        chat_type = message.get("chat_type", "")
        message_type = message.get("message_type", "")
        content_str = message.get("content", "{}")

        try:
            content = json.loads(content_str) if content_str else {}
        except json.JSONDecodeError:
            content = {}

        text = content.get("text", "").strip()
        sender_id = sender.get("sender_id", {})
        user_id = sender_id.get("user_id", "") or sender_id.get("open_id", "")

        if message_type != "text":
            return {"type": "non_text", "chat_id": chat_id, "message_id": message_id, "message_type": message_type}

        if not text:
            return {"type": "empty", "chat_id": chat_id, "message_id": message_id}

        logger.info(f"Message: chat={chat_id} msg_id={message_id} sender={user_id}")
        return {
            "type": "text",
            "chat_id": chat_id,
            "chat_type": chat_type,
            "message_id": message_id,
            "text": text,
            "user_id": user_id,
        }


# 全局组件
_bot: FeishuCodexBot | None = None
_event_handler: FeishuEventHandler | None = None
_ai_client: AIClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    global _bot, _event_handler, _ai_client

    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # 加载配置
    config_path = Path(os.getenv("BOT_CONFIG", str(INTEGRATION_ROOT / "config" / "feishu_codex_bot.json")))
    if config_path.exists():
        config = BotConfig.load(config_path)
    else:
        config = BotConfig(
            app_id=os.getenv("FEISHU_APP_ID", ""),
            app_secret=os.getenv("FEISHU_APP_SECRET", ""),
        )

    _bot = FeishuCodexBot(config)
    _event_handler = FeishuEventHandler(
        verification_token=os.getenv("FEISHU_VERIFICATION_TOKEN", ""),
        encrypt_key=os.getenv("FEISHU_ENCRYPT_KEY", ""),
    )
    _ai_client = AIClient(logger=_bot.logger)

    logger.info("HTTP server started")
    yield
    logger.info("HTTP server shutting down")


app = FastAPI(
    title="飞书 Codex 机器人 HTTP 服务",
    description="飞书机器人 HTTP 回调服务",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """健康检查接口。"""
    return {"status": "ok"}


@app.get("/debug/config")
async def debug_config():
    """配置检查（不返回真实密钥）。"""
    return {
        "feishu_app_id": bool(os.getenv("FEISHU_APP_ID")),
        "feishu_app_secret": bool(os.getenv("FEISHU_APP_SECRET")),
        "feishu_verification_token": bool(os.getenv("FEISHU_VERIFICATION_TOKEN")),
        "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
    }


@app.post("/feishu/events")
async def feishu_events(request: Request):
    """飞书事件回调接口。"""
    try:
        data = await request.json()

        # challenge 请求
        if data.get("type") == "url_verification":
            challenge = data.get("challenge")
            if challenge:
                return {"challenge": challenge}

        # 事件回调
        event_data = _event_handler.parse_event(data)
        if not event_data:
            return {"code": 0, "msg": "success"}

        if event_data.get("type") == "challenge":
            return event_data["response"]

        # 文本消息 - 异步处理
        if event_data.get("type") == "text":
            asyncio.create_task(
                _handle_text_message(
                    chat_id=event_data["chat_id"],
                    message_id=event_data["message_id"],
                    text=event_data["text"],
                    user_id=event_data["user_id"],
                )
            )

        elif event_data.get("type") == "non_text":
            _bot.send_text(event_data["chat_id"], "仅支持文本消息。发送「帮助」查看命令。")

        elif event_data.get("type") == "empty":
            _bot.send_text(event_data["chat_id"], "收到空消息。发送「帮助」查看命令。")

        return {"code": 0, "msg": "success"}

    except Exception as e:
        logger.error(f"Event handling error: {type(e).__name__}: {e}")
        return JSONResponse(status_code=500, content={"code": -1, "msg": "Internal server error"})


async def _handle_text_message(chat_id: str, message_id: str, text: str, user_id: str) -> None:
    """异步处理文本消息 - 优先使用 bot 命令处理，否则调用 AI。"""
    try:
        # 先尝试作为命令处理
        bot = _bot
        if text.strip() in ("帮助", "/help", "help", "状态", "/status", "status",
                            "停止", "/stop", "stop", "目录别名", "别名"):
            bot.handle_command(chat_id, text)
            return

        if text.strip().startswith(("目录 ", "目录\t", "运行 ", "run ")):
            bot.handle_command(chat_id, text)
            return

        # 作为 AI 问题处理
        if _ai_client and _ai_client.api_key:
            response = await _ai_client.ask_ai(user_id, text, {"system_prompt": "你是一个有用的AI助手。"})
            bot.send_text(chat_id, response)
        else:
            # 回退到 Codex CLI
            bot.handle_command(chat_id, text)

    except Exception as e:
        logger.error(f"Handle message failed: {type(e).__name__}")
        _bot.send_text(chat_id, "消息处理失败，请稍后再试。")


def main():
    """启动 HTTP 服务。"""
    import uvicorn

    port = int(os.getenv("HTTP_PORT", "8000"))
    host = os.getenv("HTTP_HOST", "0.0.0.0")

    uvicorn.run(
        "app.http_server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
