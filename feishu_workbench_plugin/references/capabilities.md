# Feishu Workbench Capability Notes

本插件不替代 Hermes 的 Feishu 核心实现，它整理的是更适合长期维护和发布的“使用层”能力：

## 1. Auth / Diagnose

- `/feishu auth`
- `/feishu diagnose`
- `/feishu doctor`
- `/feishu scopes`

关注点：

- user OAuth 是否可用
- app scope / user scope 是否缺失
- 下一步动作是否明确

## 2. ChatOps

- 会话历史读取
- thread 历史读取
- 用户态消息发送 / 回复
- reaction
- 资源下载

口径：

- 先明确 chat/thread/message 标识
- 能读不代表能全局搜索
- 搜不到不等于不存在

## 3. Office

- docs / wiki / drive
- sheets / bitable
- calendar / tasks

工作流：

1. 先 discovery
2. 再 read
3. 再 write
4. 对 destructive 操作保持明确确认

## 4. Response Style

优先输出：

1. 结论
2. 限制
3. 下一步

避免：

- 原始授权 URL
- 大段 scope dump
- 内部机制解释
- 对人无意义的 trace 套话
