# Feishu Codex Bridge

[中文](README.zh-CN.md) | English

Control local Codex CLI workflows from Feishu/Lark chat.

## Features

- Run Codex tasks from Feishu/Lark chat.
- Continue, stop, and check task status.
- Switch working directories with aliases.
- Support Feishu/Lark long-connection mode.
- Support optional HTTP callback mode.
- Forward permission and completion updates.

## Commands

| Command | Description |
|---|---|
| `运行 <task>` | Run a Codex task |
| `继续` | Continue the previous task |
| `停止` | Stop the current task |
| `状态` | Show current session status |
| `目录 <path>` | Switch working directory |
| `目录别名` | Show configured directory aliases |
| `帮助` | Show help |

## Runtime Modes

### Long Connection

```bash
python app/feishu_codex_bot.py --config config/feishu_codex_bot.json
```

### HTTP Callback

```bash
uvicorn app.http_server:app --host 0.0.0.0 --port 8000
```

## Configuration

Copy the example config:

```bash
cp config/feishu_codex_bot.example.json config/feishu_codex_bot.json
```

Then set:

- `app_id`
- `app_secret`
- `codex_path`
- `default_cwd`
- `allowed_chat_ids`

## Security

Configure `allowed_chat_ids` before real usage. Do not use unsafe permission modes in shared or untrusted chats. Do not commit real Feishu/Lark credentials, local paths, logs, state files, screenshots, or temporary files.

`permission_mode` defaults to `default`. Use `bypassPermissions` only for trusted local-only experiments.

## Tests

```bash
pytest -q
```

## Changelog

### v0.1.0-alpha

- Initial public alpha release.
- Codex subprocess bridge.
- Feishu/Lark long-connection mode.
- Optional HTTP callback mode.
- Sanitized example config.
