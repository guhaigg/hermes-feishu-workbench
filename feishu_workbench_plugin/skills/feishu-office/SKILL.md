---
name: feishu-office
description: Use for Feishu/Lark docs, wiki, drive, sheets, bitable, calendar, and tasks workflows in Hermes; prefer discovery before mutation.
---

# Feishu Office

用于飞书文档、Wiki、表格、多维表格、日历、任务这类办公流。

## 核心规则

- discovery first
- read before write
- destructive 操作前明确确认

## 建议工作流

### 文档 / Wiki / Drive

1. 先搜或枚举资源
2. 再读取目标
3. 最后更新

### Sheets / Bitable

1. 先枚举资源或表
2. 再读范围 / 结构
3. 再写值 / 样式 / 筛选 / 校验

### Calendar / Tasks

1. 先列 calendars / tasklists
2. 再读具体对象
3. 再创建或修改

## 输出口径

- 先说发现了什么
- 再说当前能不能改
- 再说需要用户补什么

## 避免

- 不先枚举就直接假定资源存在
- 把 0 结果说成账号下没有任何资源
- 输出大段调试信息

## 参考

- `../../references/capabilities.md`
