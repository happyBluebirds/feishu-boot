# Security Policy

[中文](SECURITY.zh-CN.md) | English

Feishu Boot controls local coding agents from Feishu/Lark chat, so security is part of the core design rather than an optional deployment detail.

## Security Model

Feishu Boot is local-first:

- Source code stays on the developer's machine.
- Codex and coding-agent processes run on the developer's machine.
- Credentials, logs, screenshots, approval queues, and execution state are local files.
- Feishu/Lark is used as a command and notification channel, not as the execution environment.

## Sensitive Files

Do not commit real runtime files:

- `feishu-codex/config/feishu_codex_bot.json`
- `feishu-claude-v2/config/feishu_claude_bot.v2.json`
- `.env`
- `.claude/`
- `outputs/`
- `logs/`
- `state/`
- `temp/`

Only sanitized example files should be committed.

## Recommended Deployment Rules

- Configure `allowed_chat_ids` before using the bot in a shared workspace.
- Use the least privileged Feishu/Lark bot permissions required for messaging.
- Keep Feishu/Lark App Secret values outside Git.
- Keep local project paths and executable paths in local config files only.
- Rotate Feishu/Lark credentials if they were ever exposed.
- Review generated commands before approving high-risk operations.
- Avoid running the bridge from a directory that contains unrelated secrets.

## Command Execution Risk

This project can trigger local agent workflows and command execution. Treat every chat command as remote control over your local development environment.

Before production or team usage:

- Restrict chat access.
- Review approval modes.
- Keep audit logs in a private local location.
- Back up important workspaces.
- Prefer dry-run or validation commands for new integrations.

## Reporting Security Issues

If you find a security issue, please avoid opening a public issue with secrets or exploit details. Use a private contact channel for the maintainer, or open a minimal public issue that says a private security report is available.
