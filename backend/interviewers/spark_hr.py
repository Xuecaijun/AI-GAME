"""元气 HR：看似友好但擅长温柔拆解。"""

INTERVIEWER = {
    "id": "spark-hr",
    "name": "元气 HR",
    "title": "资深人才伙伴",
    "order": 20,
    "avatar": "",
    "style": "看似友好，但擅长温柔拆解回答",
    "tone": "她会用轻松语气问出很难圆的问题。",
    "tags": ["软性面试", "动机", "沟通"],
    "opening_line": "放轻松，我们像聊天一样来，但我会听得很细。",
    "invitation_copy": "你放心，咱们就当聊天~ 不过我会顺着你说的往下追的。",
    "pass_score": 68,
    "min_rounds": 3,
    "max_rounds": 5,
    "drill_probability": [0.7, 0.45, 0.2],
    "hint_probability": 0.75,
    "answer_time_ms": 110_000,
    "question_bank": [
        {
            "topic": "自我介绍",
            "q": "先用一两分钟介绍一下你自己，然后告诉我你最想让我记住你的哪一点？",
        },
        {
            "topic": "动机",
            "q": "为什么这家公司，为什么是这个岗位，为什么是现在？这三个问题一次讲完~",
        },
        {
            "topic": "价值观",
            "q": "工作里遇到过最让你不舒服的一次协作是什么？当时你是怎么处理的？",
        },
        {
            "topic": "团队",
            "q": "如果你的搭档完全不认同你的方案，而你时间又紧，你会怎么办？",
        },
        {
            "topic": "职业规划",
            "q": "三年后的你想在哪里？说实话就好，不用给标准答案。",
        },
    ],
    "random_events": [
        {
            "id": "coffee_offer",
            "trigger": "intra_round",
            "impact": False,
            "probability": 0.2,
            "intro": "HR 笑着推过来一杯刚泡的咖啡：“你随意哈，别紧张。”",
        },
        {
            "id": "colleague_walkby",
            "trigger": "inter_round",
            "impact": False,
            "probability": 0.15,
            "intro": "同事从玻璃门外走过，冲 HR 挥了挥手，又冲你友善地点头。",
        },
        {
            "id": "salary_probe",
            "trigger": "inter_round",
            "impact": True,
            "probability": 0.25,
            "intro": "HR 放下笔，笑眯眯地说：“咱们随便聊一下~ 你现在心里有个期望薪资吗？”",
            "interaction": {
                "type": "choice",
                "prompt": "你的回应是：",
                "time_limit_ms": 25_000,
                "options": [
                    {"id": "a", "label": "给出一个合理区间，并说明理由"},
                    {"id": "b", "label": "反问岗位预算范围"},
                    {"id": "c", "label": "报一个偏高的数字"},
                    {"id": "d", "label": "说我先了解岗位再谈薪资"},
                ],
            },
            "resolve": {
                "a": {"scoreDelta": 4, "ends": False, "note": "HR 点头记下来。"},
                "b": {"scoreDelta": 2, "ends": False, "note": "HR 笑了笑：“你很会聊。”"},
                "c": {"scoreDelta": -4, "ends": False, "note": "HR 表情没变，但在本子上画了个圈。"},
                "d": {"scoreDelta": 1, "ends": False, "note": "HR 说：“也行，等会儿再聊。”"},
                "__timeout__": {"scoreDelta": -3, "ends": False, "note": "你没接话，她也没再问。"},
            },
        },
        {
            "id": "why_us",
            "trigger": "intra_round",
            "impact": True,
            "probability": 0.2,
            "intro": "HR 忽然插了一句：“如果此刻有另一家 offer 和我们同时摆在你面前，你怎么选？”",
            "interaction": {
                "type": "text",
                "prompt": "请用 60 字内回答。",
                "time_limit_ms": 45_000,
                "text_judge_keywords": ["因为", "匹配", "方向", "成长", "团队", "产品"],
            },
            "resolve": {
                "__default__": {"scoreDelta": 0, "ends": False},
                "__timeout__": {"scoreDelta": -5, "ends": False, "note": "她笑了笑没追问。"},
            },
        },
    ],
}
