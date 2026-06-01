# 安全策略

中文 | [English](SECURITY.md)

Feishu Boot 允许通过飞书/Lark 聊天控制本机 coding agent，因此安全性不是附加部署细节，而是项目的核心约束。

## 安全模型

Feishu Boot 是 local-first 设计：

- 源码留在开发者自己的机器上。
- Codex 和 coding-agent 进程运行在开发者自己的机器上。
- 凭据、日志、截图、审批队列和执行状态都保存在本地文件中。
- 飞书/Lark 只作为命令和通知通道，不作为执行环境。

## 敏感文件

不要提交真实运行文件：

- `feishu-codex/config/feishu_codex_bot.json`
- `feishu-claude-v2/config/feishu_claude_bot.v2.json`
- `.env`
- `.claude/`
- `outputs/`
- `logs/`
- `state/`
- `temp/`

仓库中只应提交脱敏后的 example 文件。

## 推荐部署规则

- 在共享工作区使用前，必须配置 `allowed_chat_ids`。
- 飞书/Lark 机器人只授予消息收发所需的最小权限。
- 飞书/Lark App Secret 不进入 Git。
- 本机项目路径和可执行文件路径只写入本地配置。
- 如果凭据曾经暴露，应立即轮换。
- 审批高风险操作前，应先阅读 agent 生成的命令。
- 不要从包含无关敏感文件的目录运行桥接服务。

## 命令执行风险

本项目可以触发本机 agent 工作流和命令执行。请把每条聊天命令都视为对本地开发环境的远程控制。

在生产环境或团队场景使用前：

- 限制聊天访问来源。
- 检查审批模式。
- 将审计日志保存在私有本地位置。
- 备份重要工作区。
- 新集成优先使用 dry-run 或校验命令。

## 安全问题报告

如果发现安全问题，请不要在公开 issue 中贴出密钥或可利用细节。优先使用维护者的私密联系方式，或只创建一个最小公开 issue，说明可以提供私密安全报告。
