"""Hermes Feishu Workbench plugin package."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_PLUGIN_ROOT = Path(__file__).parent

_FEISHU_CONTEXT = """[Feishu插件 Hermes特供版本]
当当前任务明显与飞书/Lark相关时，遵守这些规则：
- 先结论，再限制，再下一步；不要输出对人无意义的实现解释。
- 优先 discovery，再 action：文档/Wiki/Base/Sheet/Calendar/Task 先枚举，再修改。
- 聊天相关优先读取明确会话或线程；不要默认全局搜索。
- 0 结果不等于不存在；明确区分“无结果”“无权限”“应用不可见”“未授权”。
- 缺权限时直接指出缺什么 scope 或授权动作，不要长篇解释内部机制。
- 回执和状态信息保持紧凑；避免原始 URL、长 scope 列表、内部 trace 套话。
"""

_KEYWORDS = (
    "feishu",
    "lark",
    "飞书",
    "/feishu",
    "bitable",
    "base",
    "sheet",
    "sheets",
    "wiki",
    "docx",
    "calendar",
    "tasklist",
    "task",
    "message_id",
    "chat_id",
    "thread_id",
    "多维表格",
    "电子表格",
    "日历",
    "任务",
    "文档",
)


def _looks_like_feishu_turn(*, user_message: str, platform: str) -> bool:
    if str(platform or "").strip().lower() == "feishu":
        return True
    lowered = str(user_message or "").lower()
    return any(keyword in lowered for keyword in _KEYWORDS)


def _inject_feishu_context(
    session_id: str | None = None,
    user_message: str | None = None,
    conversation_history: list | None = None,
    is_first_turn: bool | None = None,
    model: str | None = None,
    platform: str | None = None,
    **kwargs: Any,
) -> dict[str, str] | None:
    del session_id, conversation_history, is_first_turn, model, kwargs
    if not _looks_like_feishu_turn(user_message=str(user_message or ""), platform=str(platform or "")):
        return None
    return {"context": _FEISHU_CONTEXT}


def _register_skills(ctx: Any) -> None:
    skills_root = _PLUGIN_ROOT / "skills"
    entries = {
        "feishu-auth-doctor": "Feishu auth, doctor, diagnose, and scope troubleshooting.",
        "feishu-chatops": "Feishu IM/message workflows with concise response rules.",
        "feishu-office": "Discovery-first docs/wiki/sheets/calendar/tasks workflows.",
    }
    for name, description in entries.items():
        ctx.register_skill(name, skills_root / name / "SKILL.md", description)


def register(ctx: Any) -> None:
    _register_skills(ctx)
    ctx.register_hook("pre_llm_call", _inject_feishu_context)


__all__ = ["register"]
