# Feishu Boot

中文 | [English](README.md)

Feishu Boot 是一个 local-first 的飞书/Lark 机器人桥接项目，面向 Codex 和各类本机 coding agent。

核心定位：Feishu Boot 让开发者可以通过飞书/Lark 控制本机 Codex 和 coding-agent 工作流，同时让源码、凭据、日志、截图和执行状态继续保留在自己的机器上。

这个项目适合本地优先的开发自动化：飞书/Lark 负责接收命令和返回结果，本机工作站负责真正执行任务。

## 项目价值

远程聊天适合让编码代理继续任务、审批命令、查询状态或返回截图；但源码和执行状态通常应留在本机。Feishu Boot 用飞书/Lark 机器人把聊天命令桥接到本机 Codex 和 Claude Code 运行器，兼顾远程操作便利性和本地执行可控性。

## 包含模块

| 模块 | 代理 | 运行方式 | 适用场景 |
|---|---|---|---|
| `feishu-codex` | Codex CLI | 子进程执行，可选 HTTP 回调 | Codex 自动化、命令式任务、OpenAI-compatible API 对话 |
| `feishu-claude-v2` | Claude Code | 本机前台窗口编排 + Claude hooks | 交互式 Claude Code 会话、权限审批、窗口和截图工作流 |
| `feishu_bot_common` | 公共库 | 飞书/Lark 网关、状态、hook 和消息工具 | 可复用机器人基础设施 |

## 架构

```text
Feishu/Lark Chat
      |
      v
Feishu Boot Gateway
      |
      +--> feishu-codex      --> Codex CLI         --> local workspace
      |
      +--> feishu-claude-v2  --> Claude Code hooks/window
      |
      v
Local logs / state / screenshots / approval queue
```

## 核心能力

- 在飞书/Lark 聊天中运行本机 Codex 任务。
- 在飞书/Lark 聊天中控制本机 Claude Code 窗口。
- 在聊天中切换常用本机工作目录。
- 启动、停止、暂停和继续本机 agent 工作流。
- 为本机前台 agent 工作流抓取截图。
- 在聊天中查看运行状态和会话状态。
- 为常用操作提供内置帮助命令。
- 将代理权限请求转发到聊天，并从聊天接收审批回复。
- 将完成、失败和状态更新回传到飞书/Lark。
- 支持飞书/Lark 长连接模式，不要求公网回调地址。
- 为 Codex bot 提供可选 HTTP 回调模式。
- 将真实凭据和运行态产物排除在公开仓库之外。

## 目录结构

```text
feishu_bot_common/  公共飞书/Lark 网关、状态和 hook 工具
feishu-codex/       Codex 桥接，支持子进程和 HTTP 回调模式
feishu-claude-v2/   Claude Code 桥接，支持 hook 和前台窗口控制
README.md           英文说明
README.zh-CN.md     中文说明
TROUBLESHOOTING.md  排障说明
```

## 快速开始

### Codex Bridge

```powershell
cd feishu-codex
python -m pip install -r requirements.txt
Copy-Item config\feishu_codex_bot.example.json config\feishu_codex_bot.json
```

修改 `config/feishu_codex_bot.json` 后运行：

```powershell
python app\feishu_codex_bot.py --config config\feishu_codex_bot.json
```

### Claude Code Bridge

```powershell
cd feishu-claude-v2
python -m pip install -r requirements.txt
Copy-Item config\feishu_claude_bot.v2.example.json config\feishu_claude_bot.v2.json
```

修改 `config/feishu_claude_bot.v2.json`，校验后启动：

```powershell
.\scripts\start-feishu-claude-bot.ps1 -ValidateOnly
.\scripts\start-feishu-claude-bot.ps1
```

## 安全说明

- 不要提交真实飞书/Lark `app_id`、`app_secret`、chat ID、本机可执行文件路径或项目路径。
- `feishu-codex/config/feishu_codex_bot.json` 和 `feishu-claude-v2/config/feishu_claude_bot.v2.json` 只保留在本机。
- `.claude/`、日志、状态文件、截图和临时文件不要进入 Git。
- 在共享环境使用前，请先配置 `allowed_chat_ids`。

## 开源定位

Feishu Boot 面向 Codex 和 Claude Code 用户，定位为开源的本机编码代理桥接项目。它强调透明的本地执行、清晰的架构、脱敏示例配置，以及便于评审和贡献者阅读的双语文档。

## 文档入口

- [English README](README.md)
- [安全策略](SECURITY.zh-CN.md)
- [路线图](ROADMAP.md)
- [贡献指南](CONTRIBUTING.md)
- [Codex 桥接说明](feishu-codex/README.md)
- [Claude Code 桥接说明](feishu-claude-v2/README.md)
- [排障说明](TROUBLESHOOTING.md)
