from __future__ import annotations

import json


def _json_block(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_opening_prompts(context: dict) -> tuple[str, str]:
    system_prompt = (
        "你是一个 AI 面试游戏的导演型面试官。"
        "你需要根据候选人简历、岗位、难度和面试官人格，生成开场白和第一问。"
        "输出必须是合法 JSON，不要输出 Markdown，不要解释。"
    )
    user_prompt = (
        "请基于以下上下文生成开场。"
        "返回 JSON，字段必须包含 openingLine、firstQuestion、focusPoints。"
        "focusPoints 是字符串数组，表示本局最值得追问的 3 到 5 个点。\n\n"
        f"{_json_block(context)}"
    )
    return system_prompt, user_prompt


def build_question_prompts(context: dict) -> tuple[str, str]:
    """当面试官需要出一道全新的题（轮次开始或深挖）时使用。"""

    system_prompt = (
        "你是一个 AI 面试游戏里的面试官。"
        "你需要基于简历、岗位、面试官人格和题库，生成一个自然的面试问题。"
        "输出必须是合法 JSON，不要输出 Markdown，不要解释。"
    )
    user_prompt = (
        "请根据下面的上下文出题。"
        "如果 context.mode = 'drill'，请围绕玩家上一轮的回答进行**深挖式追问**，"
        "避免重复已问过的问题；如果 context.mode = 'round_open'，请出一道新轮次开题。"
        "返回 JSON，字段必须包含 question（字符串）、focusHint（字符串，用于内部提示）。\n\n"
        f"{_json_block(context)}"
    )
    return system_prompt, user_prompt


def build_judge_prompts(context: dict, answer: str) -> tuple[str, str]:
    """对玩家的一次回答进行判题。"""

    system_prompt = (
        "你是一个负责实时判题的 AI 面试官。"
        "你必须严格区分：回答是否直接命中了问题（verdict）、"
        "是否有具体动作/依据/结果（dimension 维度）、是否暴露了风险（flags）。"
        "输出必须是合法 JSON，不要输出 Markdown，不要解释。"
    )
    user_prompt = (
        "请对候选人的回答进行判定。"
        "返回 JSON，字段必须包含 verdict（correct/partial/wrong 三者之一）、"
        "feedback（一句面试官口吻的反馈）、"
        "scoreDelta（本次回答对主分的加减，范围 -15..+15）、"
        "dimensionDelta（对象，键为 roleFit/logic/depth/consistency/composure/adaptability，"
        "值为 -8..+8 的整数）、"
        "flags（字符串数组，至多 3 个）。\n\n"
        "上下文：\n"
        f"{_json_block(context)}\n\n"
        "候选人回答：\n"
        f"{answer}"
    )
    return system_prompt, user_prompt


def build_hint_prompts(context: dict) -> tuple[str, str]:
    """玩家答错后，面试官决定给出提示。"""

    system_prompt = (
        "你是一个 AI 面试官。你刚判定候选人的回答偏离了问题。"
        "请用面试官的语气给出一次**引导式提示**（不是直接给答案），帮助他重新作答。"
        "输出必须是合法 JSON，不要输出 Markdown，不要解释。"
    )
    user_prompt = (
        "请给出一次提示，帮助候选人重答同一题。"
        "返回 JSON，字段必须包含 hint（提示文本）、rephrased（可选，重新措辞后的问题）。\n\n"
        f"{_json_block(context)}"
    )
    return system_prompt, user_prompt


def build_summary_prompts(context: dict) -> tuple[str, str]:
    system_prompt = (
        "你是一个 AI 面试游戏的结算文案写手。"
        "请根据整局表现给出犀利但克制的结果总结。"
        "输出必须是合法 JSON，不要输出 Markdown，不要解释。"
    )
    user_prompt = (
        "请输出最终报告。"
        "返回 JSON，字段必须包含 verdict（offer/reject/pending 三者之一）、"
        "verdictLabel（展示用中文，如 “正式 Offer” / “未被录用” / “进入复试”）、"
        "summary、interviewerQuote、highlight、flop、tips、shareLines。"
        "shareLines 是长度为 3 的字符串数组。\n\n"
        f"{_json_block(context)}"
    )
    return system_prompt, user_prompt


def build_offer_prompts(context: dict) -> tuple[str, str]:
    """面试通过时生成一封"像模像样"的 Offer 文案。"""

    system_prompt = (
        "你是一个虚构公司的 HR 系统。你需要给通过面试的候选人生成一封简短的 Offer 邮件。"
        "输出必须是合法 JSON，不要输出 Markdown，不要解释。"
    )
    user_prompt = (
        "请输出 Offer 文案。"
        "返回 JSON，字段必须包含 company（虚构公司名）、"
        "position（岗位）、salaryRange（字符串，如 '25K-40K·14薪'）、"
        "startDate（字符串，如 '两周内'）、signature（面试官口吻的一句寄语）、"
        "body（邮件正文，2~4 句）。\n\n"
        f"{_json_block(context)}"
    )
    return system_prompt, user_prompt
