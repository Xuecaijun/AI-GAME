from __future__ import annotations

import copy
import uuid
from typing import Any

from .ai_client import AIClient, AIClientError
from .mock_content import (
    COMMON_SKILLS,
    DIFFICULTIES,
    INTERVIEWERS,
    ROLE_LIBRARY,
    build_theme_blurb,
    generate_mock_resume,
    get_difficulty,
    get_interviewer,
    get_role,
)


DIMENSION_KEYS = [
    "roleFit",
    "logic",
    "depth",
    "consistency",
    "composure",
    "adaptability",
]


class GameEngine:
    def __init__(self) -> None:
        self.ai_client = AIClient()
        self.sessions: dict[str, dict[str, Any]] = {}

    def get_bootstrap(self) -> dict[str, Any]:
        return {
            "appName": "终面：AI面试官",
            "tagline": "AI 驱动的动态面试生存游戏",
            "roles": ROLE_LIBRARY,
            "interviewers": INTERVIEWERS,
            "difficulties": [{"id": key, **value} for key, value in DIFFICULTIES.items()],
            "runtime": self.ai_client.runtime_status(),
        }

    def generate_mock_resume(self, payload: dict[str, Any]) -> dict[str, Any]:
        role = get_role(payload.get("roleId", ""))
        difficulty = get_difficulty(payload.get("difficulty", "normal"))
        keyword = (payload.get("themeKeyword") or "").strip()
        return {
            "resumeText": generate_mock_resume(role, keyword, difficulty),
            "role": role,
            "difficulty": difficulty,
        }

    def start_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        role = get_role(payload.get("roleId", ""))
        interviewer = get_interviewer(payload.get("interviewerId", ""))
        difficulty = get_difficulty(payload.get("difficulty", "normal"))
        theme_keyword = (payload.get("themeKeyword") or "").strip()
        resume_mode = payload.get("resumeMode", "custom")
        provided_resume = (payload.get("resumeText") or "").strip()

        if resume_mode == "ai-generated":
            resume_text = provided_resume or generate_mock_resume(role, theme_keyword, difficulty)
        else:
            resume_text = provided_resume

        if not resume_text:
            raise ValueError("简历内容不能为空。")

        analysis = self._analyze_resume(resume_text, role, theme_keyword)
        opening = self._build_opening(role, interviewer, difficulty, theme_keyword, analysis, resume_text)

        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "themeKeyword": theme_keyword,
            "resumeMode": resume_mode,
            "resumeText": resume_text,
            "role": role,
            "interviewer": interviewer,
            "difficulty": difficulty,
            "analysis": analysis,
            "turn": 1,
            "maxTurns": difficulty["max_turns"],
            "score": 60,
            "stress": difficulty["starting_stress"],
            "dimensions": {key: 60 for key in DIMENSION_KEYS},
            "transcript": [
                {"speaker": "interviewer", "text": opening["openingLine"]},
                {"speaker": "question", "text": opening["firstQuestion"]},
            ],
            "turnResults": [],
            "currentQuestion": opening["firstQuestion"],
            "focusPoints": opening.get("focusPoints") or analysis["followUpFocus"],
            "usedFocusPoints": [],
            "questionHistory": [opening["firstQuestion"]],
        }
        self.sessions[session_id] = session
        return self._session_payload(session)

    def submit_answer(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = payload.get("sessionId", "")
        answer = (payload.get("answer") or "").strip()
        if not answer:
            raise ValueError("回答不能为空。")

        session = self.sessions.get(session_id)
        if not session:
            raise ValueError("会话不存在，请重新开始。")

        session["transcript"].append({"speaker": "candidate", "text": answer})

        evaluation = self._evaluate_answer(session, answer)
        session["turnResults"].append(
            {
                "turn": session["turn"],
                "question": session["currentQuestion"],
                "answer": answer,
                **evaluation,
            }
        )

        session["score"] = self._clamp(session["score"] + evaluation["scoreDelta"], 0, 100)
        session["stress"] = self._clamp(session["stress"] + evaluation["stressDelta"], 0, 100)
        for key, delta in evaluation["dimensionDelta"].items():
            session["dimensions"][key] = self._clamp(session["dimensions"][key] + delta, 0, 100)

        session["transcript"].append({"speaker": "feedback", "text": evaluation["feedback"]})

        should_finish = session["turn"] >= session["maxTurns"] or session["stress"] >= 95
        if should_finish:
            report = self._build_final_report(session)
            session["finalReport"] = report
            return {
                **self._session_payload(session),
                "isFinal": True,
                "report": report,
            }

        next_question = evaluation["followUpQuestion"]
        session["turn"] += 1
        session["currentQuestion"] = next_question
        session["questionHistory"].append(next_question)
        session["transcript"].append({"speaker": "question", "text": next_question})

        return {
            **self._session_payload(session),
            "isFinal": False,
        }

    def _session_payload(self, session: dict[str, Any]) -> dict[str, Any]:
        return {
            "sessionId": session["id"],
            "runtime": self.ai_client.runtime_status(),
            "selected": {
                "role": session["role"],
                "interviewer": session["interviewer"],
                "difficulty": session["difficulty"],
                "themeKeyword": session["themeKeyword"],
                "resumeMode": session["resumeMode"],
            },
            "metrics": {
                "turn": session["turn"],
                "maxTurns": session["maxTurns"],
                "score": session["score"],
                "stress": session["stress"],
                "dimensions": copy.deepcopy(session["dimensions"]),
            },
            "resumeText": session["resumeText"],
            "analysis": session["analysis"],
            "transcript": copy.deepcopy(session["transcript"]),
        }

    def _analyze_resume(self, resume_text: str, role: dict[str, Any], theme_keyword: str) -> dict[str, Any]:
        hits = [item for item in role["keywords"] if item.lower() in resume_text.lower()]
        common_hits = [item for item in COMMON_SKILLS if item.lower() in resume_text.lower()]
        risks = []

        if len(resume_text) < 120:
            risks.append("简历篇幅偏短，容易被追问到细节缺口。")
        if len(hits) < 2:
            risks.append("与目标岗位的显性关键词重合偏少，需要靠回答补足匹配度。")
        if "负责" not in resume_text and "主导" not in resume_text:
            risks.append("职责边界描述较弱，面试官可能重点追问你具体做了什么。")
        if theme_keyword and theme_keyword not in resume_text:
            risks.append(f"比赛关键词“{theme_keyword}”没有出现在简历里，回答时要主动补位。")
        if not risks:
            risks.append("整体比较顺，但仍要注意把项目结果讲具体。")

        focus = self._dedupe(hits + common_hits + role["keywords"])[:5]
        strengths = []
        if hits:
            strengths.append(f"岗位关键词命中：{', '.join(hits[:3])}")
        if common_hits:
            strengths.append(f"通用能力覆盖：{', '.join(common_hits[:3])}")
        if theme_keyword and theme_keyword in resume_text:
            strengths.append(f"已经把比赛关键词“{theme_keyword}”写进项目语境。")
        if not strengths:
            strengths.append("履历基础完整，可通过临场表达争取分数。")

        return {
            "strengths": strengths,
            "riskPoints": risks,
            "followUpFocus": focus,
            "themeBlurb": build_theme_blurb(theme_keyword, role),
        }

    def _build_opening(
        self,
        role: dict[str, Any],
        interviewer: dict[str, Any],
        difficulty: dict[str, Any],
        theme_keyword: str,
        analysis: dict[str, Any],
        resume_text: str,
    ) -> dict[str, Any]:
        context = {
            "themeKeyword": theme_keyword,
            "role": role,
            "interviewer": interviewer,
            "difficulty": difficulty,
            "analysis": analysis,
            "resumeText": resume_text,
        }
        if self.ai_client.configured:
            try:
                ai_result = self.ai_client.generate_opening(context)
                if ai_result.get("openingLine") and ai_result.get("firstQuestion"):
                    return ai_result
            except AIClientError:
                pass

        return {
            "openingLine": interviewer["opening_line"],
            "firstQuestion": self._local_opening_question(role, interviewer, theme_keyword),
            "focusPoints": analysis["followUpFocus"],
        }

    def _evaluate_answer(self, session: dict[str, Any], answer: str) -> dict[str, Any]:
        context = {
            "themeKeyword": session["themeKeyword"],
            "role": session["role"],
            "interviewer": session["interviewer"],
            "difficulty": session["difficulty"],
            "analysis": session["analysis"],
            "currentQuestion": session["currentQuestion"],
            "turn": session["turn"],
            "score": session["score"],
            "stress": session["stress"],
            "dimensions": session["dimensions"],
            "transcriptTail": session["transcript"][-6:],
        }
        if self.ai_client.configured:
            try:
                ai_result = self.ai_client.evaluate_turn(context, answer)
                normalized = self._normalize_ai_turn(ai_result)
                if normalized:
                    return normalized
            except AIClientError:
                pass
        return self._local_evaluate_answer(session, answer)

    def _local_evaluate_answer(self, session: dict[str, Any], answer: str) -> dict[str, Any]:
        answer_length = len(answer)
        role_keywords = session["role"]["keywords"]
        theme_keyword = session["themeKeyword"]

        score_delta = 0
        stress_delta = 0
        flags = []
        dimension_delta = {key: 0 for key in DIMENSION_KEYS}

        if answer_length < 30:
            score_delta -= 10
            stress_delta += 12
            flags.append("回答过短")
            dimension_delta["logic"] -= 6
            dimension_delta["composure"] -= 5
        elif answer_length < 80:
            score_delta += 1
            stress_delta += 3
            flags.append("细节不足")
        else:
            score_delta += 6
            stress_delta -= 4
            dimension_delta["logic"] += 4
            dimension_delta["composure"] += 2

        keyword_hits = [item for item in role_keywords if item.lower() in answer.lower()]
        if keyword_hits:
            score_delta += min(8, len(keyword_hits) * 3)
            dimension_delta["roleFit"] += min(6, len(keyword_hits) * 2)

        if any(token in answer for token in ["负责", "主导", "拆解", "复盘", "优化", "验证", "协作"]):
            score_delta += 4
            dimension_delta["depth"] += 3
            dimension_delta["adaptability"] += 2

        if any(char.isdigit() for char in answer):
            score_delta += 4
            dimension_delta["depth"] += 3
            dimension_delta["consistency"] += 1

        if "因为" in answer and "所以" in answer:
            score_delta += 3
            dimension_delta["logic"] += 3

        if theme_keyword and theme_keyword in answer:
            score_delta += 3
            dimension_delta["roleFit"] += 2

        if any(token in answer for token in ["不知道", "忘了", "不太清楚", "没做过"]):
            score_delta -= 12
            stress_delta += 10
            flags.append("暴露不确定性")
            dimension_delta["consistency"] -= 6
            dimension_delta["composure"] -= 4

        if any(token in answer for token in ["大概", "差不多", "应该"]):
            score_delta -= 4
            stress_delta += 5
            flags.append("表达模糊")
            dimension_delta["consistency"] -= 3

        if not flags and score_delta >= 10:
            feedback_key = "strong"
        elif score_delta >= 4:
            feedback_key = "mid"
        else:
            feedback_key = "weak"

        feedback = self._build_interviewer_feedback(session["interviewer"]["id"], feedback_key)

        follow_up = self._build_follow_up_question(session, answer, flags, keyword_hits)
        return {
            "scoreDelta": score_delta,
            "stressDelta": stress_delta,
            "feedback": feedback,
            "followUpQuestion": follow_up,
            "flags": flags,
            "dimensionDelta": dimension_delta,
        }

    def _build_follow_up_question(
        self,
        session: dict[str, Any],
        answer: str,
        flags: list[str],
        keyword_hits: list[str],
    ) -> str:
        theme_keyword = session["themeKeyword"]
        focus = self._choose_follow_up_focus(session, keyword_hits)

        if "回答过短" in flags:
            return "你还是太概括了。请只讲一个你亲自负责的动作，并说明最后结果。"
        if "暴露不确定性" in flags:
            return "你说自己不太确定，那我换个问法：这件事里你能百分之百确认的部分是什么？"
        if theme_keyword and theme_keyword not in answer:
            return f"你还没有把“{theme_keyword}”真正放进方案里。现在补充一下，它具体影响了什么设计决策？"
        if session["turn"] == 1:
            question_key = "decision"
        elif session["turn"] == 2:
            question_key = "mistake"
        else:
            question_key = "pressure"

        question = self._build_interviewer_question(
            session["interviewer"]["id"],
            focus,
            question_key,
        )

        if self._question_seen_recently(session, question):
            question = self._build_distinct_fallback_question(session, focus)

        return question

    def _choose_follow_up_focus(self, session: dict[str, Any], keyword_hits: list[str]) -> str:
        used = session.setdefault("usedFocusPoints", [])
        candidates: list[str] = []

        for item in keyword_hits:
            if item not in candidates:
                candidates.append(item)

        for item in session.get("focusPoints", []):
            if item not in candidates:
                candidates.append(item)

        for item in session["role"]["keywords"]:
            if item not in candidates:
                candidates.append(item)

        current_question = session.get("currentQuestion", "")
        for item in candidates:
            if item in used:
                continue
            if item and item in current_question:
                continue
            used.append(item)
            return item

        fallback = candidates[session["turn"] % len(candidates)] if candidates else "项目经历"
        if fallback not in used:
            used.append(fallback)
        return fallback

    def _question_seen_recently(self, session: dict[str, Any], question: str) -> bool:
        normalized = self._normalize_question(question)
        recent_questions = session.get("questionHistory", [])[-2:]
        return any(self._normalize_question(item) == normalized for item in recent_questions)

    def _build_distinct_fallback_question(self, session: dict[str, Any], focus: str) -> str:
        interviewer_id = session["interviewer"]["id"]
        variants = {
            "cold-judge": [
                f"别绕。就说“{focus}”，你亲自拍板的那个决定是什么？",
                f"就盯着“{focus}”。你做过最具体的一次优化是什么？",
                f"如果“{focus}”这块交给别人，你最担心哪里先出问题？",
            ],
            "spark-hr": [
                f"我们把范围缩小一点，只聊“{focus}”。你当时最关键的一个决定是什么？",
                f"那我们继续顺着“{focus}”聊。你做过最实的一次优化是什么？",
                f"如果把“{focus}”交给别人来做，你最担心哪个环节会掉链子？",
            ],
            "tactical-lead": [
                f"聚焦“{focus}”。你当时真正承担判断责任的那个决策点是什么？",
                f"继续拆“{focus}”。你做过最有效的一次优化动作是什么？",
                f"如果“{focus}”交接出去，最可能失真的环节在哪里？",
            ],
            "blackbox-ai": [
                f"请缩小讨论范围，仅回答“{focus}”对应的关键决策节点。",
                f"继续解析“{focus}”。请输出一次最具体的优化动作。",
                f"若“{focus}”模块被转交，最可能发生的故障点是什么？",
            ],
        }
        selected = variants.get(interviewer_id, variants["cold-judge"])
        index = min(session["turn"] - 1, len(selected) - 1)
        return selected[index]

    def _normalize_question(self, question: str) -> str:
        return "".join(question.split())

    def _build_final_report(self, session: dict[str, Any]) -> dict[str, Any]:
        context = {
            "themeKeyword": session["themeKeyword"],
            "role": session["role"],
            "interviewer": session["interviewer"],
            "difficulty": session["difficulty"],
            "score": session["score"],
            "stress": session["stress"],
            "dimensions": session["dimensions"],
            "turnResults": session["turnResults"],
            "analysis": session["analysis"],
        }
        if self.ai_client.configured:
            try:
                ai_result = self.ai_client.summarize_session(context)
                normalized = self._normalize_ai_summary(session, ai_result)
                if normalized:
                    return normalized
            except AIClientError:
                pass
        return self._local_final_report(session)

    def _local_final_report(self, session: dict[str, Any]) -> dict[str, Any]:
        score = session["score"]
        if score >= 85:
            verdict = "Offer"
            summary = "整体表现稳，回答有结构，也能把关键词接进真实方案。"
        elif score >= 72:
            verdict = "进入复试"
            summary = "基本盘不错，但部分回答还需要更强的证据和细节支撑。"
        elif score >= 60:
            verdict = "待定"
            summary = "有潜力，但亮点和风险并存，面试官暂时不会给出明确结论。"
        else:
            verdict = "不通过"
            summary = "回答缺少支撑，逻辑和一致性不够稳定，没能撑住高压追问。"

        best_turn = max(session["turnResults"], key=lambda item: item["scoreDelta"])
        worst_turn = min(session["turnResults"], key=lambda item: item["scoreDelta"])

        return {
            "verdict": verdict,
            "summary": summary,
            "interviewerQuote": self._pick_quote(session["interviewer"]["id"], verdict),
            "highlight": best_turn["answer"],
            "flop": worst_turn["answer"],
            "tips": self._build_tips(session),
            "shareLines": [
                f"{session['role']['title']} 面试结果：{verdict}",
                f"总分 {session['score']}，压力值 {session['stress']}",
                session["analysis"]["themeBlurb"],
            ],
            "dimensions": copy.deepcopy(session["dimensions"]),
        }

    def _normalize_ai_turn(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        if not payload.get("feedback") or not payload.get("followUpQuestion"):
            return None
        dimension_delta = payload.get("dimensionDelta") or {}
        normalized_dimensions = {key: int(dimension_delta.get(key, 0)) for key in DIMENSION_KEYS}
        return {
            "scoreDelta": int(payload.get("scoreDelta", 0)),
            "stressDelta": int(payload.get("stressDelta", 0)),
            "feedback": str(payload.get("feedback", "")).strip(),
            "followUpQuestion": str(payload.get("followUpQuestion", "")).strip(),
            "flags": [str(item) for item in payload.get("flags", [])][:4],
            "dimensionDelta": normalized_dimensions,
        }

    def _normalize_ai_summary(self, session: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        required = ["verdict", "summary", "interviewerQuote", "highlight", "flop", "tips", "shareLines"]
        if any(not payload.get(key) for key in required):
            return None
        return {
            "verdict": str(payload["verdict"]),
            "summary": str(payload["summary"]),
            "interviewerQuote": str(payload["interviewerQuote"]),
            "highlight": str(payload["highlight"]),
            "flop": str(payload["flop"]),
            "tips": str(payload["tips"]),
            "shareLines": [str(item) for item in payload.get("shareLines", [])][:3],
            "dimensions": copy.deepcopy(session["dimensions"]),
        }

    def _local_opening_question(self, role: dict[str, Any], interviewer: dict[str, Any], theme_keyword: str) -> str:
        if theme_keyword:
            return (
                f"先做个开场。你要应聘“{role['title']}”，而本场关键词是“{theme_keyword}”。"
                f"请介绍你自己，并说明你会怎样把“{theme_keyword}”落进一个真实产品。"
            )
        opening_by_interviewer = {
            "cold-judge": f"先别讲空话。你为什么配得上“{role['title']}”这个岗位？直接给我最有说服力的一段经历。",
            "spark-hr": f"我们轻松一点开始。你先介绍一下自己，再说说你为什么会想做“{role['title']}”。",
            "tactical-lead": f"先做一个结构化开场：你为什么适合“{role['title']}”，你的核心判断依据是什么？",
            "blackbox-ai": f"请执行自我陈述。输出你与“{role['title']}”岗位匹配度最高的经历样本。",
        }
        return opening_by_interviewer.get(interviewer["id"], role["opening_questions"][0])

    def _build_interviewer_feedback(self, interviewer_id: str, level: str) -> str:
        feedback_map = {
            "cold-judge": {
                "strong": "这次像样了。有动作、有判断，也有结果。别在下一题掉回空话。",
                "mid": "方向对，但还不够硬。把方法、依据和结果讲得再扎实一点。",
                "weak": "这段回答站不住。你需要更具体的职责、依据和结果。",
            },
            "spark-hr": {
                "strong": "这次就很清楚了，像一次完整复盘，我能听到你真正做了什么。",
                "mid": "整体方向没问题，但如果细节再落一点，说服力会明显更强。",
                "weak": "这段还比较虚，我还没听到足够具体的动作和结果。",
            },
            "tactical-lead": {
                "strong": "结构是清楚的，判断过程也完整，这样的回答更像能独立负责的人。",
                "mid": "基本思路成立，但论证链条还差一截，尤其是取舍依据。",
                "weak": "这段缺少决策逻辑，听起来更像参与过，而不是主导过。",
            },
            "blackbox-ai": {
                "strong": "回答质量提升。信息密度、因果链路与可信度均达到较优水平。",
                "mid": "回答有效，但证据密度仍不足，建议补充更明确的动作与结果。",
                "weak": "回答可信度偏低。缺少可验证动作、依据与结果样本。",
            },
        }
        return feedback_map.get(interviewer_id, feedback_map["cold-judge"])[level]

    def _build_interviewer_question(self, interviewer_id: str, focus: str, question_key: str) -> str:
        templates = {
            "cold-judge": {
                "decision": f"回到你的简历，我就盯“{focus}”。你只讲一个最能代表你的实际决策，别铺垫，直接说取舍依据。",
                "mistake": f"继续说“{focus}”。这里最容易做错的地方是什么？如果重来一次，你具体改哪一步？",
                "pressure": f"现在假设你的“{focus}”方案上线后数据不及预期，而且只给你一天时间修正。你先查什么？为什么？",
            },
            "spark-hr": {
                "decision": f"我们顺着“{focus}”往下聊。你挑一个最能代表你的真实决策，说说你当时是怎么想的。",
                "mistake": f"那如果继续看“{focus}”，你觉得这里最容易踩的坑是什么？如果重来，你会怎么改？",
                "pressure": f"假设“{focus}”上线后反馈不理想，而且时间特别紧，你会先看哪些信号来判断问题出在哪？",
            },
            "tactical-lead": {
                "decision": f"聚焦“{focus}”。请给我一个你真正负责判断的决策点，并拆开讲清楚你的取舍逻辑。",
                "mistake": f"继续拆“{focus}”。这里最容易失误的环节是什么？复盘一次的话，你会怎样修正决策路径？",
                "pressure": f"如果“{focus}”上线后核心指标不达预期，且你只有一天窗口期，你会按什么优先级排查？",
            },
            "blackbox-ai": {
                "decision": f"请聚焦“{focus}”。输出一个由你主导的关键决策样本，并说明判断依据。",
                "mistake": f"继续分析“{focus}”。该模块最易出现的错误点是什么？若重新执行，你将如何修正？",
                "pressure": f"场景更新：“{focus}”上线结果低于预期，你仅有一天修正时间。请给出排查优先级。",
            },
        }
        return templates.get(interviewer_id, templates["cold-judge"])[question_key]

    def _pick_quote(self, interviewer_id: str, verdict: str) -> str:
        quotes = {
            "cold-judge": {
                "Offer": "你不是最会说的人，但你有判断力。这比漂亮话值钱。",
                "进入复试": "基本够格，但我还没完全信你。",
                "待定": "你有想法，可惜证据不够。",
                "不通过": "简历写得比回答更像你本人。",
            },
            "spark-hr": {
                "Offer": "你挺会讲故事，但更重要的是，你讲得出细节。",
                "进入复试": "我愿意让你进下一轮，不过还想再听你展开一次项目复盘。",
                "待定": "状态还行，但亮点没有真正立住。",
                "不通过": "别紧张，你只是还没有把经历讲成可信的经历。",
            },
            "tactical-lead": {
                "Offer": "结构、取舍、复盘都在线，这是能落地的人。",
                "进入复试": "思路有了，但方法论还差最后一层。",
                "待定": "能聊，但还谈不上可靠。",
                "不通过": "你更像参与者，而不是能独立负责的人。",
            },
            "blackbox-ai": {
                "Offer": "可信度校验通过。你不仅会说，也能自证。",
                "进入复试": "候选人存在可用潜力，建议进入下一轮采样。",
                "待定": "数据不足，暂不输出强结论。",
                "不通过": "叙述连续性不足。建议重建样本。",
            },
        }
        return quotes.get(interviewer_id, quotes["cold-judge"]).get(verdict, "")

    def _build_tips(self, session: dict[str, Any]) -> str:
        low_dimensions = sorted(session["dimensions"].items(), key=lambda item: item[1])[:2]
        labels = {
            "roleFit": "岗位匹配度",
            "logic": "逻辑表达",
            "depth": "专业深度",
            "consistency": "一致性",
            "composure": "抗压表现",
            "adaptability": "临场反应",
        }
        tips = [labels[key] for key, _ in low_dimensions]
        return f"下一次优先补强：{'、'.join(tips)}。回答时尽量给出动作、依据和结果。"

    def _dedupe(self, values: list[str]) -> list[str]:
        seen = set()
        result = []
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result

    def _clamp(self, value: int, low: int, high: int) -> int:
        return max(low, min(high, int(value)))
