# Feishu Codex Bridge

中文 | [English](README.md)

通过飞书/Lark 聊天控制本机 Codex CLI 工作流。

Feishu Codex Bridge 是 Feishu Boot 中面向 Codex 的子模块。它接收飞书/Lark 消息，在本机通过子进程运行 Codex CLI，维护按 chat 隔离的任务状态，并将结果回传到聊天窗口，同时让源码和执行状态保留在本机。

## 功能

- 通过飞书/Lark 长连接机器人运行本机 Codex CLI 任务。
- 提供可选 HTTP 回调服务，支持飞书/Lark 事件订阅。
- 支持按 chat 管理任务状态、停止任务、查询状态和切换工作目录。
- 复用 `feishu_bot_common` 公共网关工具。
- 提供适合公开仓库的脱敏示例配置。
- 覆盖命令路由、challenge 校验、HTTP 模式和 AI API wrapper 的测试。

## 命令

| 命令 | 说明 |
|---|---|
| `运行 <任务>` | 在配置的工作区启动 Codex 任务。 |
| `继续` | 继续上一轮上下文。 |
| `停止` | 停止当前 chat 的任务。 |
| `状态` | 查看当前任务状态。 |
| `目录 <路径或别名>` | 切换工作目录。 |
| `目录别名` | 查看已配置的目录别名。 |
| `帮助` | 显示帮助。 |
| 普通文本 | WebSocket 模式下作为任务，HTTP 模式下作为 AI 对话输入。 |

## 运行模式

### WebSocket 长连接

推荐本机使用，不需要公网回调地址。

```powershell
python app\feishu_codex_bot.py --config config\feishu_codex_bot.json
```

### HTTP 回调

适合接入飞书/Lark 事件订阅回调。

```powershell
uvicorn app.http_server:app --host 0.0.0.0 --port 8000
```

HTTP 端点：

- `GET /health`
- `GET /debug/config`
- `POST /feishu/events`

## 快速开始

```powershell
python -m pip install -r requirements.txt
Copy-Item config\feishu_codex_bot.example.json config\feishu_codex_bot.json
```

修改 `config/feishu_codex_bot.json` 后运行：

```powershell
python app\feishu_codex_bot.py --config config\feishu_codex_bot.json
```

## 配置

重要字段：

- `app_id`：飞书/Lark 应用 ID。
- `app_secret`：飞书/Lark 应用 Secret。
- `codex_path`：Codex 可执行文件名或本机路径。
- `default_cwd`：Codex 任务默认工作目录。
- `cwd_aliases`：可信本机工作区的别名。
- `allowed_chat_ids`：chat ID 白名单，真实任务运行前必须配置。
- `additional_args`：额外 Codex CLI 参数。
- `reply_max_chars`：单条回复最大长度。

## 安全

不要在共享或不可信聊天中使用未配置 `allowed_chat_ids` 的机器人。

示例配置故意使用占位 chat ID：

```json
"allowed_chat_ids": ["oc_xxxxxxxxxxxxxxxxx"]
```

请替换为真实可信的飞书/Lark chat ID。真实配置、凭据、日志、截图、状态文件和本机路径都不应进入 Git。

## 测试

```powershell
python -m pip install -r requirements.txt
python -m pip install pytest
pytest -q
```

## 路线图

- 更安全的 Codex 子进程任务生命周期管理。
- PR review 工作流示例。
- Issue triage 工作流示例。
- Release-note generation 工作流示例。
- 命令 allowlist / denylist。
- 日志脱敏和限流。

## 变更记录

### v0.1.0-alpha

- 作为 Feishu Boot 的一部分首次公开 alpha 发布。
- 支持 WebSocket 和 HTTP 回调模式。
- 支持本机 Codex 子进程桥接。
- 复用飞书/Lark 公共网关工具。
- 提供脱敏示例配置和测试。
