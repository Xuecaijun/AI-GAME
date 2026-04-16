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


def build_turn_prompts(context: dict, answer: str) -> tuple[str, str]:
    system_prompt = (
        "你是一个负责实时追问和评分的 AI 面试官。"
        "你要既像面试官，又像游戏导演。"
        "输出必须是合法 JSON，不要输出 Markdown，不要解释。"
    )
    user_prompt = (
        "请根据当前回合信息，评估候选人的回答质量，并生成下一道追问。"
        "返回 JSON，字段必须包含 scoreDelta、stressDelta、feedback、followUpQuestion、flags、dimensionDelta。"
        "dimensionDelta 是对象，键为 roleFit、logic、depth、consistency、composure、adaptability。\n\n"
        "当前回合上下文：\n"
        f"{_json_block(context)}\n\n"
        "候选人回答：\n"
        f"{answer}"
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
        "返回 JSON，字段必须包含 verdict、summary、interviewerQuote、highlight、flop、tips、shareLines。"
        "shareLines 是长度为 3 的字符串数组。\n\n"
        f"{_json_block(context)}"
    )
    return system_prompt, user_prompt
