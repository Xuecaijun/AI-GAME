"""冷面审判官：压迫型技术面试官。"""

INTERVIEWER = {
    "id": "cold-judge",
    "name": "冷面审判官",
    "title": "资深技术总监",
    "order": 10,
    "avatar": "",
    "style": "强压迫、抓漏洞、语气克制",
    "tone": "他像在做压力测试，不接受泛泛而谈。",
    "tags": ["高压", "技术向", "抓细节"],
    "opening_line": "欢迎开始。你有几次机会证明这份履历不是包装。",
    "invitation_copy": "我只看你的判断过程和取舍，别把时间浪费在漂亮话上。",
    "pass_score": 75,
    "min_rounds": 3,
    "max_rounds": 5,
    "drill_probability": [0.85, 0.55, 0.3],
    "hint_probability": 0.45,
    "answer_time_ms": 90_000,
    "question_bank": [
        {
            "topic": "系统设计",
            "q": "如果让你为一个日活千万的小工具设计限流，你会先问哪三个问题？再给出你的方案骨架。",
        },
        {
            "topic": "取舍",
            "q": "你遇到工期和质量冲突时，你**真实**做过的那次取舍是什么？讲清楚代价。",
        },
        {
            "topic": "责任边界",
            "q": "在你最近一个项目里，有没有哪个决定是你拍板、并且事后被证明错了的？",
        },
        {
            "topic": "技术深度",
            "q": "你简历里提到的那项技术，请只讲一次你亲手修过的线上问题。",
        },
        {
            "topic": "抗压",
            "q": "假设我现在告诉你你刚才那段回答有三个漏洞，你会先问我哪一个？",
        },
    ],
    "random_events": [
        {
            "id": "phone_call_ignored",
            "trigger": "intra_round",
            "impact": False,
            "probability": 0.18,
            "intro": "面试官的手机在桌上震了一下。他瞥了一眼，面无表情地按掉。",
        },
        {
            "id": "boss_enters",
            "trigger": "inter_round",
            "impact": True,
            "probability": 0.22,
            "intro": "会议室门被推开，一位看起来是 VP 的人走进来，在面试官耳边说了两句，然后停下来看着你。",
            "interaction": {
                "type": "choice",
                "prompt": "你怎么回应？",
                "time_limit_ms": 20_000,
                "options": [
                    {"id": "a", "label": "主动自我介绍并用一句话总结你的优势"},
                    {"id": "b", "label": "微笑点头，等面试官先开口"},
                    {"id": "c", "label": "继续刚才的思路，不被打断"},
                ],
            },
            "resolve": {
                "a": {"scoreDelta": 5, "ends": False, "note": "VP 点头示意继续，面试官眼神微松。"},
                "b": {"scoreDelta": -2, "ends": False, "note": "VP 只是简单打量了你一下。"},
                "c": {"scoreDelta": -6, "ends": False, "note": "面试官冷笑了一下：你倒是挺稳。"},
                "__timeout__": {"scoreDelta": -8, "ends": False, "note": "你愣住了，空气凝了几秒。"},
            },
        },
        {
            "id": "resume_challenge",
            "trigger": "inter_round",
            "impact": True,
            "probability": 0.2,
            "intro": "面试官合上简历，盯着你说：这页里有一句话，我怀疑你写得比你做得多。",
            "interaction": {
                "type": "text",
                "prompt": "请用 80 字内解释你简历中最有争议的那段职责。",
                "time_limit_ms": 60_000,
                "text_judge_keywords": ["负责", "主导", "结果", "指标", "优化", "拆解"],
            },
            "resolve": {
                "__default__": {"scoreDelta": 0, "ends": False},
                "__timeout__": {"scoreDelta": -10, "ends": True, "note": "沉默太久，他合上了简历。"},
            },
        },
    ],
}
