from __future__ import annotations

import random
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
        "summary": "负责高反馈、高表现力的 Web 交互界面与状态流转。",
        "keywords": ["React", "状态管理", "交互设计", "性能优化", "组件", "可视化"],
        "opening_questions": [
            "你做过最复杂的一次前端交互是什么？请讲清目标、实现和结果。",
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
            "AI 产品最容易做成炫技 Demo，你会怎么避免这个问题？",
        ],
    },
]

DIFFICULTIES = {
    "easy": {
        "label": "Easy",
        "description": "简历与岗位高度匹配，问题较基础。",
        "resume_gap": "low",
        "starting_stress": 18,
        "max_turns": 4,
        "score_multiplier": 0.85,
    },
    "normal": {
        "label": "Normal",
        "description": "有少量模糊点，开始出现追问。",
        "resume_gap": "mid",
        "starting_stress": 24,
        "max_turns": 4,
        "score_multiplier": 1.0,
    },
    "hard": {
        "label": "Hard",
        "description": "简历会埋下明显风险点，追问更密集。",
        "resume_gap": "high",
        "starting_stress": 32,
        "max_turns": 5,
        "score_multiplier": 1.1,
    },
    "expert": {
        "label": "Expert",
        "description": "回答一旦不自洽，就会被连续施压。",
        "resume_gap": "very_high",
        "starting_stress": 40,
        "max_turns": 5,
        "score_multiplier": 1.2,
    },
    "master": {
        "label": "Master",
        "description": "人设反差大，高压追问，适合比赛展示。",
        "resume_gap": "extreme",
        "starting_stress": 48,
        "max_turns": 6,
        "score_multiplier": 1.3,
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

CUSTOM_ROLE_PROFILES = [
    {
        "hints": ["技术美术", "ta", "tech art", "美术技术", "shader", "特效美术"],
        "keywords": ["Shader", "渲染表现", "美术管线", "性能优化", "Unity", "工具开发"],
        "summary_template": "围绕视觉表现落地、技术约束平衡与美术流程提效展开，重点考察 {focus}。",
        "opening_questions": [
            "请讲一次你在视觉效果、性能限制和开发周期之间做平衡取舍的经历。",
            "如果项目里美术资源效果很好但性能压力过大，你会如何定位问题并推动优化方案落地？",
        ],
        "resume_lines": [
            "负责角色与场景效果的技术支持，优化 Shader、材质表现和实时渲染效果，保证画面质量与性能平衡。",
            "参与搭建美术制作规范与资源导入流程，协助策划、程序和美术团队提升协作效率。",
            "围绕 Unity 项目中的特效、后处理和资源性能问题进行排查与工具化支持，推动版本稳定迭代。",
        ],
    },
    {
        "hints": ["教师", "老师", "讲师", "班主任", "教研", "培训师", "辅导员"],
        "keywords": ["课程设计", "课堂管理", "学情分析", "表达沟通", "因材施教", "教学复盘"],
        "summary_template": "围绕教学目标达成、课堂组织与学生成长展开，重点考察 {focus}。",
        "opening_questions": [
            "请介绍一次你针对不同学生情况调整教学方式的经历，以及最后的效果。",
            "如果让你接手一个基础参差不齐的班级，你会如何设计教学目标、课堂节奏和复盘方式？",
        ],
        "resume_lines": [
            "负责课程方案设计、课堂组织与课后反馈整理，持续优化教学体验。",
            "基于学生表现和作业数据调整授课节奏，提升班级整体达成度。",
            "与家长或教研团队协作推进教学计划，沉淀可复用的教学资料。",
        ],
    },
    {
        "hints": ["医生", "医师", "护士", "医疗", "药师", "康复", "临床"],
        "keywords": ["病情评估", "诊疗流程", "医患沟通", "风险意识", "病例记录", "协同配合"],
        "summary_template": "围绕诊疗判断、流程执行与患者沟通展开，重点考察 {focus}。",
        "opening_questions": [
            "请讲一次你在时间紧张或信息不完整的情况下完成判断和处置的经历。",
            "如果遇到患者或家属对方案有疑虑，你会如何沟通、记录并推动后续处理？",
        ],
        "resume_lines": [
            "参与患者评估、流程执行与病例记录，关注关键风险点和交接质量。",
            "在规范流程下完成多环节协同，保障诊疗或护理工作稳定推进。",
            "重视与患者及家属的沟通反馈，结合实际情况持续优化处理方式。",
        ],
    },
    {
        "hints": ["律师", "法务", "法律", "合规", "律所"],
        "keywords": ["法律检索", "合同审核", "风险判断", "证据梳理", "沟通谈判", "合规意识"],
        "summary_template": "围绕法律判断、风险控制与沟通推进展开，重点考察 {focus}。",
        "opening_questions": [
            "请分享一次你梳理复杂事实关系并形成法律判断的经历。",
            "如果业务方希望快速推进但存在明显法律风险，你会如何给出可执行建议？",
        ],
        "resume_lines": [
            "参与合同审核、条款梳理与法律风险提示，支持业务稳妥推进。",
            "负责法规检索、证据整理和案例分析，形成清晰的判断依据。",
            "在沟通协同中平衡业务效率与合规要求，推动方案落地。",
        ],
    },
    {
        "hints": ["会计", "财务", "审计", "税务", "出纳", "成本"],
        "keywords": ["账务处理", "报表分析", "成本控制", "预算管理", "风险意识", "细节准确性"],
        "summary_template": "围绕财务准确性、报表分析与风险控制展开，重点考察 {focus}。",
        "opening_questions": [
            "请讲一个你通过对账、分析或复核发现异常并推动解决的问题。",
            "如果你接手一项时间紧、数据多、关联部门复杂的财务工作，你会如何保证准确性和进度？",
        ],
        "resume_lines": [
            "负责账务整理、报表输出与数据复核，关注准确性和时效性。",
            "参与预算跟踪、成本分析和异常排查，为业务提供财务支持。",
            "与业务及外部协作方沟通关键数据口径，推动流程规范化。",
        ],
    },
    {
        "hints": ["销售", "商务", "客户经理", "招商主管", "bd", "business development"],
        "keywords": ["客户沟通", "需求挖掘", "方案呈现", "商机推进", "谈判能力", "结果导向"],
        "summary_template": "围绕客户理解、商机转化与关系推进展开，重点考察 {focus}。",
        "opening_questions": [
            "请分享一次你从客户线索到推动成交的完整过程，重点讲讲关键转折点。",
            "如果客户需求频繁变化、内部资源又有限，你会如何稳住节奏并推进结果？",
        ],
        "resume_lines": [
            "负责客户拜访、需求挖掘和方案沟通，推动商机向成交转化。",
            "根据客户反馈调整推进策略，协调内部资源提升交付确定性。",
            "跟进关键节点数据和复盘结果，持续优化销售节奏与转化效率。",
        ],
    },
    {
        "hints": ["运营", "新媒体", "内容", "社群", "投放", "增长"],
        "keywords": ["内容策划", "用户运营", "数据分析", "活动执行", "转化优化", "节奏把控"],
        "summary_template": "围绕内容、用户与转化结果展开，重点考察 {focus}。",
        "opening_questions": [
            "请讲一个你策划并执行的内容或活动项目，最后是如何衡量效果的。",
            "如果一个渠道数据持续下滑，你会如何拆解问题并安排后续动作？",
        ],
        "resume_lines": [
            "负责内容策划、活动执行与用户反馈整理，关注数据表现和转化效率。",
            "基于渠道数据和用户行为调整节奏，优化留存、互动或转化结果。",
            "与设计、商务或产品协同推进项目落地，并持续复盘迭代。",
        ],
    },
    {
        "hints": ["行政", "人事", "hr", "招聘", "组织发展", "培训"],
        "keywords": ["招聘流程", "组织协调", "沟通推进", "员工体验", "流程管理", "数据复盘"],
        "summary_template": "围绕组织协同、流程执行与人才支持展开，重点考察 {focus}。",
        "opening_questions": [
            "请介绍一次你协调多方资源推进招聘、培训或组织事务的经历。",
            "如果岗位需求变化快、候选人体验又容易受影响，你会如何兼顾效率和质量？",
        ],
        "resume_lines": [
            "参与招聘、入转调离或培训支持等流程，推动组织事务稳定运行。",
            "负责信息整理、进度跟踪与跨部门沟通，保障关键节点按时完成。",
            "关注员工或候选人反馈，结合数据持续优化流程体验。",
        ],
    },
]


def get_role(role_id: str) -> dict:
    return next((item for item in ROLE_LIBRARY if item["id"] == role_id), ROLE_LIBRARY[0])


def get_difficulty(difficulty_id: str) -> dict:
    return DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normal"])


def resolve_role(role_id: str = "", role_title: str = "") -> dict:
    normalized_id = (role_id or "").strip()
    normalized_title = (role_title or "").strip()

    if normalized_title:
        return build_custom_role(normalized_title, role_id=normalized_id or "custom-role")

    if normalized_id == "random":
        return random.choice(get_random_role_candidates())

    matched = next((item for item in ROLE_LIBRARY if item["id"] == normalized_id), None)
    if matched:
        return copy_role(matched)

    return copy_role(ROLE_LIBRARY[0])


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
    keyword_line = "、".join(role["keywords"][:4]) if role.get("keywords") else "项目推进、分析复盘、跨团队协作"
    project_focus = role["keywords"][0] if role.get("keywords") else role["title"]
    resume_lines = role.get("resume_lines") or [
        f"负责“{keyword_text} 智能体验”项目的需求拆解与方案设计，围绕{project_focus}完成从调研到上线复盘的闭环。",
        "参与“多轮对话式面试助手”项目，整理追问逻辑、评分维度与结果报告文案，并推动版本迭代。",
        "和前后端协作完成 Demo 上线，支持在短周期内快速试错和优化体验。",
    ]

    extra_skill = {
        "low": "擅长把复杂需求拆成清晰流程，并持续复盘结果。",
        "mid": "能快速做出 Demo，并与设计、研发和业务团队对齐。",
        "high": "简历里提到了多模块协同、A/B 测试与增长实验，但细节未完全展开。",
        "very_high": "自称主导过高影响力项目优化，并列出了多项高级能力，存在明显可追问空间。",
        "extreme": "履历极其亮眼，覆盖策略、增长、落地与跨部门推进，真实性需要严格验证。",
    }[gap_level]

    risky_line = {
        "low": "项目描述整体自洽，漏洞较少。",
        "mid": f"曾参与一个以“{keyword_text}”为主题的项目，但职责边界略显模糊。",
        "high": f"在“{keyword_text} 智能平台”项目中写了“独立负责核心策略”，但没有展开验证方法。",
        "very_high": f"在“{keyword_text} AI 平台”项目里写了“全面提升留存与转化”，缺少关键指标解释。",
        "extreme": f"在“{keyword_text} 全链路系统”中自称覆盖从 0 到 1 全部工作，容易被质疑是否夸大。",
    }[gap_level]

    return dedent(
        f"""
        姓名：林岚
        应聘岗位：{role['title']}
        教育背景：某综合大学，本科，信息管理与数字媒体相关专业
        核心技能：{keyword_line}、{role['title']}相关实践、跨团队协作、复盘总结
        项目经历：
        1. {resume_lines[0]}
        2. {resume_lines[1]}
        3. {resume_lines[2]}
        补充说明：{extra_skill}
        潜在风险：{risky_line}
        """
    ).strip()


def build_custom_role(role_title: str, role_id: str = "custom-role") -> dict:
    title = role_title.strip()
    profile = match_custom_role_profile(title)
    keywords = infer_keywords_from_role(title, profile)
    opening_questions = build_custom_opening_questions(title, profile)
    return {
        "id": sanitize_role_id(role_id or title),
        "title": title,
        "summary": build_role_summary(title, keywords, profile),
        "keywords": keywords,
        "opening_questions": opening_questions,
        "resume_lines": build_resume_lines(title, profile),
        "is_custom": True,
    }


def infer_keywords_from_role(role_title: str, profile: dict | None = None) -> list[str]:
    if profile:
        return list(profile["keywords"])

    title = role_title.lower()
    keyword_groups = [
        (["技术美术", "tech art", "ta", "shader", "特效"], ["Shader", "渲染表现", "美术管线", "性能优化", "Unity", "工具开发"]),
        (["前端", "frontend", "web", "h5"], ["React", "TypeScript", "交互设计", "性能优化", "组件设计", "可视化"]),
        (["后端", "backend", "服务端", "java", "python"], ["Python", "API 设计", "数据库", "服务治理", "性能优化", "稳定性"]),
        (["算法", "algorithm", "机器学习", "model"], ["机器学习", "特征工程", "模型评估", "Python", "实验设计", "数据分析"]),
        (["数据", "data", "分析", "bi"], ["SQL", "数据分析", "指标体系", "实验设计", "可视化", "业务洞察"]),
        (["产品", "product", "pm"], ["需求分析", "用户研究", "原型设计", "指标设计", "项目推进", "跨团队协作"]),
        (["运营", "operation", "growth"], ["增长", "活动策划", "数据分析", "用户运营", "转化优化", "内容策略"]),
        (["设计", "designer", "ux", "ui"], ["用户体验", "Figma", "交互设计", "视觉表达", "设计系统", "原型"]),
        (["测试", "qa", "quality"], ["测试用例", "自动化测试", "缺陷分析", "质量保障", "回归测试", "风险控制"]),
        (["销售", "business", "商务"], ["客户沟通", "方案呈现", "需求挖掘", "商机推进", "谈判", "结果导向"]),
        (["人力", "hr", "招聘"], ["招聘流程", "人才评估", "沟通协调", "组织规划", "候选人体验", "数据复盘"]),
        (["财务", "finance"], ["财务分析", "预算管理", "成本控制", "报表", "风险意识", "业务协同"]),
        (["游戏", "game"], ["玩法设计", "数值", "叙事", "用户体验", "活动设计", "版本迭代"]),
        (["ai", "人工智能", "大模型", "llm"], ["Prompt", "工作流", "模型评估", "RAG", "自动化", "AI 产品化"]),
    ]

    for hints, keywords in keyword_groups:
        if any(hint in title for hint in hints):
            return keywords

    return ["沟通协作", "项目推进", "问题拆解", "数据分析", "执行落地", "复盘优化"]


def build_role_summary(role_title: str, keywords: list[str], profile: dict | None = None) -> str:
    focus = "、".join(keywords[:3]) if keywords else "问题拆解、执行与协作"
    if profile and profile.get("summary_template"):
        return str(profile["summary_template"]).format(role=role_title, focus=focus)
    return f"围绕 {role_title} 的核心工作展开，重点考察 {focus} 等能力。"


def build_custom_opening_questions(role_title: str, profile: dict | None = None) -> list[str]:
    if profile and profile.get("opening_questions"):
        return list(profile["opening_questions"])
    return [
        f"先介绍一下你自己，并说明为什么适合 {role_title} 这个岗位。",
        f"如果让你从 0 到 1 推进一项与 {role_title} 相关的工作，你会如何拆解目标、执行和验证？",
    ]


def build_resume_lines(role_title: str, profile: dict | None = None) -> list[str]:
    if profile and profile.get("resume_lines"):
        return list(profile["resume_lines"])
    return [
        f"负责与 {role_title} 相关项目的需求拆解、执行推进与阶段复盘，推动工作稳定落地。",
        "参与跨团队协作项目，整理关键流程、结果指标与风险点，支持持续迭代。",
        "根据反馈和数据调整执行节奏，在有限时间内优化结果与体验。",
    ]


def match_custom_role_profile(role_title: str) -> dict | None:
    normalized = role_title.lower()
    for profile in CUSTOM_ROLE_PROFILES:
        if any(hint.lower() in normalized for hint in profile["hints"]):
            return profile
    return None


def sanitize_role_id(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned or "custom-role"


def copy_role(role: dict) -> dict:
    return {
        "id": role["id"],
        "title": role["title"],
        "summary": role["summary"],
        "keywords": list(role.get("keywords", [])),
        "opening_questions": list(role.get("opening_questions", [])),
        **({"resume_lines": list(role["resume_lines"])} if "resume_lines" in role else {}),
        **({"is_custom": role["is_custom"]} if "is_custom" in role else {}),
    }


def get_random_role_candidates() -> list[dict]:
    candidates = [copy_role(role) for role in ROLE_LIBRARY]
    seen_titles = {role["title"] for role in candidates}

    for profile in CUSTOM_ROLE_PROFILES:
        title = str(profile.get("random_title") or profile["hints"][0]).strip()
        if not title or title in seen_titles:
            continue
        candidates.append(build_custom_role(title, role_id=f"random-{sanitize_role_id(title)}"))
        seen_titles.add(title)

    return candidates
