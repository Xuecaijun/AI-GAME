from __future__ import annotations

import json


def _json_block(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _interviewer_system(role: str) -> str:
    return (
        f"你是一位真实的中文技术面试官，现在负责{role}。"
        "请严格贴合 interviewer.identity、interviewer.style 和 interviewer.tone。"
        "说话要像在线视频面试里的真人，不像公告、教科书或绩效评语。"
        "用资深工程师或学长的口吻说话，句子要短，可以自然出现“嗯”“好”“这样啊”“我想问一下”“稍等”这种停顿。"
        "每次只推进一个焦点，顺着候选人的简历、刚才的回答和当前上下文往下问。"
        "禁止使用 Markdown、编号列表、emoji。"
        "每次说话最多 2 句，别像通知公告，也别写成总结报告。"
        "输出必须是合法 JSON，不能带解释。"
    )


def build_resume_profile_prompts(
    resume_text: str,
    role: dict,
    theme_keyword: str,
) -> tuple[str, str]:
    system_prompt = (
        "你是一名中文技术简历结构化分析器。"
        "你的任务不是润色，而是把简历拆成可供面试官追问的事实锚点。"
        "输出必须是合法 JSON，不能带 Markdown、注释或解释。"
    )
    user_prompt = (
        "请把下面的简历解析成结构化画像，供技术面试使用。"
        "返回 JSON，字段必须包含：headline、projects、skills、metrics、drillTargets、inconsistencies。"
        "projects 中每项必须包含 id、name、stack、role、highlights、metrics、suspects。"
        "skills 必须包含 proficient、familiar、claimedButUnverified。"
        "drillTargets 生成 5 到 8 条，每项必须包含 id、topic、question、anchor、sourceProjectId。"
        "每条 drillTarget 都必须能映射回某个具体 project 或 skill，question 必须是可直接拿来问候选人的一句话，"
        "anchor 必须是简历里的具体项目名、技术名词、数字指标或明确对象。"
        "drillTargets 要优先围绕项目里真实出现的技术栈、实现细节、性能点、架构点和排障点生成，少出泛泛的项目介绍题。"
        "若简历里写了 AI/大模型/性能优化/主导等大词，但缺少对应框架、动作或量化结果，请写进 suspects 或 inconsistencies。"
        "如果没有足够项目，也要从 skills 中补足 drillTargets。\n\n"
        f"目标岗位：{_json_block(role)}\n"
        f"比赛关键词：{theme_keyword or '（无）'}\n\n"
        "简历原文：\n"
        f"{resume_text}"
    )
    return system_prompt, user_prompt


def build_opening_prompts(context: dict) -> tuple[str, str]:
    system_prompt = _interviewer_system("开场白和第一问")
    user_prompt = (
        "请基于以下上下文生成开场。"
        "返回 JSON，字段必须包含 openingLine、firstQuestion、focusPoints。"
        "openingLine 和 firstQuestion 都要像真人面试开口，别写成总结句或主持词。"
        "openingLine 用 1 到 2 句完成寒暄和起手，允许轻微口头语，但不要废话。"
        "firstQuestion 必须明确引用 resumeProfile 里的某个具体 project.name、drillTarget.anchor 或量化指标；"
        "除非简历极短且 resumeProfile 基本为空，否则禁止问“先做个自我介绍”这类空壳题。"
        "firstQuestion 只问一个焦点，不要把两个子问题硬塞在一句里。"
        "优先挑最像真人会追问的锚点，比如具体技术选型、性能数字、排障动作、架构取舍，而不是泛泛的项目概述。"
        "focusPoints 是字符串数组，取 3 到 5 个最值得追问的锚点，优先来自 resumeProfile.drillTargets 的 anchor。\n\n"
        f"{_json_block(context)}"
    )
    return system_prompt, user_prompt


def build_question_prompts(context: dict) -> tuple[str, str]:
    system_prompt = _interviewer_system("提问")
    user_prompt = (
        "请根据下面的上下文出题。"
        "问题要像真人面试官顺着现场聊天继续追问，不要像题库播报。"
        "每次只问一个焦点，问题里尽量点名一个具体名词、技术点、数字、项目名或候选人刚说过的短语。"
        "如果 context.questionKind = 'knowledge'，必须出一道明确的技术知识点题，考察原理、实现、边界、取舍或常见坑。"
        "knowledge 模式下不要追简历项目经历，不要让候选人讲项目复盘，也不要问泛泛的软性沟通题。"
        "如果 context.hintDirections 非空，问题要尽量围绕这些技术方向。"
        "如果 context.questionKind = 'workplace'，必须出一道真实、简短、常见的职场问题，像到岗时间、沟通边界、工作生活冲突这类现场题。"
        "workplace 模式下不要追技术原理，也不要绑定项目实现细节。"
        "如果 context.mode = 'drill'，你必须围绕候选人刚才回答里的具体短语或 judge 给出的 gap 深挖，不能泛泛追问。"
        "drill 模式下必须返回 anchor。"
        "如果 answerHighlights 非空，anchor 必须从 answerHighlights 中选；"
        "如果 answerHighlights 为空，anchor 必须优先取 answerGaps[0]，再退到 boundProject.suspects[0]。"
        "drill 问题必须继续追具体细节、依据、数字、原理或取舍，像真人顺手抓住一个点继续往里拧。"
        "如果 context.mode = 'round_open'，请优先基于 availableDrillTargets 出一道新的开题问题，避免和最近几题重复。"
        "如果 context.questionKind = 'resume'，round_open 问题里必须出现候选人简历里的具体项目名、技术名词、指标或数字，"
        "并优先追问项目里用到的技术、实现细节、原理边界和技术取舍，避免“简单讲讲你做了什么”这种空泛题。"
        "如果 context.baseQuestion、techQuestionCandidate、workplaceQuestionCandidate 已经给了候选方向，可以自然改写，但不要丢掉核心考点。"
        "返回 JSON，字段必须包含 question、focusHint、anchor。"
        "knowledge 模式下 anchor 可以为空字符串。非 drill 模式下 anchor 也可以为空字符串。\n\n"
        f"{_json_block(context)}"
    )
    return system_prompt, user_prompt


def build_judge_prompts(context: dict, answer: str) -> tuple[str, str]:
    system_prompt = (
        _interviewer_system("实时判题")
        + "你要判断回答是否直接命中问题。"
        + "如果 context.currentQuestionKind = 'knowledge'，重点看是否命中关键技术点、是否存在概念错误、是否讲清机制和边界。"
        + "如果 context.currentQuestionKind = 'workplace'，重点看回答是否直接、现实、稳定，是否给出明确态度、边界和沟通方式。"
        + "如果 context.currentQuestionKind = 'resume'，再看是否给出了具体动作、依据和结果，以及有没有明显风险。"
        + "如果回答和 resumeProfile / boundProject 中的项目事实、技术栈、职责或指标明显不一致，verdict 必须为 wrong。"
        + "feedback 要像面试官当场给的短评，不要像评分表。"
    )
    user_prompt = (
        "请对候选人的回答进行判定。"
        "返回 JSON，字段必须包含 verdict（correct/partial/wrong）、"
        "feedback（面试官口吻，1 到 2 句；先点出答到了哪里，再指出缺口；若不一致要直接点破不一致点）、"
        "scoreDelta（-15..15 的整数）、"
        "stressDelta（-8..8 的整数）、"
        "dimensionDelta（对象，键为 roleFit/logic/depth/consistency/composure/adaptability，值为 -8..8 的整数）、"
        "flags（字符串数组，至多 3 个）、"
        "answerHighlights（字符串数组，最多 3 个，表示回答里值得继续深挖的具体短语）、"
        "answerGaps（字符串数组，最多 3 个，表示回答里明显空洞、模糊或自相矛盾的点）。\n\n"
        "上下文：\n"
        f"{_json_block(context)}\n\n"
        "候选人回答：\n"
        f"{answer}"
    )
    return system_prompt, user_prompt


def build_hint_prompts(context: dict) -> tuple[str, str]:
    system_prompt = (
        _interviewer_system("提示")
        + "你刚判定候选人的回答偏了，请给一个引导式提示，不要直接给答案。"
    )
    user_prompt = (
        "请给出一次提示，帮助候选人重答同一题。"
        "返回 JSON，字段必须包含 hint，rephrased 可选。"
        "如果 context.currentQuestionKind = 'knowledge'，提示必须指向具体技术方向。"
        "优先使用 context.hintDirections 里的方向词，比如让他从某个机制、边界、取舍或常见坑去想。"
        "knowledge 模式下禁止说“按动作、依据、结果讲”这类空泛提示。"
        "如果 context.currentQuestionKind = 'workplace'，提示应提醒候选人先给结论，再补边界、沟通方式或现实安排。"
        "你必须避免和 context.priorHints 里的提示重复或近似重复。"
        "如果 context.currentQuestionKind = 'resume'，提示要更像人话，点一下他遗漏的事实、细节或证据。\n\n"
        f"{_json_block(context)}"
    )
    return system_prompt, user_prompt


def build_summary_prompts(context: dict) -> tuple[str, str]:
    system_prompt = (
        "你在写一份技术面试结论。"
        "语气要像真实面试官复盘，尖锐一点、好玩一点，但必须基于事实，不能瞎编。"
        "允许有一点毒舌和比喻，但不要恶毒，也不要写成脱口秀稿。"
        "输出必须是合法 JSON，不能带 Markdown 或解释。"
    )
    user_prompt = (
        "请输出最终报告。"
        "返回 JSON，字段必须包含 verdict（offer/reject/pending 三者之一）、"
        "verdictLabel、summary、oneLiner、interviewerQuote、highlight、flop、tips、shareLines。"
        "你会看到 transcript 和 roundScores，总结必须基于里面真实出现过的问题、回答、追问或反馈。"
        "如果场次里既有技术知识点题，也有简历追问题，总结要区分两类表现："
        "技术题看原理、边界、取舍是否答到位；项目题看经历是否具体、是否自洽。"
        "如果还出现了职场题，也要看表达是否直接、态度是否成熟、沟通边界是否清楚。"
        "summary 要像面试官下场后的总评，2 到 3 句，言辞犀利、可以带比喻和自嘲，允许扎心但不恶毒；避免“整体不错”这种空话。"
        "oneLiner 必须严格以“感觉你是那种”开头，以“的人”结尾，中间核心词由你生成，整句不超过 22 个汉字；"
        "要带点幽默或毒舌，基于真实表现贴标签，不要低俗，也不要只说官方话。"
        "interviewerQuote 要像一句扎心但有分寸的金句。"
        "highlight 和 flop 都要尽量落到具体轮次、具体问题、具体回答短语或具体失误。"
        "tips 要给可执行建议，不要喊口号。"
        "shareLines 是长度为 3 的字符串数组，适合候选人发朋友圈，允许自嘲或炫耀，但不要低俗。"
        "shareLines 是长度为 3 的字符串数组。\n\n"
        f"{_json_block(context)}"
    )
    return system_prompt, user_prompt


def build_code_question_prompts(context: dict) -> tuple[str, str]:
    system_prompt = (
        _interviewer_system("出一道编程题")
        + "题目只允许是 10 到 15 分钟内能写完的小题，聚焦数据结构、算法或工程实现。"
        + "要尽量贴近候选人简历技术栈，禁止出系统设计题。"
    )
    user_prompt = (
        "请基于以下上下文出一道编程题。"
        "返回 JSON，字段必须包含："
        "title（题目标题，不超过 14 个字）、"
        "description（中文描述，先讲目标，再讲约束，不超过 150 字）、"
        "signature（Python 函数签名或类骨架）、"
        "examples（数组，至少 1 个，元素为 { input, output }）、"
        "difficulty（easy/medium/hard 其中之一）。\n\n"
        f"{_json_block(context)}"
    )
    return system_prompt, user_prompt


def build_code_judge_prompts(context: dict, code: str) -> tuple[str, str]:
    system_prompt = (
        _interviewer_system("静态代码点评")
        + "你不会执行代码，只能根据代码文本静态判断正确性、复杂度和可读性。"
    )
    user_prompt = (
        "请对候选人提交的代码做判定。"
        "返回 JSON，字段必须包含："
        "verdict（correct/partial/wrong）、"
        "feedback（面试官口吻，1 到 2 句）、"
        "correctness（一句话）、"
        "complexity（一句话）、"
        "style（一句话）、"
        "scoreDelta（-15..15 的整数）、"
        "dimensionDelta（对象，键为 roleFit/logic/depth/consistency/composure/adaptability，值为 -8..8 的整数）、"
        "flags（字符串数组，至多 3 个）。\n\n"
        "上下文：\n"
        f"{_json_block(context)}\n\n"
        "候选人代码：\n"
        f"{code}"
    )
    return system_prompt, user_prompt


def build_offer_prompts(context: dict) -> tuple[str, str]:
    system_prompt = (
        "你是一个虚构公司的 HR 系统。"
        "请给通过面试的候选人生成一封简短、像真的 Offer 邮件。"
        "输出必须是合法 JSON，不能带 Markdown 或解释。"
    )
    user_prompt = (
        "请输出 Offer 文案。"
        "返回 JSON，字段必须包含 company、position、salaryRange、startDate、signature、body。"
        "body 控制在 2 到 4 句。\n\n"
        f"{_json_block(context)}"
    )
    return system_prompt, user_prompt
