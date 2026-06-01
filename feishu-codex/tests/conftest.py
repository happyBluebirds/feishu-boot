"""测试配置。"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# 确保模块可导入
FEISHU_CODEX_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_ROOT = FEISHU_CODEX_ROOT.parent
if str(INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_ROOT))
if str(FEISHU_CODEX_ROOT) not in sys.path:
    sys.path.insert(0, str(FEISHU_CODEX_ROOT))


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """设置测试环境变量。"""
    monkeypatch.setenv("FEISHU_APP_ID", "test_app_id")
    monkeypatch.setenv("FEISHU_APP_SECRET", "test_app_secret")
    monkeypatch.setenv("FEISHU_VERIFICATION_TOKEN", "test_verification_token")
    monkeypatch.setenv("FEISHU_ENCRYPT_KEY", "test_encrypt_key")
    monkeypatch.setenv("OPENAI_API_KEY", "test_api_key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("MODEL_NAME", "gpt-3.5-turbo")


@pytest.fixture
def mock_logger():
    """Mock 日志管理器。"""
    logger = MagicMock()
    logger.log = MagicMock()
    return logger
