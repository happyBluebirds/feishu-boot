# Feishu Codex Bridge

[中文](README.zh-CN.md) | English

Control local Codex CLI workflows from Feishu/Lark chat.

Feishu Codex Bridge is the Codex-focused module in Feishu Boot. It receives Feishu/Lark messages, runs local Codex CLI tasks in a subprocess, tracks per-chat state, and sends results back to chat while keeping source code and execution state on the local machine.

## Features

- Feishu/Lark long-connection bot for local Codex CLI tasks.
- Optional HTTP callback server for Feishu/Lark event subscriptions.
- Per-chat task state, stop command, status command, and working-directory switching.
- Shared gateway utilities from `feishu_bot_common`.
- Sanitized example config for public repositories.
- Tests for command routing, challenge handling, HTTP mode, and AI API wrapper behavior.

## Commands

| Command | Description |
|---|---|
| `运行 <task>` | Start a Codex task in the configured workspace. |
| `继续` | Continue from the last conversation context. |
| `停止` | Stop the current task for the chat. |
| `状态` | Show current task state. |
| `目录 <path-or-alias>` | Switch working directory. |
| `目录别名` | List configured directory aliases. |
| `帮助` | Show help. |
| plain text | Treated as a task in WebSocket mode or AI chat input in HTTP mode. |

## Runtime Modes

### WebSocket Long Connection

Recommended for local usage because it does not require a public callback URL.

```powershell
python app\feishu_codex_bot.py --config config\feishu_codex_bot.json
```

### HTTP Callback

Useful when you want Feishu/Lark event subscription callbacks.

```powershell
uvicorn app.http_server:app --host 0.0.0.0 --port 8000
```

HTTP endpoints:

- `GET /health`
- `GET /debug/config`
- `POST /feishu/events`

## Quick Start

```powershell
python -m pip install -r requirements.txt
Copy-Item config\feishu_codex_bot.example.json config\feishu_codex_bot.json
```

Edit `config/feishu_codex_bot.json`, then run:

```powershell
python app\feishu_codex_bot.py --config config\feishu_codex_bot.json
```

## Configuration

Important fields:

- `app_id`: Feishu/Lark app ID.
- `app_secret`: Feishu/Lark app secret.
- `codex_path`: Codex executable name or local executable path.
- `default_cwd`: Default local workspace for Codex tasks.
- `cwd_aliases`: Friendly names for trusted local workspaces.
- `allowed_chat_ids`: Chat ID allowlist. Configure this before running real tasks.
- `additional_args`: Extra Codex CLI arguments.
- `reply_max_chars`: Maximum length of one reply chunk.

## Security

Do not use this bot in shared or untrusted chats without setting `allowed_chat_ids`.

The example config uses a placeholder chat ID intentionally:

```json
"allowed_chat_ids": ["oc_xxxxxxxxxxxxxxxxx"]
```

Replace it with your real trusted Feishu/Lark chat IDs. Keep real configs, credentials, logs, screenshots, state files, and local paths out of Git.

## Tests

```powershell
python -m pip install -r requirements.txt
python -m pip install pytest
pytest -q
```

## Roadmap

- Safer task lifecycle management for Codex subprocesses.
- PR review workflow examples.
- Issue triage workflow examples.
- Release-note generation workflow examples.
- Command allowlist and denylist support.
- Log redaction and rate limiting.

## Changelog

### v0.1.0-alpha

- Initial public alpha release as part of Feishu Boot.
- WebSocket and HTTP callback modes.
- Local Codex subprocess bridge.
- Shared Feishu/Lark gateway utilities.
- Sanitized example config and tests.
