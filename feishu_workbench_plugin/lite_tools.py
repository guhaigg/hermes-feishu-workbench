from __future__ import annotations

import json
import os
from datetime import datetime
from functools import lru_cache
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_DEFAULT_TIMEOUT = 30


def check_available() -> bool:
    return bool(os.getenv('FEISHU_APP_ID') and os.getenv('FEISHU_APP_SECRET'))


def _ok(**data: Any) -> str:
    return json.dumps({"success": True, **data}, ensure_ascii=False)


def _err(message: str, **data: Any) -> str:
    return json.dumps({"success": False, "error": message, **data}, ensure_ascii=False)


def domain_base() -> str:
    domain = (os.getenv("FEISHU_DOMAIN") or "feishu").strip().lower()
    if domain == "lark":
        return "https://open.larksuite.com"
    return "https://open.feishu.cn"


def workspace_base() -> str:
    domain = (os.getenv("FEISHU_DOMAIN") or "feishu").strip().lower()
    if domain == "lark":
        return "https://larksuite.com"
    return "https://feishu.cn"


@lru_cache(maxsize=2)
def tenant_access_token() -> str:
    app_id = os.getenv("FEISHU_APP_ID", "").strip()
    app_secret = os.getenv("FEISHU_APP_SECRET", "").strip()
    if not app_id or not app_secret:
        raise RuntimeError("FEISHU_APP_ID / FEISHU_APP_SECRET not configured")
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8")
    req = Request(
        f"{domain_base()}/open-apis/auth/v3/tenant_access_token/internal",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=_DEFAULT_TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    token = data.get("tenant_access_token")
    if not token:
        raise RuntimeError(f"Failed to obtain tenant_access_token: {data}")
    return token


def request_json(method: str, path: str, *, query: dict[str, Any] | None = None, body: dict[str, Any] | None = None, timeout: int = _DEFAULT_TIMEOUT) -> dict[str, Any]:
    url = f"{domain_base()}{path}"
    if query:
        url += "?" + urlencode({k: v for k, v in query.items() if v is not None}, doseq=True)
    headers = {"Authorization": f"Bearer {tenant_access_token()}", "Content-Type": "application/json"}
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"code": exc.code, "msg": raw or str(exc)}
        parsed.setdefault("http_status", exc.code)
        return parsed
    except (URLError, OSError, json.JSONDecodeError) as exc:
        return {"code": -1, "msg": str(exc)}


