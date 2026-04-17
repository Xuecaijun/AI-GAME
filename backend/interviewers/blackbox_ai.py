"""黑盒 AI 观察者：机械、冷幽默的 AI 面试官。"""

INTERVIEWER = {
    "id": "blackbox-ai",
    "name": "黑盒 AI 观察者",
    "title": "自动面试评估系统 v3.2",
    "order": 40,
    "avatar": "",
    "style": "机械、冷幽默、偶尔哲学发问",
    "tone": "它像一个会判定可信度的系统。",
    "tags": ["AI 面试官", "高难度", "黑色幽默"],
    "opening_line": "候选人已录入。接下来我将验证你的叙述完整性。",
    "invitation_copy": "系统提示：请保持叙述一致性。任何模糊用词都会被记录。",
    "pass_score": 80,
    "min_rounds": 4,
    "max_rounds": 6,
    "drill_probability": [0.9, 0.7, 0.4],
    "hint_probability": 0.35,
    "answer_time_ms": 80_000,
    "question_bank": [
        {
            "topic": "一致性",
            "q": "请复述 30 秒前你提到的那个项目结果。任何出入都会被记录。",
        },
        {
            "topic": "可验证性",
            "q": "输出一个可以被外部验证的指标样本：项目、指标、数字、来源。",
        },
        {
            "topic": "反事实",
            "q": "如果你没有加入那个项目，该项目会发生什么？请量化你的贡献。",
        },
        {
            "topic": "哲学",
            "q": "你如何判断：你在项目里是不可替代的，还是只是最合适的一个选项？",
        },
        {
            "topic": "压力",
            "q": "以下三个陈述里有一个是错的：1. 你主导过 A；2. 你优化过 B；3. 你独立完成过 C。请选出错误项并解释。",
        },
    ],
    "random_events": [
        {
            "id": "system_glitch",
            "trigger": "intra_round",
            "impact": False,
            "probability": 0.2,
            "intro": "系统提示：视频卡顿 1.2 秒。——数据流已恢复。",
        },
        {
            "id": "confidence_check",
            "trigger": "inter_round",
            "impact": True,
            "probability": 0.3,
            "intro": "系统提示：检测到你上一轮回答中存在两处自信度低于阈值的表达。",
            "interaction": {
                "type": "choice",
                "prompt": "请选择处理策略：",
                "time_limit_ms": 25_000,
                "options": [
                    {"id": "a", "label": "承认模糊点，并补充具体证据"},
                    {"id": "b", "label": "否认，重申刚才的结论"},
                    {"id": "c", "label": "质疑系统的判定标准"},
                ],
            },
            "resolve": {
                "a": {"scoreDelta": 6, "ends": False, "note": "系统：叙述可信度上调。"},
                "b": {"scoreDelta": -4, "ends": False, "note": "系统：未检测到新证据。"},
                "c": {"scoreDelta": 2, "ends": False, "note": "系统：哲学反问已归档。"},
                "__timeout__": {"scoreDelta": -6, "ends": False, "note": "系统：沉默也被视为一种数据。"},
            },
        },
        {
            "id": "integrity_probe",
            "trigger": "inter_round",
            "impact": True,
            "probability": 0.22,
            "intro": "系统：请输入一个你愿意被公开验证的工作样本描述。",
            "interaction": {
                "type": "text",
                "prompt": "60 字内描述一段可被验证的工作样本。",
                "time_limit_ms": 50_000,
                "text_judge_keywords": ["指标", "数据", "上线", "复盘", "结果", "来源"],
            },
            "resolve": {
                "__default__": {"scoreDelta": 0, "ends": False},
                "__timeout__": {"scoreDelta": -10, "ends": True, "note": "系统：候选人样本不可验证，本次评估终止。"},
            },
        },
    ],
}
