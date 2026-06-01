"""AI 客户端测试。"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# 确保模块可导入
FEISHU_CODEX_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_ROOT = FEISHU_CODEX_ROOT.parent
if str(INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_ROOT))

from app.ai_client import AIClient


@pytest.mark.asyncio
async def test_ask_ai_success(mock_logger):
    """测试 AI 调用成功。"""
    client = AIClient(api_key="test_key", logger=mock_logger)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test response"}}]
    }
    mock_response.raise_for_status = MagicMock()

    mock_async_client = AsyncMock()
    mock_async_client.post = AsyncMock(return_value=mock_response)
    mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
    mock_async_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.ai_client.httpx.AsyncClient", return_value=mock_async_client):
        result = await client.ask_ai("user_1", "hello")
        assert result == "Test response"


@pytest.mark.asyncio
async def test_ask_ai_no_api_key(mock_logger):
    """测试无 API key 时的处理。"""
    client = AIClient(api_key="", logger=mock_logger)
    result = await client.ask_ai("user_1", "hello")
    assert "暂时不可用" in result


@pytest.mark.asyncio
async def test_ask_ai_timeout(mock_logger):
    """测试超时处理。"""
    client = AIClient(api_key="test_key", timeout=1, logger=mock_logger)

    mock_async_client = AsyncMock()
    mock_async_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
    mock_async_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.ai_client.httpx.AsyncClient", return_value=mock_async_client):
        result = await client.ask_ai("user_1", "hello")
        assert "超时" in result


def test_sync_ask_ai_success(mock_logger):
    """测试同步 AI 调用成功。"""
    client = AIClient(api_key="test_key", logger=mock_logger)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Sync response"}}]
    }
    mock_response.raise_for_status = MagicMock()

    mock_sync_client = MagicMock()
    mock_sync_client.post = MagicMock(return_value=mock_response)
    mock_sync_client.__enter__ = MagicMock(return_value=mock_sync_client)
    mock_sync_client.__exit__ = MagicMock(return_value=None)

    with patch("app.ai_client.httpx.Client", return_value=mock_sync_client):
        result = client.sync_ask_ai("user_1", "hello")
        assert result == "Sync response"


def test_sync_ask_ai_no_key(mock_logger):
    """测试同步调用无 API key。"""
    client = AIClient(api_key="", logger=mock_logger)
    result = client.sync_ask_ai("user_1", "hello")
    assert "暂时不可用" in result
