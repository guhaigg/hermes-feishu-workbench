---
name: feishu-chatops
description: Use for Feishu/Lark chat workflows in Hermes, including message history, thread reads, user send/reply, reactions, and resource fetches.
---

# Feishu ChatOps

用于 Hermes 的飞书聊天类任务。

## 默认策略

- 先拿明确对象：`chat_id` / `thread_id` / `message_id`
- 优先读明确会话，不要一上来全局搜
- 搜索失败时，不要直接说“没有”

## 建议顺序

1. 读会话 / 读 thread
2. 需要时再搜索
3. 要发消息时，先确认对象和内容
4. 要加 reaction / 下载资源时，确认 message_id

## 回答口径

- 先说拿到了什么
- 再说缺什么
- 最后说下一步

## 避免

- 把“无结果”说成“确定不存在”
- 把 app 能力和 user OAuth 能力混成一锅
- 输出长篇内部机制解释

## 参考

- `../../references/capabilities.md`
