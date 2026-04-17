"""战术分析师：重逻辑、重拆解、重方法论。"""

INTERVIEWER = {
    "id": "tactical-lead",
    "name": "战术分析师",
    "title": "业务线 Tech Lead",
    "order": 30,
    "avatar": "",
    "style": "重逻辑、重拆解、重方法论",
    "tone": "他更看重你的思考结构和复盘能力。",
    "tags": ["结构化", "方法论", "复盘"],
    "opening_line": "我不关心漂亮话，我只看你的判断过程和取舍。",
    "invitation_copy": "欢迎。待会儿麻烦你按：动作、依据、结果的顺序回答。",
    "pass_score": 72,
    "min_rounds": 3,
    "max_rounds": 5,
    "drill_probability": [0.75, 0.6, 0.35],
    "hint_probability": 0.5,
    "answer_time_ms": 100_000,
    "question_bank": [
        {
            "topic": "拆解",
            "q": "请把“把一个普通产品改造成 AI 产品”这件事拆成最多 5 个子问题，按优先级排序。",
        },
        {
            "topic": "指标",
            "q": "你最近一个项目的核心北极星指标是什么？你怎么证明它真的是那个指标？",
        },
        {
            "topic": "复盘",
            "q": "讲一次你主导的复盘，不需要漂亮，讲你真正改掉了什么。",
        },
        {
            "topic": "假设检验",
            "q": "你怎么验证一个功能是否被用户真的需要？给出你做过的一次具体设计。",
        },
        {
            "topic": "决策",
            "q": "讲一次你在数据不充足时做的决策，你用什么替代数据？",
        },
    ],
    "random_events": [
        {
            "id": "whiteboard_request",
            "trigger": "inter_round",
            "impact": True,
            "probability": 0.2,
            "intro": "面试官指向白板：“我们换种方式，请你画出刚才那个方案的决策分支。”",
            "interaction": {
                "type": "choice",
                "prompt": "你的反应：",
                "time_limit_ms": 20_000,
                "options": [
                    {"id": "a", "label": "主动起身，边画边讲"},
                    {"id": "b", "label": "留在座位上用口述描述"},
                    {"id": "c", "label": "请面试官再给一点背景再动手"},
                ],
            },
            "resolve": {
                "a": {"scoreDelta": 5, "ends": False, "note": "他点头：“行，能动起来就好。”"},
                "b": {"scoreDelta": -3, "ends": False, "note": "他皱了皱眉：“光说不画可不够。”"},
                "c": {"scoreDelta": 1, "ends": False, "note": "他点头：“合理。”"},
                "__timeout__": {"scoreDelta": -5, "ends": False},
            },
        },
        {
            "id": "tight_timeline",
            "trigger": "intra_round",
            "impact": True,
            "probability": 0.18,
            "intro": "他忽然说：“假设现在这个方案只有 24 小时上线窗口。”",
            "interaction": {
                "type": "text",
                "prompt": "你会先砍掉什么？保留什么？（80 字内）",
                "time_limit_ms": 60_000,
                "text_judge_keywords": ["砍", "保留", "优先级", "风险", "最小", "MVP"],
            },
            "resolve": {
                "__default__": {"scoreDelta": 0, "ends": False},
                "__timeout__": {"scoreDelta": -6, "ends": False, "note": "他摇头：“这就回答不出来，上线也悬。”"},
            },
        },
        {
            "id": "note_taking",
            "trigger": "inter_round",
            "impact": False,
            "probability": 0.2,
            "intro": "面试官翻页记笔记，头也没抬地说了句：“继续。”",
        },
    ],
}
