"""飞书 challenge 校验测试。"""

import sys
from pathlib import Path

# 确保模块可导入
FEISHU_CODEX_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_ROOT = FEISHU_CODEX_ROOT.parent
if str(INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_ROOT))

from app.http_server import FeishuEventHandler


def test_handle_challenge():
    """测试 challenge 处理。"""
    handler = FeishuEventHandler(verification_token="test_token")
    data = {
        "type": "url_verification",
        "challenge": "test_challenge_value",
        "token": "test_token",
    }
    result = handler.handle_challenge(data)
    assert result == {"challenge": "test_challenge_value"}


def test_handle_non_challenge():
    """测试非 challenge 请求。"""
    handler = FeishuEventHandler(verification_token="test_token")
    data = {"type": "event_callback", "event": {}}
    result = handler.handle_challenge(data)
    assert result is None


def test_verify_token():
    """测试 token 验证。"""
    handler = FeishuEventHandler(verification_token="test_token")
    assert handler.verify_token("test_token") is True
    assert handler.verify_token("wrong_token") is False


def test_verify_token_skip_when_empty():
    """测试未配置 token 时跳过验证。"""
    handler = FeishuEventHandler(verification_token="")
    assert handler.verify_token("any_token") is True


def test_duplicate_event_detection():
    """测试重复事件检测。"""
    handler = FeishuEventHandler()
    assert handler.is_duplicate_event("event_001") is False
    assert handler.is_duplicate_event("event_001") is True
    assert handler.is_duplicate_event("event_002") is False


def test_parse_message_event():
    """测试消息事件解析。"""
    handler = FeishuEventHandler()
    data = {
        "header": {
            "event_id": "evt_001",
            "event_type": "im.message.receive_v1",
        },
        "event": {
            "message": {
                "chat_id": "chat_001",
                "message_id": "msg_001",
                "chat_type": "p2p",
                "message_type": "text",
                "content": '{"text":"hello"}',
            },
            "sender": {
                "sender_id": {"user_id": "user_001"},
            },
        },
    }
    result = handler.parse_event(data)
    assert result is not None
    assert result["type"] == "text"
    assert result["chat_id"] == "chat_001"
    assert result["text"] == "hello"
    assert result["user_id"] == "user_001"


def test_parse_empty_text():
    """测试空消息解析。"""
    handler = FeishuEventHandler()
    data = {
        "header": {
            "event_id": "evt_002",
            "event_type": "im.message.receive_v1",
        },
        "event": {
            "message": {
                "chat_id": "chat_001",
                "message_id": "msg_002",
                "chat_type": "p2p",
                "message_type": "text",
                "content": '{"text":""}',
            },
            "sender": {
                "sender_id": {"user_id": "user_001"},
            },
        },
    }
    result = handler.parse_event(data)
    assert result is not None
    assert result["type"] == "empty"


def test_parse_non_text_message():
    """测试非文本消息解析。"""
    handler = FeishuEventHandler()
    data = {
        "header": {
            "event_id": "evt_003",
            "event_type": "im.message.receive_v1",
        },
        "event": {
            "message": {
                "chat_id": "chat_001",
                "message_id": "msg_003",
                "chat_type": "p2p",
                "message_type": "image",
                "content": "{}",
            },
            "sender": {
                "sender_id": {"user_id": "user_001"},
            },
        },
    }
    result = handler.parse_event(data)
    assert result is not None
    assert result["type"] == "non_text"
