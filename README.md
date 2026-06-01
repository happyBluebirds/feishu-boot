# Feishu Boot

[中文](README.zh-CN.md) | English

Feishu Boot is a local-first Feishu/Lark bot bridge for Codex and coding agents.

Feishu Boot lets developers control local Codex and coding-agent workflows from Feishu/Lark while keeping source code, credentials, logs, screenshots, and execution state on their own machine.

The project is intended for local-first developer automation: Feishu/Lark is the command surface, and your workstation remains the execution environment.

## Why This Exists

Remote chat is convenient for asking an agent to continue work, approve a command, check status, or return a screenshot. Source code and execution state, however, often need to stay local. Feishu Boot bridges that gap by connecting Feishu/Lark bot messages to local Codex and Claude Code runners.

## Included Bridges

| Module | Agent | Runtime style | Best for |
|---|---|---|---|
| `feishu-codex` | Codex CLI | Subprocess execution and optional HTTP callback | Codex automation, command-style tasks, API-compatible chat flows |
| `feishu-claude-v2` | Claude Code | Local foreground window orchestration with Claude hooks | Interactive Claude Code sessions, permission approvals, window and screenshot workflows |
| `feishu_bot_common` | Shared library | Gateway, state, hook, and message utilities | Reusable Feishu/Lark bot infrastructure |

## Core Capabilities

- Run local Codex tasks from Feishu/Lark chat.
- Control local Claude Code windows from Feishu/Lark chat.
- Forward agent permission requests to chat and accept replies from chat.
- Send completion, failure, and status updates back to Feishu/Lark.
- Support Feishu/Lark long connection mode without requiring a public callback URL.
- Provide optional HTTP callback mode for Codex bot deployments.
- Keep real credentials and runtime artifacts outside the public repository.

## Repository Layout

```text
feishu_bot_common/  Shared Feishu/Lark gateway, state, and hook helpers
feishu-codex/       Codex bridge with subprocess and HTTP callback modes
feishu-claude-v2/   Claude Code bridge with hook and foreground-window support
README.md           English overview
README.zh-CN.md     Chinese overview
TROUBLESHOOTING.md  Troubleshooting notes
```

## Quick Start

### Codex Bridge

```powershell
cd feishu-codex
python -m pip install -r requirements.txt
Copy-Item config\feishu_codex_bot.example.json config\feishu_codex_bot.json
```

Edit `config/feishu_codex_bot.json`, then run:

```powershell
python app\feishu_codex_bot.py --config config\feishu_codex_bot.json
```

### Claude Code Bridge

```powershell
cd feishu-claude-v2
python -m pip install -r requirements.txt
Copy-Item config\feishu_claude_bot.v2.example.json config\feishu_claude_bot.v2.json
```

Edit `config/feishu_claude_bot.v2.json`, validate it, then run:

```powershell
.\scripts\start-feishu-claude-bot.ps1 -ValidateOnly
.\scripts\start-feishu-claude-bot.ps1
```

## Security Notes

- Do not commit real Feishu/Lark `app_id`, `app_secret`, chat IDs, local executable paths, or project paths.
- Keep `feishu-codex/config/feishu_codex_bot.json` and `feishu-claude-v2/config/feishu_claude_bot.v2.json` local.
- Keep `.claude/`, logs, state files, screenshots, and temporary files out of Git.
- Configure `allowed_chat_ids` before using the bots in any shared environment.

## Open Source Positioning

Feishu Boot is prepared as an open-source local-agent bridge project for Codex and Claude Code users. It focuses on transparent local execution, readable architecture, sanitized examples, and bilingual documentation for reviewers and contributors.

## Documentation

- [中文说明](README.zh-CN.md)
- [Security policy](SECURITY.md)
- [Codex bridge guide](feishu-codex/README.md)
- [Claude Code bridge guide](feishu-claude-v2/README.md)
- [Troubleshooting](TROUBLESHOOTING.md)
