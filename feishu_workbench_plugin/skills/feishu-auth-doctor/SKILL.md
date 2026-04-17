---
name: feishu-auth-doctor
description: Use for Feishu/Lark auth health checks, OAuth reauth, diagnose/doctor workflows, and scope troubleshooting in Hermes.
---

# Feishu Auth Doctor

用于 Hermes 的飞书授权、诊断、scope 排障。

## 何时使用

- 用户说飞书没反应、搜不到、发不出去、权限不够
- 需要判断是：
  - 未授权
  - 需重授
  - scope 缺失
  - app 不可见
  - live probe 失败

## 工作流

1. 先看当前状态
   - `/feishu auth`
   - `/feishu diagnose`

2. 需要完整矩阵时再看
   - `/feishu doctor`
   - `/feishu scopes`

3. 输出时按这个顺序
   - 当前状态
   - 缺口
   - 下一步

## 输出规则

- 直接说要不要重授
- 直接说缺哪些 scope
- 不要堆原始 URL
- 不要贴长 scope 列表，除非用户明确要看全量

## 参考

需要更完整能力边界时，读：

- `../../references/capabilities.md`
