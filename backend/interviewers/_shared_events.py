"""技术面三位面试官共享的随机事件池。

设计原则：
- 腾讯会议感：网络波动、同事探头、共享屏幕请求、外部电话打断等生活化场景。
- 选项文案保持中性，不绑定面试官人设（人设差异由题库、概率和对话口吻承担）。
- 三位技术面面试官 ``random_events`` 字段统一引用 ``TECH_SHARED_EVENTS``，
  用 ``copy.deepcopy`` 注入以避免 fired 状态跨会话污染。
"""

from __future__ import annotations

import copy
from typing import Any


TECH_SHARED_EVENTS: list[dict[str, Any]] = [
    {
        "id": "network_lag",
        "trigger": "intra_round",
        "impact": False,
        "probability": 0.18,
        "intro": "对方摄像头画面卡了一下，腾讯会议右上角弹出“网络不稳定”。过了两秒又恢复了。",
    },
    {
        "id": "screen_share_request",
        "trigger": "inter_round",
        "impact": True,
        "probability": 0.22,
        "intro": "面试官说：“方便打开共享屏幕吗？我想看你边写边讲。”",
        "interaction": {
            "type": "choice",
            "prompt": "你会怎么回应？",
            "time_limit_ms": 20_000,
            "options": [
                {"id": "a", "label": "马上打开共享，边写边说"},
                {"id": "b", "label": "说一下自己当前没有合适环境，改成口述"},
                {"id": "c", "label": "问能不能先看完整体思路再共享"},
            ],
        },
        "resolve": {
            "a": {"scoreDelta": 4, "ends": False, "note": "面试官点点头：行，咱们就这样。"},
            "b": {"scoreDelta": -2, "ends": False, "note": "面试官嗯了一声没多说。"},
            "c": {"scoreDelta": 1, "ends": False, "note": "面试官说：可以，你先讲。"},
            "__timeout__": {"scoreDelta": -5, "ends": False, "note": "你愣了几秒没回应，面试官先往下推进了。"},
        },
    },
    {
        "id": "colleague_peek",
        "trigger": "inter_round",
        "impact": False,
        "probability": 0.15,
        "intro": "面试官身后有位同事走过，探头看了一眼屏幕，点了点头又走开。",
    },
    {
        "id": "urgent_call",
        "trigger": "intra_round",
        "impact": True,
        "probability": 0.18,
        "intro": "面试官手机响了一下，他瞄了一眼屏幕：“抱歉，紧急电话，我接一下，大概一分钟。”",
        "interaction": {
            "type": "choice",
            "prompt": "趁这段时间你会：",
            "time_limit_ms": 15_000,
            "options": [
                {"id": "a", "label": "安静等待，顺便整理一下刚才回答的思路"},
                {"id": "b", "label": "在聊天框补发一段对前一题的补充"},
                {"id": "c", "label": "直接把摄像头和麦克风关掉休息一下"},
            ],
        },
        "resolve": {
            "a": {"scoreDelta": 3, "ends": False, "note": "面试官回来时你状态看起来更稳了。"},
            "b": {"scoreDelta": 2, "ends": False, "note": "面试官扫了一眼聊天框：“哦，这个补充挺好。”"},
            "c": {"scoreDelta": -3, "ends": False, "note": "面试官回来后又等你几秒才开始。"},
            "__timeout__": {"scoreDelta": 0, "ends": False, "note": "你没动，也还行。"},
        },
    },
    {
        "id": "followup_probe",
        "trigger": "inter_round",
        "impact": True,
        "probability": 0.2,
        "intro": "面试官合上本子：“我临时想再问一下，你对我们这边的技术栈了解多少？”",
        "interaction": {
            "type": "text",
            "prompt": "用 50 字以内回答。",
            "time_limit_ms": 45_000,
            "text_judge_keywords": ["了解", "用过", "关注", "学过", "项目", "文档", "对标"],
        },
        "resolve": {
            "__default__": {"scoreDelta": 0, "ends": False},
            "__timeout__": {"scoreDelta": -4, "ends": False, "note": "他笑了笑：没关系，回头再聊。"},
        },
    },
]


def shared_events() -> list[dict[str, Any]]:
    """返回事件池的深拷贝，避免三位面试官共享引用。"""

    return copy.deepcopy(TECH_SHARED_EVENTS)
