---
name: feishu-chatops
description: Use for Feishu/Lark IM workflows: chat history, thread context, message search, user-send, replies, reactions, and message resources.
---

# Feishu ChatOps

用于 Hermes 的飞书消息、会话、话题、用户态发消息和 reaction 流程。

## 何时使用

- 用户要读取飞书群聊 / 单聊 / thread 上下文
- 用户要搜索消息
- 用户要以用户身份发消息或回复消息
- 用户要给消息加 reaction / 表情
- 用户给出 `chat_id`、`message_id`、`thread_id`

## 工作流

1. 先确认对象：
   - `chat_id`
   - `thread_id`
   - `message_id`
   - 用户 open_id / union_id

2. 优先读取明确对象：
   - 有 thread 就读 thread
   - 有 message_id 就读消息上下文
   - 有 chat_id 就读该会话
   - 没有明确对象时再搜索

3. 用户态能力优先确认 OAuth：
   - 消息搜索通常需要用户 OAuth
   - 读取个人可见历史通常需要用户 OAuth
   - 以用户身份发送也需要对应 scope

## 输出规则

- 不要默认说“飞书里没有”
- 0 结果要说清楚可能是：无结果 / 无权限 / 未授权 / 查询范围不对
- 发消息前，如内容会产生实际影响，先给预览并等待确认
- reaction 这类轻量操作可以直接说明目标消息和表情

