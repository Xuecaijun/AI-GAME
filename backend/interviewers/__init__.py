"""面试官注册表。

将同目录下每个 Python 模块中的 ``INTERVIEWER`` 字典自动收集进
``INTERVIEWER_REGISTRY``。新增面试官 = 新建一个 ``xxx.py`` 文件并导出
``INTERVIEWER = {...}``，无需改动其它代码。
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

INTERVIEWER_REGISTRY: list[dict[str, Any]] = []
_REGISTRY_BY_ID: dict[str, dict[str, Any]] = {}


def _load() -> None:
    INTERVIEWER_REGISTRY.clear()
    _REGISTRY_BY_ID.clear()

    for module_info in pkgutil.iter_modules(__path__):
        if module_info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{module_info.name}")
        data = getattr(module, "INTERVIEWER", None)
        if not isinstance(data, dict):
            continue
        if "id" not in data or "name" not in data:
            continue
        INTERVIEWER_REGISTRY.append(data)
        _REGISTRY_BY_ID[data["id"]] = data

    INTERVIEWER_REGISTRY.sort(key=lambda item: item.get("order", 100))


def all_interviewers() -> list[dict[str, Any]]:
    if not INTERVIEWER_REGISTRY:
        _load()
    return INTERVIEWER_REGISTRY


def get_interviewer(interviewer_id: str) -> dict[str, Any]:
    if not INTERVIEWER_REGISTRY:
        _load()
    if interviewer_id in _REGISTRY_BY_ID:
        return _REGISTRY_BY_ID[interviewer_id]
    return INTERVIEWER_REGISTRY[0]


def public_card(interviewer: dict[str, Any]) -> dict[str, Any]:
    """用于前端展示的精简字段（避免把题库、事件概率直接暴露）。"""

    return {
        "id": interviewer["id"],
        "name": interviewer["name"],
        "avatar": interviewer.get("avatar", ""),
        "title": interviewer.get("title", ""),
        "style": interviewer.get("style", ""),
        "tone": interviewer.get("tone", ""),
        "opening_line": interviewer.get("opening_line", ""),
        "pass_score": interviewer.get("pass_score", 70),
        "tags": interviewer.get("tags", []),
        "invitation_copy": interviewer.get("invitation_copy", ""),
    }


_load()
