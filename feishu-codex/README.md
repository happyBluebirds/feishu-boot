# 飞书 Codex 助手机器人

通过飞书聊天控制本机 Codex (Claude Code) CLI，支持后台任务执行、状态查询、目录切换、AI API 对话等功能。

## 功能

| 命令 | 说明 |
|------|------|
| `运行 <任务>` | 后台执行 Codex 任务 |
| `继续` | 继续上一轮对话 |
| `停止` | 终止当前任务 |
| `状态` | 查询当前会话状态 |
| `目录 <路径>` | 切换工作目录 |
| `目录别名` | 显示已配置的目录别名 |
| `帮助` | 显示帮助信息 |
| 直接发送文本 | 作为任务执行或 AI 对话（HTTP 模式） |

## 运行模式

### 模式 1：WebSocket 长连接（推荐）

实时接收飞书消息，无需公网地址。

```bash
python app/feishu_codex_bot.py --config config/feishu_codex_bot.json
```

### 模式 2：HTTP 回调

支持飞书事件订阅回调，需配置公网地址。

```bash
uvicorn app.http_server:app --host 0.0.0.0 --port 8000
```

HTTP 模式额外能力：
- `GET /health` - 健康检查
- `GET /debug/config` - 配置检查（不返回密钥）
- `POST /feishu/events` - 飞书事件回调（支持 challenge 校验）

## 目录结构

```
feishu-codex/
├── app/
│   ├── feishu_codex_bot.py      # WebSocket 模式主程序
│   ├── feishu_gateway.py        # 飞书消息网关（重导出）
│   ├── ai_client.py             # AI API 调用封装（新增）
│   └── http_server.py           # HTTP 回调模式（新增）
├── tests/
│   ├── conftest.py              # 测试配置
│   ├── test_challenge.py        # Challenge 校验测试
│   ├── test_ai_client.py        # AI 客户端测试
│   ├── test_http_server.py      # HTTP 服务测试
│   └── test_bot_commands.py     # 机器人命令测试
├── config/
│   ├── feishu_codex_bot.json           # 生效配置
│   └── feishu_codex_bot.example.json   # 配置模板
├── hooks/
│   ├── feishu_codex_permission_hook.py # 权限请求 hook
│   └── feishu_codex_turn_hook.py       # 完成通知 hook
├── scripts/
│   ├── start-feishu-codex-bot.ps1      # 启动脚本
│   └── stop-feishu-codex-bot.ps1       # 停止脚本
├── .env.example                 # 环境变量模板（新增）
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

**方式一：JSON 配置（WebSocket 模式）**

```bash
cp config/feishu_codex_bot.example.json config/feishu_codex_bot.json
```

编辑 `config/feishu_codex_bot.json`：

```json
{
  "app_id": "cli_xxxxxxxxxxxxxxxxx",
  "app_secret": "your-feishu-app-secret",
  "codex_path": "claude",
  "default_cwd": "D:\\code\\codex",
  "cwd_aliases": {
    "codex": "D:\\code\\codex"
  },
  "allowed_chat_ids": [],
  "permission_mode": "bypassPermissions",
  "default_model": "",
  "additional_args": [],
  "reply_max_chars": 3500
}
```

**方式二：环境变量（HTTP 模式）**

```bash
cp .env.example .env
```

编辑 `.env` 文件填入飞书和 AI 配置。

### 3. 启动

**WebSocket 模式：**

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-feishu-codex-bot.ps1
```

或：

```bash
python app/feishu_codex_bot.py --config config/feishu_codex_bot.json
```

**HTTP 回调模式：**

```bash
uvicorn app.http_server:app --host 0.0.0.0 --port 8000
```

### 4. 验证

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

## 测试

```bash
pytest -q
```

## 配置说明

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `app_id` | 飞书应用 App ID | 必填 |
| `app_secret` | 飞书应用 Secret | 必填 |
| `codex_path` | Codex CLI 路径 | `claude` |
| `default_cwd` | 默认工作目录 | 当前目录 |
| `cwd_aliases` | 目录别名映射 | `{}` |
| `allowed_chat_ids` | 允许的聊天 ID 白名单（空=不限制） | `[]` |
| `permission_mode` | 授权模式 | `bypassPermissions` |
| `default_model` | 默认模型（空=CLI 默认） | `""` |
| `additional_args` | 额外 CLI 参数 | `[]` |
| `reply_max_chars` | 单条消息最大字符数 | `3500` |

