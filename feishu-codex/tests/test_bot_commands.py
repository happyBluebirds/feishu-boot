"""机器人命令测试。"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# 确保模块可导入
FEISHU_CODEX_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_ROOT = FEISHU_CODEX_ROOT.parent
if str(INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_ROOT))

from app.feishu_codex_bot import BotConfig, FeishuCodexBot


def _make_bot(tmp_path: Path) -> FeishuCodexBot:
    """创建测试用机器人实例。"""
    config = BotConfig(
        app_id="test",
        app_secret="test",
        codex_path="echo",
        default_cwd=str(tmp_path),
        state_path=str(tmp_path / "state.json"),
        log_path=str(tmp_path / "bot.log"),
    )
    return FeishuCodexBot(config)


def test_help_command(tmp_path):
    """测试帮助命令。"""
    bot = _make_bot(tmp_path)
    sent_texts = []
    bot.send_text = lambda chat_id, text: sent_texts.append((chat_id, text))

    bot.handle_command("chat_001", "帮助")
    assert len(sent_texts) == 1
    assert "运行" in sent_texts[0][1]
    assert "停止" in sent_texts[0][1]


def test_status_command(tmp_path):
    """测试状态命令。"""
    bot = _make_bot(tmp_path)
    sent_texts = []
    bot.send_text = lambda chat_id, text: sent_texts.append((chat_id, text))

    bot.handle_command("chat_001", "状态")
    assert len(sent_texts) == 1
    assert "状态" in sent_texts[0][1]


def test_directory_alias_command(tmp_path):
    """测试目录别名命令。"""
    config = BotConfig(
        app_id="test",
        app_secret="test",
        codex_path="echo",
        default_cwd=str(tmp_path),
        cwd_aliases={"work": str(tmp_path)},
        state_path=str(tmp_path / "state.json"),
        log_path=str(tmp_path / "bot.log"),
    )
    bot = FeishuCodexBot(config)
    sent_texts = []
    bot.send_text = lambda chat_id, text: sent_texts.append((chat_id, text))

    bot.handle_command("chat_001", "目录别名")
    assert len(sent_texts) == 1
    assert "work" in sent_texts[0][1]


def test_empty_command_ignored(tmp_path):
    """测试空命令被忽略。"""
    bot = _make_bot(tmp_path)
    sent_texts = []
    bot.send_text = lambda chat_id, text: sent_texts.append((chat_id, text))

    bot.handle_command("chat_001", "")
    bot.handle_command("chat_001", "   ")
    assert len(sent_texts) == 0


def test_split_text_short(tmp_path):
    """测试短文本不拆分。"""
    bot = _make_bot(tmp_path)
    chunks = bot.gateway.split_text("short text")
    assert chunks == ["short text"]


def test_split_text_long(tmp_path):
    """测试长文本拆分。"""
    bot = _make_bot(tmp_path)
    long_text = "x" * 5000
    chunks = bot.gateway.split_text(long_text)
    assert len(chunks) > 1
