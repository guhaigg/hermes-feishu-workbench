from __future__ import annotations

import json
import os
import re
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
        "doc": {"doc", "docx"},
        "docs": {"doc", "docx"},
        "sheet": {"sheet"},
        "sheets": {"sheet"},
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
    path_map = {"doc": "docx", "docx": "docx", "sheet": "sheet", "bitable": "base", "base": "base", "wiki": "wiki"}
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
            "is_primary": bool(item.get("is_primary") or item.get("default")),
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
    return _request_ok("list_tasklists", endpoint, result, identity="app", inventory_scope="app_visible_tasklists", is_full_account_inventory=False, count=len(items), results=items, note="Lists tasklists visible to the current app identity.")


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


def lite_tools() -> dict[str, dict[str, Any]]:
    return {
        "feishu_lite_list_calendars": {"description": "List calendars visible to the current Feishu app identity.", "handler": list_calendars},
        "feishu_lite_list_tasklists": {"description": "List tasklists visible to the current Feishu app identity.", "handler": list_tasklists},
        "feishu_lite_list_docs": {"description": "List doc/wiki resources visible to the current Feishu app identity.", "handler": list_docs},
        "feishu_lite_list_resources": {"description": "List mixed resources visible to the current Feishu app identity inside reachable wiki spaces.", "handler": list_resources},
        "feishu_lite_search_doc_wiki": {"description": "Search doc/wiki titles visible to the current Feishu app identity.", "handler": search_doc_wiki},
    }
