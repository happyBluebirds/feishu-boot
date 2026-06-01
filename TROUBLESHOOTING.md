# 常见问题与排障指南

## 飞书机器人通用问题

### 收不到消息
- 检查飞书应用是否已发布
- 检查是否订阅了 `im.message.receive_v1` 事件
- 查看日志文件是否有 `recv` 记录
- 检查 WebSocket 连接是否成功（stderr 中有 `connected to wss://`）

### WebSocket 连接失败 `app_id is invalid`
- 检查配置文件中的 `app_id` 是否正确
- 确认使用 `--config` 参数指定了正确的配置文件
- 默认配置路径是 `feishu_claude_bot.v2.example.json`（占位符），需要用 `--config config/feishu_claude_bot.v2.json`

### 控制台乱码
- Windows 原生命令（taskkill 等）输出 GBK 编码中文
- Git Bash 终端期望 UTF-8
- 解决：`taskkill ... >/dev/null 2>&1`，脚本自己输出 UTF-8 提示
- Python 环境变量：`PYTHONIOENCODING=utf-8`

## feishu-claude-v2 问题

### 前台窗口发送失败 `WINDOW_ACTIVATE_FAILED`
- Windows 前台锁定机制阻止 `SetForegroundWindow`
- 可能原因：窗口被最小化、被其他应用完全遮挡
- 已添加 Alt 键技巧和 ClickCenter 兜底
- 确保 Claude Code 终端窗口至少部分可见

### 截图发了 3 张
- `截图 claude` 截取所有找到的 Claude 终端窗口（hwnds=3）
- 只想截活跃窗口：用 `截图 1`、`截图 2`、`截图 3`
- 或用 `截图 桌面` 截取整个桌面

### 暂停命令中断错窗口
- 已修复：优先使用 `active_window_hwnd`（已选窗口），PID 作兜底
- 用 `切换到窗口 N` 先选择目标窗口，再发 `暂停`

### 权限请求没到飞书
- 检查 `feishu-claude-permission-hook.log`
- 确认 Claude hook 配置指向正确的 hooks 目录

### 任务完成后没有摘要
- 检查 `feishu-claude-turn-hook.log`
- 检查 Claude JSONL 文件是否已写入最新摘要

## feishu-codex 问题

### 沙箱初始化失败 / 没有权限
- 使用 `--dangerously-bypass-approvals-and-sandbox` 绕过沙箱
- 安全靠 `allowed_chat_ids` 白名单控制聊天来源
- 确保 `allowed_chat_ids` 不为空

### 任务卡住不返回
- 检查 `codex exec` 进程是否还在运行
- `codex exec` 默认超时 600 秒（10 分钟）
- 检查 state 文件中的 `status` 和 `last_error`

### `--quiet` 参数错误
- 已修复：使用 `codex exec` 子命令，不再使用 `--quiet`

### subprocess 卡住
- 已修复：添加 `stdin=subprocess.DEVNULL`

## 部署检查清单

- [ ] 飞书应用已创建并启用机器人能力
- [ ] 配置文件中 `app_id` 和 `app_secret` 正确
- [ ] `allowed_chat_ids` 已配置（不为空）
- [ ] 订阅了 `im.message.receive_v1` 事件
- [ ] 申请了 `im:message` 和 `im:message:send_as_bot` 权限
- [ ] 应用已发布
- [ ] WebSocket 连接成功
- [ ] `/health` 接口返回正常（HTTP 模式）
- [ ] 测试命令 `帮助` 能收到回复
- [ ] 测试 `截图 claude` 能收到截图
- [ ] 测试普通文本命令能正常执行