### AI API 配置（HTTP 模式可选）

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `OPENAI_API_KEY` | AI API Key | - |
| `OPENAI_BASE_URL` | AI API 地址 | `https://api.openai.com/v1` |
| `MODEL_NAME` | 模型名称 | `gpt-3.5-turbo` |
| `AI_TIMEOUT` | 超时时间（秒） | `30` |
| `AI_MAX_TOKENS` | 最大 token 数 | `2000` |
| `AI_TEMPERATURE` | 温度参数 | `0.7` |

## 飞书后台配置

### 1. 创建企业自建应用

登录飞书开放平台，创建企业自建应用。

### 2. 启用机器人能力

在应用详情页添加"机器人"能力。

### 3. 获取凭证

获取 App ID 和 App Secret，填入配置。

### 4. 配置事件订阅（HTTP 模式）

- 进入"事件订阅"页面
- 设置请求地址：`https://your-domain.com/feishu/events`
- 记录 Verification Token 和 Encrypt Key

### 5. 订阅消息事件

订阅 `im.message.receive_v1` 事件。

### 6. 申请权限

- `im:message` - 获取与发送消息
- `im:message:send_as_bot` - 以应用身份发送消息

### 7. 发布应用

创建版本并提交审核，审核通过后发布。

### 8. 本地调试

使用 ngrok 获取公网地址：

```bash
ngrok http 8000
```

## 配置 Claude Hooks（可选）

在 Claude Code 的 settings 中添加 hooks：

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cmd /c python D:\\code\\codex\\integrations\\feishu-codex\\hooks\\feishu_codex_permission_hook.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cmd /c python D:\\code\\codex\\integrations\\feishu-codex\\hooks\\feishu_codex_turn_hook.py"
          }
        ]
      }
    ]
  }
}
```

## 输出目录

运行时产物统一存放在 `D:\code\codex\outputs\feishu-codex\`：

- `state/` - 会话状态、授权队列
- `logs/` - 主日志、hook 日志

## 排障

- **收不到消息**：检查日志文件是否有 `recv`
- **任务没执行**：检查 state 文件中的 `status` 和 `last_error`
- **权限请求没到飞书**：检查 hook 日志
- **Challenge 验证失败**：检查 `FEISHU_VERIFICATION_TOKEN` 配置

## 安全注意事项

- 不要将真实密钥提交到代码仓库
- 使用环境变量或 JSON 配置文件管理敏感信息
- 生产环境建议启用 HTTPS
- 定期轮换 API Key

## 测试结果

```
tests/test_ai_client.py::test_ask_ai_success PASSED
tests/test_ai_client.py::test_ask_ai_no_api_key PASSED
tests/test_ai_client.py::test_ask_ai_timeout PASSED
tests/test_ai_client.py::test_sync_ask_ai_success PASSED
tests/test_ai_client.py::test_sync_ask_ai_no_key PASSED
tests/test_bot_commands.py::test_help_command PASSED
tests/test_bot_commands.py::test_status_command PASSED
tests/test_bot_commands.py::test_directory_alias_command PASSED
tests/test_bot_commands.py::test_empty_command_ignored PASSED
tests/test_bot_commands.py::test_split_text_short PASSED
tests/test_bot_commands.py::test_split_text_long PASSED
tests/test_challenge.py::test_handle_challenge PASSED
tests/test_challenge.py::test_handle_non_challenge PASSED
tests/test_challenge.py::test_verify_token PASSED
tests/test_challenge.py::test_verify_token_skip_when_empty PASSED
tests/test_challenge.py::test_duplicate_event_detection PASSED
tests/test_challenge.py::test_parse_message_event PASSED
tests/test_challenge.py::test_parse_empty_text PASSED
tests/test_challenge.py::test_parse_non_text_message PASSED
tests/test_http_server.py::test_health_check PASSED
tests/test_http_server.py::test_challenge_endpoint PASSED
tests/test_http_server.py::test_debug_config PASSED

