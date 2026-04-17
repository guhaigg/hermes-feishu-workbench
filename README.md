# Feishu插件 Hermes特供版本

一个面向 **Hermes Agent** 的飞书 / Lark 插件包。

它不重写 Hermes 的飞书底层连接、OAuth、消息网关和工具实现；它负责把飞书相关任务的 **工作流、答复口径、提示注入、技能包** 独立整理出来，让 Hermes 在处理飞书任务时更像一个靠谱的办公助手。

## 致谢 Linux.do

感谢 Linux.do 佬友们的一切分享。

LinuxDo 地址：[https://linux.do/](https://linux.do/)

## 这个插件解决什么

Hermes 飞书能力越来越多以后，容易出现几个问题：

- 输出太长，夹带很多对人无意义的内部解释
- 搜不到就说“没有”，没有区分无权限、不可见、未授权、确实无结果
- 不先枚举资源就直接尝试修改
- 遇到 OAuth / scope 问题时，原因和下一步说不清楚
- 文档、表格、日历、任务、消息这些能力分散，缺少统一使用口径

这个插件做的是使用层增强：

- 给飞书任务自动注入简洁口径
- 让 Hermes 优先走 discovery-first 流程
- 提供三个可显式调用的 Feishu plugin skills
- 把“授权诊断 / 聊天流 / 办公流”的经验沉淀成独立包

## 设计说明

本项目参考了现有 **飞书官方插件 / OpenClaw 飞书插件** 的功能组织方式和使用体验，按 Hermes 当前已有的飞书工具链做了模仿、裁剪和适配。

重点不是复刻官方插件的全部 OpenAPI 实现，而是把对 Hermes 有用的部分整理成：

- 更清晰的飞书任务口径
- 更少废话的卡片 / 回执风格
- discovery-first 的办公流
- 可显式调用的 Hermes plugin skills

如果 Hermes 主体没有实现某个飞书 API，这个插件不会凭空补上底层能力。

## 当前功能

### 1. 飞书任务自动口径注入

插件会注册一个 `pre_llm_call` hook。

当当前任务明显与飞书 / Lark 相关时，会自动给 Hermes 注入这些规则：

- 先结论，再限制，再下一步
- 优先 discovery，再 action
- 0 结果不等于不存在
- 明确区分：
  - 无结果
  - 无权限
  - 应用不可见
  - 未授权
- 缺权限时直接说缺什么 scope 或需要什么授权动作
- 不输出原始授权 URL、长 scope 列表、内部 trace 套话

### 2. 三个 plugin skills

安装后会注册三个 namespaced skills：

```text
feishu-workbench:feishu-auth-doctor
feishu-workbench:feishu-chatops
feishu-workbench:feishu-office
```

#### `feishu-workbench:feishu-auth-doctor`

适合：

- `/feishu auth`
- `/feishu diagnose`
- `/feishu doctor`
- OAuth 掉线
- scope 缺失
- user token 需重授

核心口径：

- 当前状态
- 缺口
- 下一步

#### `feishu-workbench:feishu-chatops`

适合：

- 读取飞书会话历史
- 读取话题 / thread
- 消息搜索
- 用户态发消息 / 回复
- reaction
- 消息资源下载

核心口径：

- 先明确 `chat_id` / `thread_id` / `message_id`
- 优先读明确对象，不默认全局搜
- 搜不到不等于不存在

#### `feishu-workbench:feishu-office`

适合：

- 文档 / Wiki / Drive
- Sheets / Bitable
- Calendar / Tasks

核心口径：

- discovery first
- read before write
- destructive 操作前明确确认

### 3. 当前不会做的事

这个插件不提供：

- 新的飞书 API 凭据管理
- 新的飞书 OAuth 服务
- 新的消息网关
- 新的飞书 OpenAPI Python 工具实现
- `hermes feishu-workbench ...` 顶层 CLI 命令

这些能力仍由 Hermes 主体提供。

这个仓库只保留当前实测可用的两块：

1. `pre_llm_call` 飞书任务口径注入
2. `feishu-workbench:*` plugin skills

## 前置要求

你需要先有一套已经接入飞书的 Hermes。

建议 Hermes 已具备这些能力：

- Feishu gateway / websocket
- `/feishu auth`
- `/feishu diagnose`
- `/feishu doctor`
- Feishu messages / IM user OAuth
- docs / wiki / drive
- sheets / bitable
- calendar / tasks

如果 Hermes 主体没有对应工具，这个插件不会凭空变出飞书 API 能力。

## 安装

### 方式 1：Hermes 插件安装

```bash
hermes plugins install https://github.com/guhaigg/hermes-feishu-workbench.git
```

然后重启 Hermes。

### 方式 2：手动安装到 Hermes 插件目录

把整个项目目录放到：

```text
~/.hermes/plugins/feishu-workbench/
```

然后重启 Hermes：

```bash
hermes gateway restart
```

如果你的 Hermes 是 supervisor / systemd / 自定义脚本常驻，按你的部署方式重启 gateway。

### 方式 3：Python 包安装

```bash
pip install git+https://github.com/guhaigg/hermes-feishu-workbench.git
```

Hermes 会通过 `hermes_agent.plugins` entry point 自动发现插件。

## 使用

### 自动使用

大多数情况下不用手动操作。

只要用户任务明显和飞书相关，比如：

```text
帮我看看飞书有哪些表格
```

```text
飞书这个群最近聊了什么
```

```text
帮我更新一下这个飞书文档
```

插件会通过 hook 自动注入飞书任务口径。

### 显式加载 skill

如果你想让 Hermes 更强制地遵守某个流程，可以显式调用 plugin skill：

```text
使用 feishu-workbench:feishu-auth-doctor 帮我排查飞书授权为什么又掉了
```

```text
使用 feishu-workbench:feishu-chatops 读取这个 thread 的上下文并总结
```

```text
使用 feishu-workbench:feishu-office 先枚举我可见的飞书表格，再决定下一步
```

### 在 cron / 自动任务中使用

适合把 skill 名写进任务描述里，例如：

```text
使用 feishu-workbench:feishu-office，每天检查指定飞书表格并汇总异常。
```

## 验证安装

可以在 Hermes 所在环境里运行一个 Python 检查：

```bash
python - <<'PY'
from hermes_cli.plugins import PluginManager

pm = PluginManager()
pm.discover_and_load()

plugin = pm._plugins.get("feishu-workbench")
print("enabled:", bool(plugin and plugin.enabled))
print("error:", None if not plugin else plugin.error)
print("hooks:", sorted(pm._hooks.keys()))
print("skills:", sorted(pm._plugin_skills.keys()))
PY
```

期望看到：

```text
enabled: True
error: None
hooks: ['pre_llm_call']
skills:
  feishu-workbench:feishu-auth-doctor
  feishu-workbench:feishu-chatops
  feishu-workbench:feishu-office
```

也可以检查单个 skill：

```bash
python - <<'PY'
import json
from tools.skills_tool import skill_view

for name in [
    "feishu-workbench:feishu-auth-doctor",
    "feishu-workbench:feishu-chatops",
    "feishu-workbench:feishu-office",
]:
    data = json.loads(skill_view(name))
    print(name, data.get("success"))
PY
```

## 仓库结构

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

## 本地开发

```bash
python -m compileall .
python scripts/smoke_test.py
```

## 未来方向

### P1：把更多飞书经验沉淀成 skills

- 飞书表格运维 skill
- 飞书文档写作 / 审阅 skill
- 飞书会议纪要 / 日历联动 skill
- 飞书群聊上下文总结 skill

### P2：做更完整的能力矩阵

- app identity 能力
- user OAuth 能力
- scope 映射
- 缺权限时的建议动作

### P3：把部分 Hermes 主仓改动插件化

目前 Hermes 主仓里已有不少飞书能力增强：

- 授权卡片瘦身
- 进度卡片瘦身
- 飞书诊断摘要
- 表格增强
- calendar / task / docs / wiki / drive / sheets 工作流约束

后续可以继续抽象成更独立的插件工具，而不是只做提示层。

### P4：适配更多安装方式

- GitHub release
- pip 包发布
- Hermes plugins registry / skills hub

## License

MIT
