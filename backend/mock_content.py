from __future__ import annotations

from textwrap import dedent

ROLE_LIBRARY = [
    {
        "id": "ai-game-planner",
        "title": "AI 游戏策划",
        "summary": "为带有大模型交互的游戏设计玩法、反馈循环与数值逻辑。",
        "keywords": ["玩法设计", "数值", "叙事", "用户体验", "迭代", "数据分析"],
        "opening_questions": [
            "先用一分钟介绍你自己，并说说为什么适合 AI 游戏策划这个岗位。",
            "如果让你把一个普通 Web 互动改造成 AI 游戏，你会先改哪一层？",
        ],
    },
    {
        "id": "frontend-engineer",
        "title": "前端交互开发",
        "summary": "负责高反馈、高表现力的 Web 互动界面与状态流转。",
        "keywords": ["React", "状态管理", "交互设计", "性能优化", "组件", "可视化"],
        "opening_questions": [
            "你做过最复杂的一次前端交互是什么？请讲清楚目标、实现和结果。",
            "如果一个 AI 对话页面越来越复杂，你会怎么拆前端状态？",
        ],
    },
    {
        "id": "ai-application-engineer",
        "title": "AI 应用工程师",
        "summary": "负责模型调用、Prompt 编排、结构化输出和业务集成。",
        "keywords": ["Prompt", "RAG", "评估", "API 集成", "工作流", "容错"],
        "opening_questions": [
            "请讲一个你把大模型真正接进产品或工具链的案例。",
            "如果模型输出经常不稳定，你会怎么设计兜底机制？",
        ],
    },
    {
        "id": "product-manager",
        "title": "AI 产品策划",
        "summary": "负责用户问题定义、功能拆解、体验闭环与产品验证。",
        "keywords": ["需求分析", "用户研究", "增长", "原型", "指标", "跨团队协作"],
        "opening_questions": [
            "请介绍一个你主导过的产品方案，以及你如何验证它真的解决了问题。",
            "AI 产品最容易做成炫技 Demo，你怎么避免这个问题？",
        ],
    },
]

INTERVIEWERS = [
    {
        "id": "cold-judge",
        "name": "冷面审判官",
        "style": "强压迫、抓漏洞、语气克制",
        "tone": "他像在做压力测试，不接受泛泛而谈的答案。",
        "opening_line": "欢迎开始。你有四次机会证明，这份履历不是包装。",
    },
    {
        "id": "spark-hr",
        "name": "元气 HR",
        "style": "看似友好，但擅长温柔拆解回答",
        "tone": "她会用轻松语气问出很难圆的问题。",
        "opening_line": "放轻松，我们像聊天一样来，但我会听得很细。",
    },
    {
        "id": "tactical-lead",
        "name": "战术分析师",
        "style": "重逻辑、重拆解、重方法论",
        "tone": "他更看重你的思考结构和复盘能力。",
        "opening_line": "我不关心漂亮话，我只看你的判断过程和取舍。",
    },
    {
        "id": "blackbox-ai",
        "name": "黑盒 AI 观察者",
        "style": "机械、冷幽默、偶尔哲学发问",
        "tone": "它像一个会判定可信度的系统。",
        "opening_line": "候选人已录入。接下来我将验证你的叙述完整性。",
    },
]

DIFFICULTIES = {
    "easy": {
        "label": "Easy",
        "description": "简历与岗位高度匹配，问题较基础。",
        "resume_gap": "low",
        "starting_stress": 18,
        "max_turns": 4,
    },
    "normal": {
        "label": "Normal",
        "description": "有少量模糊点，开始出现追问。",
        "resume_gap": "mid",
        "starting_stress": 24,
        "max_turns": 4,
    },
    "hard": {
        "label": "Hard",
        "description": "简历会埋下明显风险点，追问更密集。",
        "resume_gap": "high",
        "starting_stress": 32,
        "max_turns": 4,
    },
    "expert": {
        "label": "Expert",
        "description": "回答一旦不自洽，就会被连续施压。",
        "resume_gap": "very_high",
        "starting_stress": 40,
        "max_turns": 4,
    },
    "master": {
        "label": "Master",
        "description": "人设反差大，高压追问，适合比赛展示。",
        "resume_gap": "extreme",
        "starting_stress": 48,
        "max_turns": 4,
    },
}

COMMON_SKILLS = [
    "Python",
    "JavaScript",
    "TypeScript",
    "Unity",
    "数据分析",
    "用户研究",
    "Prompt",
    "A/B 测试",
    "运营",
    "SQL",
    "Figma",
    "React",
]


def get_role(role_id: str) -> dict:
    return next((item for item in ROLE_LIBRARY if item["id"] == role_id), ROLE_LIBRARY[0])


def get_interviewer(interviewer_id: str) -> dict:
    return next((item for item in INTERVIEWERS if item["id"] == interviewer_id), INTERVIEWERS[0])


def get_difficulty(difficulty_id: str) -> dict:
    return DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normal"])


def build_theme_blurb(keyword: str, role: dict) -> str:
    if not keyword:
        return f"你面试的岗位是“{role['title']}”，公司正在寻找能把 AI 落到真实体验里的成员。"
    return (
        f"本场比赛关键词是“{keyword}”。你面试的岗位是“{role['title']}”，"
        f"你需要证明自己能把“{keyword}”真正融入产品体验，而不是只写在包装文案里。"
    )


def generate_mock_resume(role: dict, keyword: str, difficulty: dict) -> str:
    keyword_text = keyword or "AI 面试训练"
    gap_level = difficulty["resume_gap"]

    extra_skill = {
        "low": "擅长把复杂需求拆成清晰流程。",
        "mid": "能快速做出 Demo 并和设计、研发对齐。",
        "high": "简历里提到了多模态、A/B 测试与增长实验，但细节未完全展开。",
        "very_high": "自称主导过千万级项目优化，并写了多项高级能力，存在明显可追问空间。",
        "extreme": "履历极其亮眼，覆盖模型调优、增长、叙事与跨端开发，真实性需要严格验证。",
    }[gap_level]

    risky_line = {
        "low": "项目描述整体自洽，漏洞较少。",
        "mid": f"曾参与一个以“{keyword_text}”为主题的互动项目，但职责边界略模糊。",
        "high": f"在“{keyword_text} 智能面板”项目中写了“独立负责核心策略”，但没有展开验证方法。",
        "very_high": f"在“{keyword_text} AI 平台”项目里写了“全面提升留存与转化”，缺少关键指标解释。",
        "extreme": f"在“{keyword_text} 全链路智能系统”中自称覆盖从 0 到 1 全部工作，容易被质疑是否夸大。",
    }[gap_level]

    return dedent(
        f"""
        姓名：林岚
        应聘岗位：{role['title']}
        教育背景：某综合大学，数字媒体技术专业
        核心技能：{", ".join(role["keywords"][:4])}，Python，协作沟通
        项目经历：
        1. 负责“{keyword_text} AI 互动体验”原型设计，完成需求拆解、玩法结构与版本复盘。
        2. 参与“多轮对话式面试助手”项目，整理追问逻辑、评分维度与结果报告文案。
        3. 和前后端协作完成 Demo 上线，支持 3 天内快速改版。
        补充说明：{extra_skill}
        潜在风险：{risky_line}
        """
    ).strip()