def _normalize_timestamp(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = int(raw)
    except ValueError:
        return raw
    if parsed > 10_000_000_000:
        parsed //= 1000
    try:
        return datetime.fromtimestamp(parsed).isoformat()
    except Exception:
        return raw


def _contains_query(title: str, query: str) -> bool:
    return query.casefold() in (title or "").casefold()


def _normalize_obj_types(raw: Any) -> set[str]:
    values: list[str] = []
    if isinstance(raw, list):
        values = [str(item).strip().lower() for item in raw]
    elif isinstance(raw, str):
        values = [part.strip().lower() for part in raw.split(",")]
    aliases = {
        "base": {"base", "bitable"},
        "bases": {"base", "bitable"},
        "bitable": {"base", "bitable"},
        "bitables": {"base", "bitable"},
        "doc": {"doc", "docx"},
        "docs": {"doc", "docx"},
        "document": {"doc", "docx"},
        "documents": {"doc", "docx"},
        "sheet": {"sheet"},
        "sheets": {"sheet"},
        "spreadsheet": {"sheet"},
        "spreadsheets": {"sheet"},
        "wiki": {"wiki"},
        "wikis": {"wiki"},
    }
    normalized: set[str] = set()
    for item in values:
        if item:
            normalized.update(aliases.get(item, {item}))
    return normalized


def _build_node_urls(node: dict[str, Any]) -> tuple[str | None, str | None]:
    base = workspace_base()
    node_token = str(node.get("node_token") or "").strip()
    obj_token = str(node.get("obj_token") or "").strip()
    obj_type = str(node.get("obj_type") or "").strip().lower()
    wiki_url = f"{base}/wiki/{node_token}" if node_token else None
    path_map = {
        "doc": "docx",
        "docx": "docx",
        "sheet": "sheet",
        "slides": "slides",
        "mindnote": "mindnote",
        "bitable": "base",
        "base": "base",
        "wiki": "wiki",
    }
    object_path = path_map.get(obj_type or "", "")
    object_url = f"{base}/{object_path}/{obj_token}" if object_path and obj_token else None
    if obj_type == "wiki" and wiki_url:
        object_url = wiki_url
    return wiki_url, object_url


def _extract_items(data: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    for key in keys:
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _request_ok(action: str, endpoint: str, result: dict[str, Any], **data: Any) -> str:
    if result.get("code") not in (0, None):
        message = result.get("msg") or result.get("message") or "Unknown API error"
        return _err(message, action=action, endpoint=endpoint, result=result, **data)
    return _ok(action=action, endpoint=endpoint, result=result, **data)


# ---------- Discovery: calendars / tasklists ----------

def list_calendars(args: dict[str, Any], **_kw: Any) -> str:
    endpoint = "/open-apis/calendar/v4/calendars"
    result_limit = max(1, min(int(args.get("limit") or args.get("page_size") or 20), 50))
    result = request_json("GET", endpoint, query={"page_size": 50})
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    items = []
    for item in _extract_items(data or {}, "items", "calendar_list", "calendars"):
        items.append({
            "calendar_id": str(item.get("calendar_id") or item.get("id") or "").strip() or None,
            "summary": str(item.get("summary") or item.get("name") or item.get("title") or "").strip() or None,
            "description": str(item.get("description") or "").strip() or None,
            "is_primary": bool(item.get("is_primary") or item.get("default") or str(item.get("type") or '').lower() == 'primary'),
        })
    return _request_ok("list_calendars", endpoint, result, identity="app", inventory_scope="app_visible_calendars", is_full_account_inventory=False, count=min(len(items), result_limit), results=items[:result_limit], note="Lists calendars visible to the current app identity.")


def list_tasklists(args: dict[str, Any], **_kw: Any) -> str:
    endpoint = "/open-apis/task/v2/tasklists"
    result_limit = max(1, min(int(args.get("limit") or args.get("page_size") or 20), 50))
    result = request_json("GET", endpoint, query={"page_size": 50})
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    items = []
    for item in _extract_items(data or {}, "items", "tasklists"):
        items.append({
            "tasklist_guid": str(item.get("tasklist_guid") or item.get("guid") or "").strip() or None,
            "name": str(item.get("name") or item.get("title") or "").strip() or None,
            "is_default": bool(item.get("is_default") or item.get("default")),
        })
    return _request_ok("list_tasklists", endpoint, result, identity="app", inventory_scope="app_visible_tasklists", is_full_account_inventory=False, count=min(len(items), result_limit), results=items[:result_limit], note="Lists tasklists visible to the current app identity.")


# ---------- Discovery: docs / resources / bases / sheets ----------

def _list_spaces() -> tuple[list[dict[str, Any]], str | None]:
    spaces: list[dict[str, Any]] = []
    page_token: str | None = None
    while True:
        query = {"page_size": 50}
        if page_token:
            query["page_token"] = page_token
        result = request_json("GET", "/open-apis/wiki/v2/spaces", query=query)
        if result.get("code") not in (0, None):
            return [], result.get("msg") or result.get("message") or "wiki space listing failed"
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        spaces.extend(_extract_items(data or {}, "items"))
        if not isinstance(data, dict) or not data.get("has_more") or not data.get("page_token"):
            break
        page_token = str(data.get("page_token") or "").strip() or None
        if not page_token:
            break
    return spaces, None


def _search_space_nodes(space: dict[str, Any], *, query: str, result_limit: int, node_budget: int, obj_types: set[str] | None = None, parent_node_token: str | None = None) -> tuple[list[dict[str, Any]], int, str | None]:
    space_id = str(space.get("space_id") or "").strip()
    if not space_id:
        return [], 0, "space_id missing"
    results: list[dict[str, Any]] = []
    scanned_nodes = 0
    queue: list[str] = [str(parent_node_token or "").strip()]
    visited = set(queue)
    while queue and scanned_nodes < node_budget and len(results) < result_limit:
        current_parent = queue.pop(0)
        page_token: str | None = None
        while scanned_nodes < node_budget and len(results) < result_limit:
            params: dict[str, Any] = {"page_size": min(50, max(1, node_budget - scanned_nodes))}
            if current_parent:
                params["parent_node_token"] = current_parent
            if page_token:
                params["page_token"] = page_token
            path = f"/open-apis/wiki/v2/spaces/{space_id}/nodes"
            result = request_json("GET", path, query=params)
            if result.get("code") not in (0, None):
                return results, scanned_nodes, result.get("msg") or result.get("message") or f"wiki node listing failed for space {space_id}"
            data = result.get("data") if isinstance(result.get("data"), dict) else {}
            nodes = _extract_items(data or {}, "items")
            scanned_nodes += len(nodes)
            for node in nodes:
                title = str(node.get("title") or "").strip()
                obj_type = str(node.get("obj_type") or "").strip().lower()
                if (not query or _contains_query(title, query)) and (not obj_types or obj_type in obj_types):
                    wiki_url, object_url = _build_node_urls(node)
                    results.append({
                        "title": title or "(untitled)",
                        "space_id": space_id,
                        "space_name": str(space.get("name") or "").strip() or None,
                        "node_token": node.get("node_token"),
                        "obj_type": obj_type or None,
                        "obj_token": node.get("obj_token") or None,
                        "wiki_url": wiki_url,
                        "object_url": object_url,
                        "edit_time": _normalize_timestamp(node.get("obj_edit_time")),
                    })
                    if len(results) >= result_limit:
                        break
                if node.get("has_child"):
                    child = str(node.get("node_token") or "").strip()
                    if child and child not in visited:
                        visited.add(child)
                        queue.append(child)
            if len(results) >= result_limit:
                break
            if not isinstance(data, dict) or not data.get("has_more") or not data.get("page_token"):
                break
            page_token = str(data.get("page_token") or "").strip() or None
            if not page_token:
                break
    return results, scanned_nodes, None


def _scan_resources(args: dict[str, Any], *, default_obj_types: list[str] | None = None, action: str) -> str:
    query = str(args.get("query") or "").strip()
    requested_space_id = str(args.get("space_id") or "").strip()
    requested_parent = str(args.get("parent_node_token") or "").strip() or None
    result_limit = max(1, min(int(args.get("page_size") or args.get("limit") or 20), 200))
    node_budget = max(result_limit, min(int(args.get("max_nodes") or 300), 1000))
    obj_types = _normalize_obj_types(args.get("obj_types") or default_obj_types or [])
    spaces, error = _list_spaces()
    if error:
        return _err(error, action=action, identity="app")
    if requested_space_id:
        spaces = [space for space in spaces if str(space.get("space_id") or "") == requested_space_id]
    results: list[dict[str, Any]] = []
    scanned_spaces = 0
    scanned_nodes = 0
    warnings: list[str] = []
    for space in spaces:
        if len(results) >= result_limit or scanned_nodes >= node_budget:
            break
        part, count, err = _search_space_nodes(space, query=query, result_limit=result_limit-len(results), node_budget=max(1, node_budget-scanned_nodes), obj_types=obj_types or None, parent_node_token=requested_parent)
        scanned_spaces += 1
        scanned_nodes += count
        results.extend(part)
        if err:
            warnings.append(err)
    response = {
        "action": action,
        "identity": "app",
        "inventory_scope": "app_visible_wiki_resources",
        "is_full_account_inventory": False,
        "query": query or None,
        "requested_space_id": requested_space_id or None,
        "requested_parent_node_token": requested_parent,
        "obj_types": sorted(obj_types) if obj_types else [],
        "results": results[:result_limit],
        "count": min(len(results), result_limit),
        "scanned_spaces": scanned_spaces,
        "scanned_nodes": scanned_nodes,
        "max_nodes": node_budget,
        "note": "Results come from wiki/v2 space/node enumeration via app identity, so they only cover resources visible to the current app inside reachable wiki spaces.",
    }
    if warnings:
        response["warnings"] = warnings
    return _ok(**response)


def list_docs(args: dict[str, Any], **_kw: Any) -> str:
    return _scan_resources(args, default_obj_types=["doc", "docx", "wiki"], action="list_docs")


def list_resources(args: dict[str, Any], **_kw: Any) -> str:
    return _scan_resources(args, default_obj_types=None, action="list_resources")


def search_doc_wiki(args: dict[str, Any], **_kw: Any) -> str:
    query = str(args.get("query") or "").strip()
    if not query:
        return _err("query is required", action="search_doc_wiki")
    return _scan_resources(args, default_obj_types=["doc", "docx", "wiki"], action="search_doc_wiki")


def list_bases(args: dict[str, Any], **_kw: Any) -> str:
    return _scan_resources(args, default_obj_types=["bitable", "base"], action="list_bases")


def list_sheets(args: dict[str, Any], **_kw: Any) -> str:
    return _scan_resources(args, default_obj_types=["sheet"], action="list_sheets")


# ---------- Read messages ----------

def _normalize_message_text(msg_type: str, raw_content: str) -> str:
    content = str(raw_content or "")
    if not content:
        return ""
    try:
        payload = json.loads(content)
    except Exception:
        return content
    if msg_type == "text":
        return str(payload.get("text") or "")
    if msg_type == "post":
        try:
            lines = []
            zh = payload.get("zh_cn") if isinstance(payload.get("zh_cn"), dict) else {}
            title = str(zh.get("title") or "").strip()
            if title:
                lines.append(title)
            for block in zh.get("content") or []:
                row = []
                for item in block or []:
                    if isinstance(item, dict):
                        text = str(item.get("text") or "").strip()
                        if text:
                            row.append(text)
                if row:
                    lines.append(" ".join(row))
            return "\n".join(lines).strip()
        except Exception:
            return content
    for key in ("text", "title", "content"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return content


def _format_message_item(item: dict[str, Any]) -> dict[str, Any]:
    body = item.get("body") if isinstance(item.get("body"), dict) else {}
    sender = item.get("sender") if isinstance(item.get("sender"), dict) else {}
    sender_id = None
    sender_name = None
    sender_id_type = sender.get("id_type")
    sender_type = sender.get("sender_type")
    if isinstance(sender.get("sender_id"), dict):
        sid = sender.get("sender_id")
        sender_id = sid.get("open_id") or sid.get("user_id") or sid.get("union_id")
        sender_name = sid.get("name") or None
    return {
        "message_id": item.get("message_id"),
        "root_id": item.get("root_id") or None,
        "thread_id": item.get("thread_id") or None,
        "reply_to": item.get("parent_id") or None,
        "upper_message_id": item.get("upper_message_id") or None,
        "chat_id": item.get("chat_id") or None,
        "msg_type": item.get("msg_type"),
        "content": _normalize_message_text(item.get("msg_type", ""), body.get("content", "") or ""),
        "create_time": _normalize_timestamp(item.get("create_time")),
        "update_time": _normalize_timestamp(item.get("update_time")),
        "deleted": bool(item.get("deleted", False)),
        "updated": bool(item.get("updated", False)),
        "sender": {
            "id": sender_id,
            "name": sender_name,
            "sender_type": sender_type,
            "id_type": sender_id_type,
        },
    }


def _map_sort_type(value: str) -> str:
    return "ByCreateTimeAsc" if (value or "").strip() == "ByCreateTimeAsc" else "ByCreateTimeDesc"


def _list_messages(*, action: str, container_id_type: str, container_id: str, page_size: int = 20, page_token: str | None = None, sort_type: str = "ByCreateTimeDesc", resolved_thread_id: str | None = None, resolution_source: str | None = None) -> str:
    result = request_json("GET", "/open-apis/im/v1/messages", query={
        "container_id_type": container_id_type,
        "container_id": container_id,
        "sort_type": sort_type,
        "page_size": page_size,
        "page_token": page_token or None,
    })
    if result.get("code") not in (0, None):
        return _err(result.get("msg") or result.get("message") or "message listing failed", action=action, endpoint="/open-apis/im/v1/messages", result=result)
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    raw_items = data.get("items") if isinstance(data, dict) else None
    items = [item for item in (raw_items or []) if isinstance(item, dict)]
    response = {
        "success": True,
        "action": action,
        "identity": "app",
        "container_id_type": container_id_type,
        "container_id": container_id,
        "messages": [_format_message_item(item) for item in items],
        "count": len(items),
        "has_more": bool(data.get("has_more", False)) if isinstance(data, dict) else False,
        "page_token": data.get("page_token") if isinstance(data, dict) else None,
        "sort_type": sort_type,
        "note": "This tool uses the configured Feishu app identity. For group history, the app must have group-message permission and the bot must be in the group.",
    }
    if resolved_thread_id:
        response["resolved_thread_id"] = resolved_thread_id
    if resolution_source:
        response["resolution_source"] = resolution_source
    return json.dumps(response, ensure_ascii=False)


def _resolve_thread_id(thread_id_or_message_id: str) -> tuple[str | None, str | None, str | None]:
    value = (thread_id_or_message_id or "").strip()
    if not value:
        return None, None, "thread_id is required"
    if value.startswith("omt_"):
        return value, "thread_id", None
    if not value.startswith("om_"):
        return None, None, "thread_id must be a thread id (omt_xxx) or a message id (om_xxx)"
    result = request_json("GET", f"/open-apis/im/v1/messages/{value}", query={"user_id_type": "open_id"})
    if result.get("code") not in (0, None):
        return None, None, f"thread resolution failed: {result.get('msg') or result.get('message') or 'Unknown API error'}"
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    message_obj = data.get("message") if isinstance(data.get("message"), dict) else None
    if not message_obj and isinstance(data.get("items"), list) and data.get("items") and isinstance(data.get("items")[0], dict):
        message_obj = data.get("items")[0]
    if not isinstance(message_obj, dict):
        return None, None, "thread resolution failed: message payload missing"
    resolved = str(message_obj.get("thread_id") or "").strip()
    if not resolved:
        return None, None, "the provided message has no thread_id"
    return resolved, "message_id", None


def get_messages(args: dict[str, Any], **_kw: Any) -> str:
    chat_id = str(args.get("chat_id") or "").strip()
    if not chat_id:
        return _err("chat_id is required", action="get_messages")
    page_size = max(1, min(int(args.get("page_size") or args.get("limit") or 20), 50))
    return _list_messages(action="get_messages", container_id_type="chat", container_id=chat_id, page_size=page_size, page_token=str(args.get("page_token") or "").strip() or None, sort_type=_map_sort_type(str(args.get("sort_type") or "")))


def get_thread_messages(args: dict[str, Any], **_kw: Any) -> str:
    resolved_thread_id, resolution_source, error = _resolve_thread_id(str(args.get("thread_id") or ""))
    if error:
        return _err(error, action="get_thread_messages")
    page_size = max(1, min(int(args.get("page_size") or args.get("limit") or 20), 50))
    return _list_messages(action="get_thread_messages", container_id_type="thread", container_id=resolved_thread_id or "", page_size=page_size, page_token=str(args.get("page_token") or "").strip() or None, sort_type=_map_sort_type(str(args.get("sort_type") or "")), resolved_thread_id=resolved_thread_id, resolution_source=resolution_source)


def lite_tools() -> dict[str, dict[str, Any]]:
    return {
        "feishu_lite_list_calendars": {"description": "List calendars visible to the current Feishu app identity.", "handler": list_calendars},
        "feishu_lite_list_tasklists": {"description": "List tasklists visible to the current Feishu app identity.", "handler": list_tasklists},
        "feishu_lite_list_docs": {"description": "List doc/wiki resources visible to the current Feishu app identity.", "handler": list_docs},
        "feishu_lite_list_resources": {"description": "List mixed resources visible to the current Feishu app identity inside reachable wiki spaces.", "handler": list_resources},
        "feishu_lite_search_doc_wiki": {"description": "Search doc/wiki titles visible to the current Feishu app identity.", "handler": search_doc_wiki},
        "feishu_lite_list_bases": {"description": "List Base/Bitable resources visible to the current Feishu app identity.", "handler": list_bases},
        "feishu_lite_list_sheets": {"description": "List Sheet resources visible to the current Feishu app identity.", "handler": list_sheets},
        "feishu_lite_get_messages": {"description": "List messages from a known Feishu chat_id using app identity.", "handler": get_messages},
        "feishu_lite_get_thread_messages": {"description": "List replies from a known Feishu thread_id or source message_id using app identity.", "handler": get_thread_messages},
    }



