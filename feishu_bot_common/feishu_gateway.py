"""飞书消息网关 - WebSocket 长连接收发、消息分片、发送重试。

所有飞书机器人的消息边界，不包含任何业务逻辑。
"""

from __future__ import annotations

import json
import site
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any


def _ensure_lark_import(integration_root: Path) -> None:
    """确保 lark_oapi 可导入，优先用 vendor 目录兜底。"""
    try:
        user_site = site.getusersitepackages()
    except Exception:
        user_site = ""
    if user_site and user_site not in sys.path:
        sys.path.append(user_site)

    try:
        import lark_oapi  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    vendor = integration_root / "vendor"
    if vendor.is_dir():
        vendor_str = str(vendor)
        if vendor_str not in sys.path:
            sys.path.append(vendor_str)


@dataclass
class FeishuGatewayConfig:
    """飞书消息网关配置。"""
    app_id: str
    app_secret: str
    reply_max_chars: int = 3500
    retry_count: int = 3
    retry_delay_seconds: float = 1.5


@dataclass(frozen=True)
class IncomingTextMessage:
    """标准化的飞书文本消息。"""
    chat_id: str
    message_id: str
    text: str
    raw_content: str


class FeishuGateway:
    """飞书 OpenAPI 消息网关。

    职责：WebSocket 长连接监听、文本/图片发送、消息分片、发送重试。
    不包含任何业务逻辑（命令解析、状态管理等由调用方负责）。
    """

    def __init__(
        self,
        client: Any,
        send_lock: threading.Lock,
        config: FeishuGatewayConfig,
        log_fn: Callable[[str], None],
    ) -> None:
        self.client = client
        self.send_lock = send_lock
        self.config = config
        self.log = log_fn

    def split_text(self, text: str) -> list[str]:
        """将长文本拆分为飞书友好的分片。"""
        text = text.strip() or "(空消息)"
        limit = max(200, self.config.reply_max_chars)
        if len(text) <= limit:
            return [text]

        chunks: list[str] = []
        remaining = text
        while len(remaining) > limit:
            cut = remaining.rfind("\n", 0, limit)
            if cut <= 0:
                cut = limit
            chunks.append(remaining[:cut])
            remaining = remaining[cut:].lstrip("\n")
        if remaining:
            chunks.append(remaining)

        total = len(chunks)
        return [f"({index}/{total})\n{chunk}" for index, chunk in enumerate(chunks, start=1)]

    def start_text_listener(
        self,
        on_text: Callable[[IncomingTextMessage], None],
        on_non_text: Callable[[str, str], None],
        on_empty_text: Callable[[str], None],
    ) -> None:
        """启动飞书长连接监听。阻塞直到中断。"""
        import lark_oapi as lark

        # 看门狗：跟踪最后一次收到飞书事件的时间，超时则强制断开触发重连。
        last_event_time = time.time()
        last_event_lock = threading.Lock()
        watchdog_stop = threading.Event()

        def touch_event_time() -> None:
            with last_event_lock:
                nonlocal last_event_time
                last_event_time = time.time()

        def handle_im_message(data: Any) -> None:
            try:
                touch_event_time()
                event = data.event
                chat_id = event.message.chat_id
                message_type = event.message.message_type
                if message_type != "text":
                    on_non_text(chat_id, message_type)
                    return

                raw_content = str(event.message.content or "")
                content = json.loads(raw_content)
                raw_text = str(content.get("text", "")).strip()
                if not raw_text:
                    on_empty_text(chat_id)
                    return

                on_text(
                    IncomingTextMessage(
                        chat_id=chat_id,
                        message_id=str(getattr(event.message, "message_id", "") or ""),
                        text=raw_text,
                        raw_content=raw_content,
                    )
                )
            except Exception as exc:
                self.log(f"handle message failed error={exc}")

        event_handler = (
            lark.EventDispatcherHandler.builder("", "")
            .register_p2_im_message_receive_v1(handle_im_message)
            .register_p2_im_message_message_read_v1(lambda data: None)
            .build()
        )

        def _watchdog_check(ws_ref: Any) -> None:
            """后台线程：长时间无飞书事件时强制关闭 WebSocket 触发重连。"""
            while not watchdog_stop.is_set():
                watchdog_stop.wait(timeout=60)
                if watchdog_stop.is_set():
                    break
                with last_event_lock:
                    elapsed = time.time() - last_event_time
                if elapsed > 300:
                    conn = getattr(ws_ref, "_conn", None)
                    if conn is not None:
                        self.log(f"WebSocket watchdog: no event for {elapsed:.0f}s, forcing reconnect")
                        try:
                            import asyncio
                            loop = getattr(ws_ref, "_loop", None)
                            if loop is None:
                                # lark SDK 内部 event loop
                                try:
                                    loop = asyncio.get_event_loop()
                                except RuntimeError:
                                    loop = None
                            if loop and loop.is_running():
                                asyncio.run_coroutine_threadsafe(conn.close(), loop)
                            else:
                                # fallback: 直接关闭底层 transport
                                transport = getattr(conn, "transport", None)
                                if transport:
                                    transport.close()
                        except Exception as exc:
                            self.log(f"WebSocket watchdog force close failed: {exc}")
                    # 无论是否成功关闭，重置计时避免反复触发
                    touch_event_time()

        ws_client = lark.ws.Client(
            self.config.app_id,
            self.config.app_secret,
            event_handler=event_handler,
            log_level=lark.LogLevel.INFO,
        )

        watchdog_thread = threading.Thread(
            target=_watchdog_check, args=(ws_client,), daemon=True
        )
        watchdog_thread.start()

        ws_reconnect_delay = 3
        ws_max_delay = 60
        try:
            while True:
                try:
                    touch_event_time()
                    ws_client.start()
                except KeyboardInterrupt:
                    self.log("bot stopped by user")
                    break
                except Exception as exc:
                    self.log(f"WebSocket disconnected error={exc}, reconnecting in {ws_reconnect_delay}s...")
                    time.sleep(ws_reconnect_delay)
                    ws_reconnect_delay = min(ws_reconnect_delay * 2, ws_max_delay)
        finally:
            watchdog_stop.set()

    def send_text(self, chat_id: str, text: str) -> None:
        """发送纯文本飞书消息，支持分片和重试。"""
        import lark_oapi as lark
        from lark_oapi.api.im.v1 import (
            CreateMessageRequest,
            CreateMessageRequestBody,
            CreateMessageResponse,
        )

        for chunk in self.split_text(text):
            last_error: Exception | None = None
            for attempt in range(1, self.config.retry_count + 1):
                try:
                    request = (
                        CreateMessageRequest.builder()
                        .receive_id_type("chat_id")
                        .request_body(
                            CreateMessageRequestBody.builder()
                            .receive_id(chat_id)
                            .msg_type("text")
                            .content(json.dumps({"text": chunk}, ensure_ascii=False))
                            .build()
                        )
                        .build()
                    )
                    with self.send_lock:
                        response: CreateMessageResponse = self.client.im.v1.message.create(request)
                    if not response.success():
                        raise RuntimeError(f"send message failed: code={response.code} msg={response.msg}")
                    last_error = None
                    break
                except Exception as exc:
                    last_error = exc
                    self.log(f"send text retry chat={chat_id} attempt={attempt}/{self.config.retry_count} error={exc}")
                    if attempt < self.config.retry_count:
                        time.sleep(self.config.retry_delay_seconds)
            if last_error is not None:
                raise last_error

    def send_image(self, chat_id: str, image_path: Path) -> None:
        """上传本地图片并发送到飞书聊天，支持重试。"""
        import lark_oapi as lark
        from lark_oapi.api.im.v1 import (
            CreateImageRequest,
            CreateImageRequestBody,
            CreateImageResponse,
            CreateMessageRequest,
            CreateMessageRequestBody,
            CreateMessageResponse,
        )

        last_error: Exception | None = None
        for attempt in range(1, self.config.retry_count + 1):
            try:
                with image_path.open("rb") as image_file:
                    upload_request = (
                        CreateImageRequest.builder()
                        .request_body(
                            CreateImageRequestBody.builder()
                            .image_type("message")
                            .image(image_file)
                            .build()
                        )
                        .build()
                    )
                    with self.send_lock:
                        upload_response: CreateImageResponse = self.client.im.v1.image.create(upload_request)
                if not upload_response.success() or not upload_response.data or not upload_response.data.image_key:
                    raise RuntimeError(f"upload image failed: code={upload_response.code} msg={upload_response.msg}")

                request = (
                    CreateMessageRequest.builder()
                    .receive_id_type("chat_id")
                    .request_body(
                        CreateMessageRequestBody.builder()
                        .receive_id(chat_id)
                        .msg_type("image")
                        .content(json.dumps({"image_key": upload_response.data.image_key}, ensure_ascii=False))
                        .build()
                    )
                    .build()
                )
                with self.send_lock:
                    response: CreateMessageResponse = self.client.im.v1.message.create(request)
                if not response.success():
                    raise RuntimeError(f"send image failed: code={response.code} msg={response.msg}")
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                self.log(f"send image retry chat={chat_id} attempt={attempt}/{self.config.retry_count} error={exc}")
                if attempt < self.config.retry_count:
                    time.sleep(self.config.retry_delay_seconds)
        if last_error is not None:
            raise last_error


def create_gateway(
    app_id: str,
    app_secret: str,
    integration_root: Path,
    log_fn: Callable[[str], None],
    reply_max_chars: int = 3500,
) -> FeishuGateway:
    """便捷工厂：创建并返回一个可用的 FeishuGateway 实例。"""
    import lark_oapi as lark

    _ensure_lark_import(integration_root)

    client = lark.Client.builder().app_id(app_id).app_secret(app_secret).build()
    config = FeishuGatewayConfig(
        app_id=app_id,
        app_secret=app_secret,
        reply_max_chars=reply_max_chars,
    )
    return FeishuGateway(client, threading.Lock(), config, log_fn)
