---
name: feishu-office
description: Use for Feishu/Lark docs, wiki, drive, sheets, bitable, calendar, and task workflows with discovery-first behavior.
---

# Feishu Office

用于 Hermes 的飞书文档、Wiki、Drive、Sheets、Bitable、Calendar、Tasks 办公流。

## 何时使用

- 用户要找飞书文档、Wiki、表格、多维表格
- 用户要读写飞书文档或表格
- 用户要查询 / 创建 / 修改日历
- 用户要查询 / 创建 / 修改任务
- 用户说“看看我有哪些表格 / 日历 / 任务清单”

## 工作流

1. Discovery first：
   - 先枚举可见资源
   - 再读取目标资源
   - 最后才写入 / 修改

2. Read before write：
   - 更新文档前先读取当前内容或目标 block
   - 更新表格前先确认 spreadsheet/base/table/sheet
   - 改日历和任务前先确认具体对象

3. destructive 操作前确认：
   - 删除
   - 批量修改
   - 覆盖表格
   - 发出会议邀请

## 资源口径

- “搜不到”不等于“账号里没有”
- “可见资源为空”要说明当前查询范围和权限边界
- 如果需要用户 OAuth，直接说需要 `/feishu auth`
- 如果缺 scope，直接说缺哪个能力，不要泛泛说“权限问题”

## 输出规则

- 先给结论
- 再说限制
- 最后给下一步
- 不贴长 JSON
- 不贴内部 trace
- 不要把 app token 能力和 user OAuth 能力混成一件事

