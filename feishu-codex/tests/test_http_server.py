"""HTTP 服务测试。"""

import os
import sys
from pathlib import Path

# 确保模块可导入
FEISHU_CODEX_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_ROOT = FEISHU_CODEX_ROOT.parent
if str(INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_ROOT))

from fastapi.testclient import TestClient


def test_health_check():
    """测试健康检查。"""
    # 需要重新导入以确保 lifespan 初始化
    from app.http_server import app, _bot, _event_handler
    from app.http_server import FeishuEventHandler, FeishuCodexBot
    from app.http_server import app as _app

    import app.http_server as server_module
    server_module._event_handler = FeishuEventHandler(verification_token="test_token")
    # _bot 可以是 None，health 不需要它

    client = TestClient(_app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_challenge_endpoint():
    """测试 challenge 端点。"""
    import app.http_server as server_module
    from app.http_server import app, FeishuEventHandler

    server_module._event_handler = FeishuEventHandler(verification_token="test_token")

    client = TestClient(app)
    response = client.post("/feishu/events", json={
        "type": "url_verification",
        "challenge": "test_challenge",
        "token": "test_token",
    })
    assert response.status_code == 200
    assert response.json() == {"challenge": "test_challenge"}


def test_debug_config():
    """测试配置检查。"""
    import app.http_server as server_module
    from app.http_server import app, FeishuEventHandler

    server_module._event_handler = FeishuEventHandler()

    client = TestClient(app)
    response = client.get("/debug/config")
    assert response.status_code == 200
    data = response.json()
    assert "feishu_app_id" in data
    assert isinstance(data["feishu_app_id"], bool)
