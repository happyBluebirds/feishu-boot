"""飞书机器人公共模块。

提供 Feishu 消息网关、状态管理、日志工具等共享组件，
供 feishu-claude-v2 和 feishu-codex 等独立机器人复用。
"""

# 从飞书消息网关模块导出核心类
from .feishu_gateway import FeishuGateway, FeishuGatewayConfig, IncomingTextMessage
# 从 Hook 工具模块导出时间格式化函数
from .hook_utils import format_ts, format_duration
# 从状态管理模块导出机器人状态管理器
from .state_manager import BotStateManager

__all__ = [
    "FeishuGateway",          # 飞书消息网关主类
    "FeishuGatewayConfig",    # 网关配置数据类
    "IncomingTextMessage",    # 标准化文本消息数据类
    "BotStateManager",        # 按 chat 持久化的状态管理器
    "format_ts",              # Unix 时间戳格式化
    "format_duration",        # 耗时格式化
]
