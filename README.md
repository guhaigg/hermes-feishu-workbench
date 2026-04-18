# Feishu 插件 Hermes 特供版本

面向 **Hermes Agent** 的飞书 / Lark 工作流插件包。

这个仓库不是飞书官方插件，也不是 OpenClaw 官方插件；它是基于 Hermes 当前已经接入的飞书能力、参考飞书官方插件的使用体验后，整理出来的 **Hermes 特供版插件 / skill 包**。

> 当前版本重点是让 Hermes 在飞书任务里说清楚、少乱猜、优先 discovery、减少无意义卡片与内部实现废话。它不负责替代 Hermes 主仓里的飞书 OpenAPI 工具实现。

## 致谢

感谢 [Linux.do](https://linux.do/) 佬友们的一切分享。

## 当前真实状态

当前版本：`0.1.2`

已经包含：

- 一个 Hermes plugin entry point：`feishu-workbench`
- 一个 `pre_llm_call` hook：识别飞书相关任务后注入简洁口径与 discovery-first 约束
- 3 个 plugin skills：
  - `feishu-workbench:feishu-auth-doctor`
  - `feishu-workbench:feishu-chatops`
  - `feishu-workbench:feishu-office`
- 一份能力说明：`feishu_workbench_plugin/references/capabilities.md`
- smoke test：`scripts/smoke_test.py`
- GitHub Actions CI：`.github/workflows/ci.yml`

没有包含：

- 不内置飞书 App ID / App Secret / token
- 不新建飞书开放平台应用
- 不实现完整 OpenClaw 官方飞书插件的所有 API
- 不替代 Hermes 主仓里的 Feishu tools
- 不提供 `hermes feishu-workbench ...` 顶层 CLI 命令
- 不保证“全账号枚举所有资源”；能看到什么取决于 Hermes 当前身份、scope、飞书 API 权限和可见空间

## 它能让 Hermes 在飞书里做什么

前提：你的 Hermes 主体已经接入并启用了对应 Feishu tools。

### 授权 / 诊断类任务

适用场景：

- `/feishu auth`
- `/feishu diagnose`
- `/feishu doctor`
- `/feishu scopes`
- 用户 OAuth / app token / scope 问题排查

目标：

- 缺权限时直接说缺什么 scope
- token 失效时直接提示重授
- 不把“没有结果”说成“账号里不存在”
- 不用一大坨内部实现解释污染聊天

### 消息 / ChatOps

适用场景：

- 读取明确 chat / thread 的历史
- 搜索消息
- 发送 / 回复消息
- reaction / 附件资源相关任务

目标：

- 有明确 chat_id / thread_id 时优先读明确范围
- 不把“能读当前会话”吹成“能全局搜索所有消息”
- 对用户态能力和应用态能力做清晰区分

### 办公流

适用场景：

- docs / wiki / drive
- sheets / bitable
- calendar / tasks

目标：

- discovery first：先枚举可见资源，再读，再写
- 0 结果只表示“当前身份和当前扫描范围没找到”
- 修改 / 删除 / 发消息这类写操作前应明确目标和内容
- 结果里说明范围：应用可见、用户 OAuth 可见、已知链接 / 已知 token 等

## 和飞书官方 OpenClaw 插件的关系

本插件的设计参考了飞书官方 OpenClaw 插件的体验方向，例如：授权 / 诊断要清晰、飞书资源要先 discovery、卡片和回复要少废话、办公能力覆盖消息、文档、表格、日历、任务。

但当前仓库不是官方插件的移植版，也没有复制官方插件的完整实现。

更准确地说：

- 飞书官方插件：提供完整的 OpenClaw 侧飞书能力实现和交互体验
- 本仓库：给 Hermes 提供飞书任务口径、skills、工作流约束和 Hermes 特有的使用层适配
- Hermes 主仓：负责真正的 Feishu tools、gateway、OAuth、卡片回调、API 调用

## 安装方式

### 方式 1：作为 Hermes 插件安装

```bash
hermes plugins install https://github.com/<yourname>/hermes-feishu-workbench.git
hermes gateway restart
```

### 方式 2：手动安装到插件目录

```bash
mkdir -p ~/.hermes/plugins
git clone https://github.com/<yourname>/hermes-feishu-workbench.git ~/.hermes/plugins/feishu-workbench
hermes gateway restart
```

### 方式 3：作为 Python 包安装

```bash
pip install git+https://github.com/<yourname>/hermes-feishu-workbench.git
```

Hermes 会通过 entry point 发现插件：

```toml
[project.entry-points."hermes_agent.plugins"]
feishu-workbench = "feishu_workbench_plugin:register"
```

## 使用方式

### 自动注入

当用户消息明显与飞书 / Lark 相关时，插件会通过 `pre_llm_call` 注入上下文规则。

触发关键词包括但不限于：`feishu`、`lark`、`飞书`、`/feishu`、`bitable`、`sheet`、`wiki`、`docx`、`calendar`、`tasklist`、`message_id`、`chat_id`、`thread_id`、`多维表格`、`电子表格`、`日历`、`任务`、`文档`。

### 手动加载 skill

```text
使用 feishu-workbench:feishu-auth-doctor 检查飞书授权状态
```

```text
使用 feishu-workbench:feishu-office 先列可见日历、任务清单和文档资源，再总结
```

## 推荐的 Hermes 配置

如果你的模型 / 上游接口对大型 tool schema 不稳定，建议给飞书平台使用轻量工具集。

```yaml
platform_toolsets:
  feishu:
    - feishu-lite
    - no_mcp
```

`feishu-lite` 只适合 discovery / 轻量状态检查，通常包含：

- `feishu_list_calendars`
- `feishu_list_tasklists`
- `feishu_list_docs`
- `feishu_list_resources`
- `feishu_search_doc_wiki`

如果你的上游能承受更大的工具 schema，再切回完整飞书工具集：

```yaml
platform_toolsets:
  feishu:
    - feishu
    - memory
    - skills
    - no_mcp
```

## 飞书开放平台权限参考

本插件本身不申请权限；权限由 Hermes 主体的飞书应用和 OAuth 流程负责。

如果你希望覆盖消息、文档、Drive/Wiki、表格、日历、任务等能力，可在飞书开放平台的“权限管理 -> 批量导入/导出权限”中参考以下配置。

注意：权限是否能获批取决于你的租户、应用类型、企业管理策略和飞书平台审核。不要把“已导入权限”理解成“当前 token 已经拥有权限”；补 scope 后通常需要重新发布应用并重新授权用户 OAuth。

```json
{
  "scopes": {
    "tenant": [
      "contact:contact.base:readonly",
      "docx:document:create",
      "docx:document:readonly",
      "docx:document:write_only",
      "docx:document.block:convert",
      "drive:drive.metadata:readonly",
      "im:chat:read",
      "im:chat:update",
      "im:message.group_at_msg:readonly",
      "im:message.p2p_msg:readonly",
      "im:message.pins:read",
      "im:message.pins:write_only",
      "im:message.reactions:read",
      "im:message.reactions:write_only",
      "im:message:readonly",
      "im:message:recall",
      "im:message:send_as_bot",
      "im:message:send_multi_users",
      "im:message:send_sys_msg",
      "im:message:update",
      "im:resource",
      "application:application:self_manage",
      "cardkit:card:write",
      "cardkit:card:read",
      "docs:document.comment:create",
      "docs:document.comment:delete",
      "docs:document.comment:read",
      "docs:document.comment:update",
      "docs:document.comment:write_only"
    ],
    "user": [
      "offline_access",
      "contact:contact.base:readonly",
      "contact:user.base:readonly",
      "contact:user.basic_profile:readonly",
      "contact:user.employee_id:readonly",
      "contact:user:search",
      "im:chat.members:read",
      "im:chat:read",
      "im:message",
      "im:message.group_msg:get_as_user",
      "im:message.p2p_msg:get_as_user",
      "im:message:readonly",
      "search:message",
      "search:docs:read",
      "docs:document:copy",
      "docs:document:export",
      "docs:document.media:download",
      "docs:document.media:upload",
      "docs:document.comment:create",
      "docs:document.comment:read",
      "docs:document.comment:update",
      "docx:document:create",
      "docx:document:readonly",
      "docx:document:write_only",
      "drive:drive.metadata:readonly",
      "drive:file:download",
      "drive:file:upload",
      "space:document:move",
      "space:document:retrieve",
      "wiki:space:read",
      "wiki:space:retrieve",
      "wiki:space:write_only",
      "wiki:node:read",
      "wiki:node:retrieve",
      "wiki:node:create",
      "wiki:node:copy",
      "wiki:node:move",
      "base:app:create",
      "base:app:read",
      "base:app:update",
      "base:app:copy",
      "base:table:create",
      "base:table:read",
      "base:table:update",
      "base:field:create",
      "base:field:read",
      "base:field:update",
      "base:field:delete",
      "base:record:create",
      "base:record:retrieve",
      "base:record:update",
      "base:record:delete",
      "base:view:read",
      "base:view:write_only",
      "sheets:spreadsheet:create",
      "sheets:spreadsheet:read",
      "sheets:spreadsheet:write_only",
      "sheets:spreadsheet.meta:read",
      "calendar:calendar:read",
      "calendar:calendar.event:create",
      "calendar:calendar.event:read",
      "calendar:calendar.event:reply",
      "calendar:calendar.event:update",
      "calendar:calendar.free_busy:read",
      "task:task:read",
      "task:task:write",
      "task:task:writeonly",
      "task:tasklist:read",
      "task:tasklist:write",
      "task:comment:read",
      "task:comment:write"
    ]
  }
}
```

## 已知限制

- 当前插件只是 Hermes 使用层插件；完整工具实现仍在 Hermes 主仓。
- 飞书 User OAuth 可能会因 refresh token、scope、发布状态、回调配置变化而失效。
- “列出所有资源”通常只能说“当前身份可见范围内的资源”，不能说成“全账号所有资源”。
- 飞书 Lite 工具集为了稳定性牺牲了完整操作能力；需要写入 / 修改时请切换到完整 `feishu` 工具集。
- 如果模型上游对工具 schema 很敏感，完整工具集可能导致 502 / upstream failed；建议先用 `feishu-lite` 验证链路。

## 本地验证

```bash
python scripts/smoke_test.py
python -m compileall feishu_workbench_plugin
```

## 目录结构

```text
hermes-feishu-workbench/
├── plugin.yaml
├── __init__.py
├── pyproject.toml
├── LICENSE
├── feishu_workbench_plugin/
│   ├── __init__.py
│   ├── skills/
│   │   ├── feishu-auth-doctor/
│   │   │   └── SKILL.md
│   │   ├── feishu-chatops/
│   │   │   └── SKILL.md
│   │   └── feishu-office/
│   │       └── SKILL.md
│   └── references/
│       └── capabilities.md
├── scripts/
│   └── smoke_test.py
└── .github/workflows/ci.yml
```

## 后续方向

- 将 Hermes 主仓里更成熟的飞书诊断能力继续拆成可复用插件工具。
- 增加可执行的权限矩阵检查脚本。
- 增加根据上游模型能力自动选择 `feishu-lite` / `feishu` 的安装建议。
- 增加更多真实租户回归用例。