22 passed
```

## 变更记录

### 2026-05-28

- 修复 `--quiet` 参数不兼容问题，改用 `codex exec` 子命令
- 修复 subprocess 卡住问题，添加 `stdin=subprocess.DEVNULL`
- 新增 HTTP 回调模式（FastAPI）
- 新增 AI API 调用封装（OpenAI-compatible）
- 新增 `.env.example` 环境变量模板
- 新增 22 个自动化测试
- 新增行级注释

## 测试结果

```
tests/test_ai_client.py::test_ask_ai_success PASSED
tests/test_ai_client.py::test_ask_ai_no_api_key PASSED
tests/test_ai_client.py::test_ask_ai_timeout PASSED
tests/test_ai_client.py::test_sync_ask_ai_success PASSED
tests/test_ai_client.py::test_sync_ask_ai_no_key PASSED
tests/test_bot_commands.py::test_help_command PASSED
tests/test_bot_commands.py::test_status_command PASSED
tests/test_bot_commands.py::test_directory_alias_command PASSED
tests/test_bot_commands.py::test_empty_command_ignored PASSED
tests/test_bot_commands.py::test_split_text_short PASSED
tests/test_bot_commands.py::test_split_text_long PASSED
tests/test_challenge.py::test_handle_challenge PASSED
tests/test_challenge.py::test_handle_non_challenge PASSED
tests/test_challenge.py::test_verify_token PASSED
tests/test_challenge.py::test_verify_token_skip_when_empty PASSED
tests/test_challenge.py::test_duplicate_event_detection PASSED
tests/test_challenge.py::test_parse_message_event PASSED
tests/test_challenge.py::test_parse_empty_text PASSED
tests/test_challenge.py::test_parse_non_text_message PASSED
tests/test_http_server.py::test_health_check PASSED
tests/test_http_server.py::test_challenge_endpoint PASSED
tests/test_http_server.py::test_debug_config PASSED

22 passed
```

## 变更记录

### 2026-05-28

- 修复 `--quiet` 参数不兼容问题，改用 `codex exec` 子命令
- 修复 subprocess 卡住问题，添加 `stdin=subprocess.DEVNULL`
- 新增 HTTP 回调模式（FastAPI）
- 新增 AI API 调用封装（OpenAI-compatible）
- 新增 `.env.example` 环境变量模板
- 新增 22 个自动化测试
- 新增行级注释

## 测试结果

```
tests/test_ai_client.py::test_ask_ai_success PASSED
tests/test_ai_client.py::test_ask_ai_no_api_key PASSED
tests/test_ai_client.py::test_ask_ai_timeout PASSED
tests/test_ai_client.py::test_sync_ask_ai_success PASSED
tests/test_ai_client.py::test_sync_ask_ai_no_key PASSED
tests/test_bot_commands.py::test_help_command PASSED
tests/test_bot_commands.py::test_status_command PASSED
tests/test_bot_commands.py::test_directory_alias_command PASSED
tests/test_bot_commands.py::test_empty_command_ignored PASSED
tests/test_bot_commands.py::test_split_text_short PASSED
tests/test_bot_commands.py::test_split_text_long PASSED
tests/test_challenge.py::test_handle_challenge PASSED
tests/test_challenge.py::test_handle_non_challenge PASSED
tests/test_challenge.py::test_verify_token PASSED
tests/test_challenge.py::test_verify_token_skip_when_empty PASSED
tests/test_challenge.py::test_duplicate_event_detection PASSED
tests/test_challenge.py::test_parse_message_event PASSED
tests/test_challenge.py::test_parse_empty_text PASSED
tests/test_challenge.py::test_parse_non_text_message PASSED
tests/test_http_server.py::test_health_check PASSED
tests/test_http_server.py::test_challenge_endpoint PASSED
tests/test_http_server.py::test_debug_config PASSED

