"""AI/Codex API 调用封装 - 支持 OpenAI-compatible API。

独立于 Codex CLI 的 API 调用能力，用于直接调用 AI 模型。
"""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from feishu_bot_common.state_manager import LogManager


class AIClient:
    """AI 客户端 - 支持 OpenAI-compatible API。"""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model: str = "gpt-3.5-turbo",
        timeout: int = 30,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        logger: LogManager | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.model = model or os.getenv("MODEL_NAME", "gpt-3.5-turbo")
        self.timeout = timeout or int(os.getenv("AI_TIMEOUT", "30"))
        self.max_tokens = max_tokens or int(os.getenv("AI_MAX_TOKENS", "2000"))
        self.temperature = temperature or float(os.getenv("AI_TEMPERATURE", "0.7"))
        self.logger = logger

    def _log(self, msg: str) -> None:
        if self.logger:
            self.logger.log(msg)

    async def ask_ai(
        self,
        user_id: str,
        prompt: str,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """调用 AI 接口获取回复。"""
        if not self.api_key:
            self._log("OPENAI_API_KEY not configured")
            return "当前智能处理服务暂时不可用，请稍后再试。"

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if context and context.get("system_prompt"):
            messages.append({"role": "system", "content": context["system_prompt"]})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    self._log(f"AI response received for user={user_id} len={len(content)}")
                    return content.strip()

                self._log(f"Empty AI response for user={user_id}")
                return "未获取到有效回复，请稍后再试。"

        except httpx.TimeoutException:
            self._log(f"AI request timeout for user={user_id}")
            return "智能处理服务响应超时，请稍后再试。"

        except httpx.HTTPStatusError as e:
            self._log(f"AI request HTTP error: {e.response.status_code}")
            return "当前智能处理服务暂时不可用，请稍后再试。"

        except Exception as e:
            self._log(f"AI request failed: {type(e).__name__}")
            return "当前智能处理服务暂时不可用，请稍后再试。"

    def sync_ask_ai(self, user_id: str, prompt: str, context: Optional[dict[str, Any]] = None) -> str:
        """同步版本的 AI 调用（用于非 async 场景）。"""
        if not self.api_key:
            self._log("OPENAI_API_KEY not configured")
            return "当前智能处理服务暂时不可用，请稍后再试。"

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if context and context.get("system_prompt"):
            messages.append({"role": "system", "content": context["system_prompt"]})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    self._log(f"AI response received for user={user_id} len={len(content)}")
                    return content.strip()

                return "未获取到有效回复，请稍后再试。"

        except Exception as e:
            self._log(f"AI request failed: {type(e).__name__}")
            return "当前智能处理服务暂时不可用，请稍后再试。"
