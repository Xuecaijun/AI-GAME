"""随机事件引擎。

核心约定：
- 每位面试官在自己的文件里通过 ``random_events`` 声明事件，字段由
  ``INTERVIEWER["random_events"]`` 的结构描述（见任何一位面试官文件）。
- 本模块只负责：按概率掷骰、标记已触发、返回有影响事件的待交互描述、
  按 ``resolve`` 表结算玩家的选择或文本输入。
"""

from __future__ import annotations

import random
from typing import Any


def roll_event(
    interviewer: dict[str, Any],
    trigger: str,
    session: dict[str, Any],
) -> dict[str, Any] | None:
    """在指定触发点掷骰，返回命中的事件（若有）。

    - ``trigger`` 取值：``intra_round`` / ``inter_round``
    - 每个事件一局内最多触发一次，已触发的放在 ``session["firedEvents"]``
    """

    fired: set[str] = session.setdefault("firedEvents", set())
    if isinstance(fired, list):
        fired = set(fired)
        session["firedEvents"] = fired

    candidates = [
        event
        for event in interviewer.get("random_events", [])
        if event.get("trigger") == trigger and event.get("id") not in fired
    ]
    if not candidates:
        return None

    random.shuffle(candidates)
    for event in candidates:
        probability = float(event.get("probability", 0))
        if probability <= 0:
            continue
        if random.random() <= probability:
            fired.add(event["id"])
            return event
    return None


def public_event_payload(event: dict[str, Any]) -> dict[str, Any]:
    """裁剪出前端需要的部分（不暴露结算表 / 关键词）。"""

    payload = {
        "id": event["id"],
        "intro": event.get("intro", ""),
        "impact": bool(event.get("impact", False)),
    }
    interaction = event.get("interaction")
    if interaction and event.get("impact"):
        safe_interaction = {
            "type": interaction.get("type", "choice"),
            "prompt": interaction.get("prompt", ""),
            "timeLimitMs": int(interaction.get("time_limit_ms", 20_000)),
        }
        if safe_interaction["type"] == "choice":
            safe_interaction["options"] = [
                {"id": option["id"], "label": option["label"]}
                for option in interaction.get("options", [])
            ]
        payload["interaction"] = safe_interaction
    return payload


def resolve_event(
    event: dict[str, Any],
    submission: dict[str, Any],
) -> dict[str, Any]:
    """按玩家提交（选择 id 或文本）执行 ``resolve`` 表。

    返回统一结构::

        {
            "scoreDelta": int,
            "ends": bool,                  # 是否直接终结面试
            "note": str,                   # 旁白，注入 transcript
            "playerText": str | None,      # 玩家的文本输入，用于 transcript 回显
        }
    """

    resolve_table = event.get("resolve", {})
    interaction = event.get("interaction") or {}
    interaction_type = interaction.get("type", "choice")

    timed_out = bool(submission.get("timedOut"))
    if timed_out and "__timeout__" in resolve_table:
        hit = resolve_table["__timeout__"]
        return _pack_resolve(hit, player_text=None)

    if interaction_type == "choice":
        choice_id = (submission.get("choiceId") or "").strip()
        if choice_id and choice_id in resolve_table:
            return _pack_resolve(resolve_table[choice_id], player_text=None)
        if "__default__" in resolve_table:
            return _pack_resolve(resolve_table["__default__"], player_text=None)
        return {"scoreDelta": 0, "ends": False, "note": "", "playerText": None}

    text = (submission.get("text") or "").strip()
    if not text and "__timeout__" in resolve_table:
        return _pack_resolve(resolve_table["__timeout__"], player_text=text)

    keywords = interaction.get("text_judge_keywords") or []
    default_entry = resolve_table.get("__default__", {"scoreDelta": 0, "ends": False})

    score_delta = int(default_entry.get("scoreDelta", 0))
    note = default_entry.get("note", "")
    ends = bool(default_entry.get("ends", False))

    hits = sum(1 for keyword in keywords if keyword and keyword in text)
    if hits >= 3:
        score_delta += 5
        note = note or "回答抓住了关键点。"
    elif hits >= 1:
        score_delta += 2
    else:
        score_delta -= 3
        note = note or "回答偏离了关键词。"

    if len(text) < 15:
        score_delta -= 4
        note = note or "回答过于简短，显得不自信。"
    elif len(text) > 40:
        score_delta += 1

    return {
        "scoreDelta": int(score_delta),
        "ends": ends,
        "note": note,
        "playerText": text,
    }


def _pack_resolve(entry: dict[str, Any], player_text: str | None) -> dict[str, Any]:
    return {
        "scoreDelta": int(entry.get("scoreDelta", 0)),
        "ends": bool(entry.get("ends", False)),
        "note": str(entry.get("note", "")),
        "playerText": player_text,
    }


def narration_bubble(event: dict[str, Any], note: str = "") -> str:
    """统一把事件旁白渲染成 transcript 可用的文案。"""

    intro = event.get("intro", "")
    if note:
        return f"{intro}\n—— {note}"
    return intro