22 passed
```

## 变更记录

### 2026-05-28

- 修复 `--quiet` 参数不兼容问题，改用 `codex exec` 子命令
- 修复 subprocess 卡住问题，添加 `stdin=subprocess.DEVNULL`
- 新增 HTTP 回调模式（FastAPI）
- 新增 AI API 调用封装（OpenAI-compatible）
- 新增 `.env.example` 环境变量模板
- 新增 22 个自动化测试
- 新增行级注释

## 测试结果

```
tests/test_ai_client.py::test_ask_ai_success PASSED
tests/test_ai_client.py::test_ask_ai_no_api_key PASSED
tests/test_ai_client.py::test_ask_ai_timeout PASSED
tests/test_ai_client.py::test_sync_ask_ai_success PASSED
tests/test_ai_client.py::test_sync_ask_ai_no_key PASSED
tests/test_bot_commands.py::test_help_command PASSED
tests/test_bot_commands.py::test_status_command PASSED
tests/test_bot_commands.py::test_directory_alias_command PASSED
tests/test_bot_commands.py::test_empty_command_ignored PASSED
tests/test_bot_commands.py::test_split_text_short PASSED
tests/test_bot_commands.py::test_split_text_long PASSED
tests/test_challenge.py::test_handle_challenge PASSED
tests/test_challenge.py::test_handle_non_challenge PASSED
tests/test_challenge.py::test_verify_token PASSED
tests/test_challenge.py::test_verify_token_skip_when_empty PASSED
tests/test_challenge.py::test_duplicate_event_detection PASSED
tests/test_challenge.py::test_parse_message_event PASSED
tests/test_challenge.py::test_parse_empty_text PASSED
tests/test_challenge.py::test_parse_non_text_message PASSED
tests/test_http_server.py::test_health_check PASSED
tests/test_http_server.py::test_challenge_endpoint PASSED
tests/test_http_server.py::test_debug_config PASSED

22 passed
```

## 变更记录

### 2026-05-28

- 修复 `--quiet` 参数不兼容问题，改用 `codex exec` 子命令
- 修复 subprocess 卡住问题，添加 `stdin=subprocess.DEVNULL`
- 新增 HTTP 回调模式（FastAPI）
- 新增 AI API 调用封装（OpenAI-compatible）
- 新增 `.env.example` 环境变量模板
- 新增 22 个自动化测试
- 新增行级注释

## 测试结果

```
tests/test_ai_client.py::test_ask_ai_success PASSED
tests/test_ai_client.py::test_ask_ai_no_api_key PASSED
tests/test_ai_client.py::test_ask_ai_timeout PASSED
tests/test_ai_client.py::test_sync_ask_ai_success PASSED
tests/test_ai_client.py::test_sync_ask_ai_no_key PASSED
tests/test_bot_commands.py::test_help_command PASSED
tests/test_bot_commands.py::test_status_command PASSED
tests/test_bot_commands.py::test_directory_alias_command PASSED
tests/test_bot_commands.py::test_empty_command_ignored PASSED
tests/test_bot_commands.py::test_split_text_short PASSED
tests/test_bot_commands.py::test_split_text_long PASSED
tests/test_challenge.py::test_handle_challenge PASSED
tests/test_challenge.py::test_handle_non_challenge PASSED
tests/test_challenge.py::test_verify_token PASSED
tests/test_challenge.py::test_verify_token_skip_when_empty PASSED
tests/test_challenge.py::test_duplicate_event_detection PASSED
tests/test_challenge.py::test_parse_message_event PASSED
tests/test_challenge.py::test_parse_empty_text PASSED
tests/test_challenge.py::test_parse_non_text_message PASSED
tests/test_http_server.py::test_health_check PASSED
tests/test_http_server.py::test_challenge_endpoint PASSED
tests/test_http_server.py::test_debug_config PASSED

22 passed
```

## 变更记录

### 2026-05-28

- 修复 `--quiet` 参数不兼容问题，改用 `codex exec` 子命令
- 修复 subprocess 卡住问题，添加 `stdin=subprocess.DEVNULL`
- 新增 HTTP 回调模式（FastAPI）
- 新增 AI API 调用封装（OpenAI-compatible）
- 新增 `.env.example` 环境变量模板
- 新增 22 个自动化测试
- 新增行级注释

## 后续扩展

- 支持群聊 @机器人 触发
- 支持卡片消息交互
- 添加请求频率限制
- 支持多轮对话上下文
- Dockerfile 部署
