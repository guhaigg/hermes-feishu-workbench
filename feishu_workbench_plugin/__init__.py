"""Hermes Feishu Workbench plugin package."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PLUGIN_ROOT = Path(__file__).parent

_FEISHU_CONTEXT = """[Feishu插件 Hermes特供版本]
当前任务明显与飞书/Lark相关时，遵守这些规则：
- 先结论，再限制，再下一步；不要输出对人无意义的实现解释。
- 优先 discovery，再 action：文档/Wiki/Base/Sheet/Calendar/Task 先枚举，再修改。
- 聊天相关优先读取明确会话或线程；不要默认全局搜索。
- 0 结果不等于不存在；明确区分“无结果”“无权限”“应用不可见”“未授权”。
- 缺权限时直接指出缺什么 scope 或授权动作，不要长篇解释内部机制。
- 回执和状态信息保持紧凑；避免原始 URL、长 scope 列表、内部 trace 套话。
- 如果可用工具里出现 feishu_lite_*，这些是本插件提供的轻量 discovery 代理工具；优先用它们完成日历、任务清单、文档/资源枚举。
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

_LITE_TARGETS = {
    "feishu_lite_list_calendars": "feishu_list_calendars",
    "feishu_lite_list_tasklists": "feishu_list_tasklists",
    "feishu_lite_list_docs": "feishu_list_docs",
    "feishu_lite_list_resources": "feishu_list_resources",
    "feishu_lite_search_doc_wiki": "feishu_search_doc_wiki",
}


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


def _dispatch_existing_tool(tool_name: str, args: dict, **kwargs: Any) -> str:
    """Call a Hermes built-in Feishu tool while exposing a smaller schema."""
    try:
        from tools.registry import registry

        payload = dict(args or {})
        nested_payload = payload.pop("payload", None)
        if isinstance(nested_payload, dict):
            payload.update(nested_payload)
        return registry.dispatch(tool_name, payload, **kwargs)
    except Exception as exc:  # Keep handlers JSON-only, as Hermes tools expect.
        return json.dumps(
            {
                "success": False,
                "error": str(exc),
                "proxied_tool": tool_name,
                "next_step": "确认 Hermes 主仓已安装并启用对应 Feishu tool，或切回主仓完整 Feishu 工具集。",
            },
            ensure_ascii=False,
        )


def _make_lite_handler(target_tool: str):
    def _handler(args: dict, **kwargs: Any) -> str:
        return _dispatch_existing_tool(target_tool, args, **kwargs)

    return _handler


def _lite_schema(name: str, description: str) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Optional search keyword or title filter.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Optional max result count.",
                    "minimum": 1,
                    "maximum": 50,
                },
                "page_size": {
                    "type": "integer",
                    "description": "Optional Feishu page size.",
                    "minimum": 1,
                    "maximum": 50,
                },
                "payload": {
                    "type": "object",
                    "description": "Optional raw passthrough args for the underlying Hermes Feishu tool.",
                    "additionalProperties": True,
                },
            },
            "additionalProperties": True,
        },
    }


def _register_lite_tools(ctx: Any) -> None:
    descriptions = {
        "feishu_lite_list_calendars": "List calendars visible to the current Hermes Feishu identity via the underlying feishu_list_calendars tool.",
        "feishu_lite_list_tasklists": "List tasklists visible to the current Hermes Feishu identity via the underlying feishu_list_tasklists tool.",
        "feishu_lite_list_docs": "List docs/wiki resources visible to Hermes via the underlying feishu_list_docs tool.",
        "feishu_lite_list_resources": "List mixed Feishu resources visible to Hermes via the underlying feishu_list_resources tool.",
        "feishu_lite_search_doc_wiki": "Search Feishu docs/wiki using the underlying feishu_search_doc_wiki tool.",
    }
    for name, target in _LITE_TARGETS.items():
        ctx.register_tool(
            name=name,
            toolset="feishu-workbench-lite",
            schema=_lite_schema(name, descriptions[name]),
            handler=_make_lite_handler(target),
            description=descriptions[name],
            emoji="🪶",
        )


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
    _register_lite_tools(ctx)
    ctx.register_hook("pre_llm_call", _inject_feishu_context)


__all__ = ["register"]
