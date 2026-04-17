"""主引擎：轮次状态机 + 深挖/提示/随机事件 + Offer 判定。

状态转换概览：

    start_session()
        └─> opening → awaiting_answer (R1)

    submit_answer():
        judging → (correct | partial | wrong)
            correct / partial:
                roll drill_probability[drillDepth]
                    yes & depth < 3  -> drillDepth++，awaiting_answer (同轮)
                    no               -> round_end
            wrong:
                roll hint_probability & hintsUsed < 3
                    yes              -> hint，awaiting_answer (同题)
                    no               -> round_end (本轮折扣)

    submit_timeout():
        记为本题 0 分，round_end (直接结束本轮)

    round_end():
        roll inter_round_event
            无影响        -> 写 transcript，下一轮或 final
            有影响        -> 返回 phase=event，等 /session/event
        检查 roundIndex >= totalRounds -> final

    submit_event():
        resolve → 加减分 → 如 ends=True -> final，
                            否则按原触发位置继续
"""

from __future__ import annotations

import copy
import random
import time
import uuid
from typing import Any

from .ai_client import AIClient, AIClientError
from .events import narration_bubble, public_event_payload, resolve_event, roll_event
from .interviewers import all_interviewers, get_interviewer, public_card
from .mock_content import (
    COMMON_SKILLS,
    DIFFICULTIES,
    ROLE_LIBRARY,
    build_theme_blurb,
    generate_mock_resume,
    get_difficulty,
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

ROUND_BASE_SCORE = 100
DRILL_PENALTY_PARTIAL = 12
DRILL_PENALTY_WRONG = 28
HINT_PENALTY = 8
TIMEOUT_SCORE = 10


class GameEngine:
    def __init__(self) -> None:
        self.ai_client = AIClient()
        self.sessions: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------ bootstrap

    def get_bootstrap(self) -> dict[str, Any]:
        return {
            "appName": "终面：AI面试官",
            "tagline": "AI 驱动的动态面试生存游戏",
            "roles": ROLE_LIBRARY,
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

    # ------------------------------------------------------------------ invitation

    def build_invitations(self, payload: dict[str, Any]) -> dict[str, Any]:
        role = get_role(payload.get("roleId", ""))
        difficulty = get_difficulty(payload.get("difficulty", "normal"))
        resume_text = (payload.get("resumeText") or "").strip()
        theme_keyword = (payload.get("themeKeyword") or "").strip()

        if not resume_text:
            raise ValueError("请先填写或生成简历。")

        analysis = self._analyze_resume(resume_text, role, theme_keyword)

        all_items = list(all_interviewers())
        if not all_items:
            raise ValueError("面试官池为空，请检查 backend/interviewers/ 目录。")

        count = min(3, len(all_items))
        random.shuffle(all_items)
        picked = all_items[:count]

        return {
            "role": role,
            "difficulty": difficulty,
            "analysis": analysis,
            "invitations": [public_card(item) for item in picked],
        }

    # ------------------------------------------------------------------ session lifecycle

    def start_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        role = get_role(payload.get("roleId", ""))
        difficulty = get_difficulty(payload.get("difficulty", "normal"))
        interviewer = get_interviewer(payload.get("interviewerId", ""))
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

        min_rounds = int(interviewer.get("min_rounds", 3))
        max_rounds = int(interviewer.get("max_rounds", 5))
        difficulty_boost = int(difficulty.get("max_turns", min_rounds)) - 3
        total_rounds = random.randint(
            min_rounds,
            max(min_rounds, min(max_rounds, max_rounds + max(0, difficulty_boost))),
        )

        first = self._build_opening(role, interviewer, difficulty, theme_keyword, analysis, resume_text)

        session_id = str(uuid.uuid4())
        session: dict[str, Any] = {
            "id": session_id,
            "createdAt": time.time(),
            "role": role,
            "interviewer": interviewer,
            "difficulty": difficulty,
            "themeKeyword": theme_keyword,
            "resumeMode": resume_mode,
            "resumeText": resume_text,
            "analysis": analysis,
            # 状态机
            "currentPhase": "awaiting_answer",
            "roundIndex": 1,
            "totalRounds": total_rounds,
            "drillDepth": 0,
            "hintsUsed": 0,
            "currentQuestion": first["firstQuestion"],
            "currentTopic": first.get("topic", ""),
            "roundScore": ROUND_BASE_SCORE,
            "roundScores": [],
            "roundFlags": [],
            "sessionStress": int(difficulty.get("starting_stress", 20)),
            "dimensions": {key: 60 for key in DIMENSION_KEYS},
            "transcript": [
                {"speaker": "interviewer", "text": first["openingLine"]},
                {"speaker": "question", "text": first["firstQuestion"]},
            ],
            "questionHistory": [first["firstQuestion"]],
            "focusPoints": first.get("focusPoints") or analysis["followUpFocus"],
            "usedFocusPoints": [],
            "firedEvents": set(),
            "pendingEvent": None,
            "pendingEventTrigger": None,
            "ended": False,
            "finalReport": None,
        }
        self.sessions[session_id] = session

        return self._descriptor(
            session,
            phase="awaiting_answer",
            question=first["firstQuestion"],
            timer_ms=int(interviewer.get("answer_time_ms", 90_000)),
        )

    # ------------------------------------------------------------------ actions

    def submit_answer(self, payload: dict[str, Any]) -> dict[str, Any]:
        session = self._require_session(payload)
        answer = (payload.get("answer") or "").strip()
        if not answer:
            raise ValueError("回答不能为空。")
        if session["ended"]:
            raise ValueError("本场面试已结束。")
        if session["currentPhase"] != "awaiting_answer":
            raise ValueError("当前阶段不接受回答。")

        session["transcript"].append({"speaker": "candidate", "text": answer})

        judge = self._judge_answer(session, answer)
        session["transcript"].append({"speaker": "feedback", "text": judge["feedback"]})

        for key, delta in judge["dimensionDelta"].items():
            session["dimensions"][key] = self._clamp(session["dimensions"][key] + delta, 0, 100)
        session["sessionStress"] = self._clamp(
            session["sessionStress"] + int(judge.get("stressDelta", 0)), 0, 100
        )

        verdict = judge["verdict"]
        if verdict in ("correct", "partial"):
            if verdict == "partial":
                session["roundScore"] = max(0, session["roundScore"] - DRILL_PENALTY_PARTIAL)
                session["roundFlags"].append("answer_partial")

            if self._roll_drill(session):
                return self._advance_drill(session)
            return self._close_round_and_advance(session)

        # verdict == wrong
        session["roundScore"] = max(0, session["roundScore"] - DRILL_PENALTY_WRONG)
        session["roundFlags"].append("answer_wrong")

        if self._roll_hint(session):
            return self._advance_hint(session)
        return self._close_round_and_advance(session)

    def submit_timeout(self, payload: dict[str, Any]) -> dict[str, Any]:
        session = self._require_session(payload)
        if session["ended"]:
            raise ValueError("本场面试已结束。")
        if session["currentPhase"] != "awaiting_answer":
            raise ValueError("当前阶段没有计时题目。")

        session["transcript"].append({"speaker": "candidate", "text": "（超时未作答）"})
        session["transcript"].append({
            "speaker": "feedback",
            "text": self._timeout_feedback(session),
        })
        session["roundScore"] = min(session["roundScore"], TIMEOUT_SCORE)
        session["roundFlags"].append("timeout")

        session["dimensions"]["composure"] = self._clamp(
            session["dimensions"]["composure"] - 8, 0, 100
        )
        session["dimensions"]["adaptability"] = self._clamp(
            session["dimensions"]["adaptability"] - 6, 0, 100
        )
        session["sessionStress"] = self._clamp(session["sessionStress"] + 12, 0, 100)

        return self._close_round_and_advance(session, forced_wrong=True)

    def submit_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        session = self._require_session(payload)
        event = session.get("pendingEvent")
        trigger = session.get("pendingEventTrigger")
        if not event:
            raise ValueError("当前没有待处理的随机事件。")
        if session["ended"]:
            raise ValueError("本场面试已结束。")

        submission = {
            "choiceId": payload.get("choiceId"),
            "text": payload.get("text"),
            "timedOut": bool(payload.get("timedOut")),
        }
        result = resolve_event(event, submission)

        if result.get("playerText"):
            session["transcript"].append(
                {"speaker": "candidate", "text": result["playerText"]}
            )
        elif submission["choiceId"]:
            label = self._event_choice_label(event, submission["choiceId"])
            if label:
                session["transcript"].append({"speaker": "candidate", "text": f"（你选择）{label}"})
        elif submission["timedOut"]:
            session["transcript"].append({"speaker": "candidate", "text": "（事件未作回应）"})

        if result["note"]:
            session["transcript"].append({"speaker": "system", "text": result["note"]})

        session["sessionStress"] = self._clamp(
            session["sessionStress"] + (5 if result["scoreDelta"] < 0 else -3),
            0,
            100,
        )

        if result["scoreDelta"]:
            session["roundScore"] = self._clamp(
                session["roundScore"] + result["scoreDelta"], 0, 120
            )
            session["dimensions"]["adaptability"] = self._clamp(
                session["dimensions"]["adaptability"]
                + (3 if result["scoreDelta"] > 0 else -4),
                0,
                100,
            )

        session["pendingEvent"] = None
        session["pendingEventTrigger"] = None

        if result["ends"]:
            return self._finalize(session, forced_end_reason="event_ends")

        if trigger == "intra_round":
            return self._descriptor(
                session,
                phase="awaiting_answer",
                question=session["currentQuestion"],
                timer_ms=int(session["interviewer"].get("answer_time_ms", 90_000)),
            )
        return self._start_next_round_or_final(session)

    # ------------------------------------------------------------------ state transitions

    def _advance_drill(self, session: dict[str, Any]) -> dict[str, Any]:
        session["drillDepth"] += 1
        session["hintsUsed"] = 0
        question = self._build_drill_question(session)
        session["currentQuestion"] = question
        session["questionHistory"].append(question)
        session["transcript"].append({"speaker": "question", "text": f"[追问 {session['drillDepth']}] {question}"})

        # 深挖阶段也可能触发轮内事件
        if session["pendingEvent"] is None:
            event = roll_event(session["interviewer"], "intra_round", session)
            if event:
                return self._attach_event(session, event, trigger="intra_round")

        return self._descriptor(
            session,
            phase="awaiting_answer",
            question=question,
            timer_ms=int(session["interviewer"].get("answer_time_ms", 90_000)),
        )

    def _advance_hint(self, session: dict[str, Any]) -> dict[str, Any]:
        session["hintsUsed"] += 1
        session["roundScore"] = max(0, session["roundScore"] - HINT_PENALTY)
        hint = self._build_hint(session)
        session["transcript"].append({"speaker": "system", "text": f"[提示 {session['hintsUsed']}/3] {hint}"})
        return self._descriptor(
            session,
            phase="awaiting_answer",
            question=session["currentQuestion"],
            timer_ms=int(session["interviewer"].get("answer_time_ms", 90_000)),
            hint=hint,
        )

    def _close_round_and_advance(
        self,
        session: dict[str, Any],
        forced_wrong: bool = False,
    ) -> dict[str, Any]:
        final_round_score = int(round(session["roundScore"] * session["difficulty"].get("score_multiplier", 1.0)))
        final_round_score = self._clamp(final_round_score, 0, 100)
        session["roundScores"].append(
            {
                "round": session["roundIndex"],
                "score": final_round_score,
                "drillDepth": session["drillDepth"],
                "hintsUsed": session["hintsUsed"],
                "flags": list(session["roundFlags"]),
                "question": session["currentQuestion"],
            }
        )
        session["transcript"].append(
            {
                "speaker": "system",
                "text": f"第 {session['roundIndex']} 轮结算：{final_round_score} 分。",
            }
        )

        return self._start_next_round_or_final(session)

    def _start_next_round_or_final(self, session: dict[str, Any]) -> dict[str, Any]:
        if session["roundIndex"] >= session["totalRounds"]:
            return self._finalize(session)

        # 轮间事件
        event = roll_event(session["interviewer"], "inter_round", session)
        if event:
            if event.get("impact"):
                return self._attach_event(session, event, trigger="inter_round")
            session["transcript"].append(
                {"speaker": "system", "text": narration_bubble(event)}
            )

        session["roundIndex"] += 1
        session["drillDepth"] = 0
        session["hintsUsed"] = 0
        session["roundScore"] = ROUND_BASE_SCORE
        session["roundFlags"] = []
        question = self._build_round_question(session)
        session["currentQuestion"] = question
        session["questionHistory"].append(question)
        session["transcript"].append(
            {
                "speaker": "question",
                "text": f"[第 {session['roundIndex']} 轮] {question}",
            }
        )

        # 轮内事件
        intra = roll_event(session["interviewer"], "intra_round", session)
        if intra:
            if intra.get("impact"):
                return self._attach_event(session, intra, trigger="intra_round")
            session["transcript"].append(
                {"speaker": "system", "text": narration_bubble(intra)}
            )

        return self._descriptor(
            session,
            phase="awaiting_answer",
            question=question,
            timer_ms=int(session["interviewer"].get("answer_time_ms", 90_000)),
        )

    def _attach_event(
        self,
        session: dict[str, Any],
        event: dict[str, Any],
        trigger: str,
    ) -> dict[str, Any]:
        session["pendingEvent"] = event
        session["pendingEventTrigger"] = trigger
        session["transcript"].append(
            {"speaker": "system", "text": narration_bubble(event)}
        )
        session["currentPhase"] = "event"
        return self._descriptor(
            session,
            phase="event",
            event=public_event_payload(event),
        )

    def _finalize(
        self,
        session: dict[str, Any],
        forced_end_reason: str | None = None,
    ) -> dict[str, Any]:
        session["ended"] = True
        session["currentPhase"] = "final"
        report = self._build_final_report(session, forced_end_reason)
        session["finalReport"] = report
        return self._descriptor(session, phase="final", report=report)

    # ------------------------------------------------------------------ judge / drill / hint

    def _judge_answer(self, session: dict[str, Any], answer: str) -> dict[str, Any]:
        context = {
            "themeKeyword": session["themeKeyword"],
            "role": session["role"],
            "interviewer": {
                "id": session["interviewer"]["id"],
                "style": session["interviewer"]["style"],
                "tone": session["interviewer"]["tone"],
            },
            "difficulty": session["difficulty"],
            "analysis": session["analysis"],
            "roundIndex": session["roundIndex"],
            "drillDepth": session["drillDepth"],
            "currentQuestion": session["currentQuestion"],
            "transcriptTail": session["transcript"][-6:],
        }
        if self.ai_client.configured:
            try:
                result = self.ai_client.judge_answer(context, answer)
                normalized = self._normalize_judge(result)
                if normalized:
                    return normalized
            except AIClientError:
                pass
        return self._local_judge_answer(session, answer)

    def _normalize_judge(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        verdict = str(payload.get("verdict", "")).lower().strip()
        if verdict not in {"correct", "partial", "wrong"}:
            return None
        feedback = str(payload.get("feedback", "")).strip()
        if not feedback:
            return None
        dimension_delta = payload.get("dimensionDelta") or {}
        return {
            "verdict": verdict,
            "feedback": feedback,
            "scoreDelta": int(payload.get("scoreDelta", 0)),
            "stressDelta": int(payload.get("stressDelta", 0)),
            "flags": [str(item) for item in payload.get("flags", [])][:3],
            "dimensionDelta": {
                key: int(dimension_delta.get(key, 0)) for key in DIMENSION_KEYS
            },
        }

    def _local_judge_answer(self, session: dict[str, Any], answer: str) -> dict[str, Any]:
        role_keywords = session["role"]["keywords"]
        theme_keyword = session["themeKeyword"]
        length = len(answer)

        dimension_delta = {key: 0 for key in DIMENSION_KEYS}
        score_delta = 0
        flags: list[str] = []

        if length < 30:
            score_delta -= 10
            dimension_delta["logic"] -= 6
            dimension_delta["composure"] -= 4
            flags.append("回答过短")
        elif length < 80:
            score_delta += 1
            flags.append("细节不足")
        else:
            score_delta += 6
            dimension_delta["logic"] += 4
            dimension_delta["composure"] += 2

        hits = [item for item in role_keywords if item.lower() in answer.lower()]
        if hits:
            score_delta += min(8, len(hits) * 3)
            dimension_delta["roleFit"] += min(6, len(hits) * 2)

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
            dimension_delta["consistency"] -= 6
            dimension_delta["composure"] -= 4
            flags.append("暴露不确定性")
        if any(token in answer for token in ["大概", "差不多", "应该"]):
            score_delta -= 4
            dimension_delta["consistency"] -= 3
            flags.append("表达模糊")

        if score_delta >= 8 and "暴露不确定性" not in flags:
            verdict = "correct"
        elif score_delta >= 0:
            verdict = "partial"
        else:
            verdict = "wrong"

        feedback = self._build_interviewer_feedback(session["interviewer"]["id"], verdict)

        stress_delta = 5 if verdict == "wrong" else (-3 if verdict == "correct" else 0)

        return {
            "verdict": verdict,
            "feedback": feedback,
            "scoreDelta": score_delta,
            "stressDelta": stress_delta,
            "flags": flags,
            "dimensionDelta": dimension_delta,
        }

    def _build_drill_question(self, session: dict[str, Any]) -> str:
        context = {
            "mode": "drill",
            "role": session["role"],
            "interviewer": {
                "id": session["interviewer"]["id"],
                "style": session["interviewer"]["style"],
            },
            "drillDepth": session["drillDepth"],
            "currentQuestion": session["currentQuestion"],
            "transcriptTail": session["transcript"][-6:],
            "focusPoints": session.get("focusPoints", []),
        }
        if self.ai_client.configured:
            try:
                result = self.ai_client.generate_question(context)
                question = str(result.get("question", "")).strip()
                if question and not self._question_seen_recently(session, question):
                    return question
            except AIClientError:
                pass
        return self._local_drill_question(session)

    def _build_round_question(self, session: dict[str, Any]) -> str:
        bank = session["interviewer"].get("question_bank", [])
        asked = set(session.get("questionHistory", []))
        candidates = [item for item in bank if item.get("q") not in asked]
        if not candidates:
            candidates = bank

        if candidates:
            choice = random.choice(candidates)
            session["currentTopic"] = choice.get("topic", "")
            base_question = choice["q"]
        else:
            base_question = session["role"]["opening_questions"][0]

        if self.ai_client.configured:
            try:
                context = {
                    "mode": "round_open",
                    "role": session["role"],
                    "interviewer": {
                        "id": session["interviewer"]["id"],
                        "style": session["interviewer"]["style"],
                    },
                    "roundIndex": session["roundIndex"],
                    "baseQuestion": base_question,
                    "topic": session.get("currentTopic", ""),
                    "transcriptTail": session["transcript"][-4:],
                    "focusPoints": session.get("focusPoints", []),
                }
                result = self.ai_client.generate_question(context)
                question = str(result.get("question", "")).strip()
                if question and not self._question_seen_recently(session, question):
                    return question
            except AIClientError:
                pass

        return base_question

    def _build_hint(self, session: dict[str, Any]) -> str:
        context = {
            "role": session["role"],
            "interviewer": {
                "id": session["interviewer"]["id"],
                "style": session["interviewer"]["style"],
            },
            "currentQuestion": session["currentQuestion"],
            "transcriptTail": session["transcript"][-4:],
            "hintsUsed": session["hintsUsed"],
        }
        if self.ai_client.configured:
            try:
                result = self.ai_client.generate_hint(context)
                hint = str(result.get("hint", "")).strip()
                if hint:
                    return hint
            except AIClientError:
                pass
        return self._local_hint(session)

    # ------------------------------------------------------------------ rolls

    def _roll_drill(self, session: dict[str, Any]) -> bool:
        if session["drillDepth"] >= 3:
            return False
        probs = session["interviewer"].get("drill_probability", [0.8, 0.5, 0.25])
        idx = min(session["drillDepth"], len(probs) - 1)
        return random.random() <= float(probs[idx])

    def _roll_hint(self, session: dict[str, Any]) -> bool:
        if session["hintsUsed"] >= 3:
            return False
        prob = float(session["interviewer"].get("hint_probability", 0.5))
        return random.random() <= prob

    # ------------------------------------------------------------------ opening / report

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
            "interviewer": {
                "id": interviewer["id"],
                "style": interviewer["style"],
                "tone": interviewer["tone"],
            },
            "difficulty": difficulty,
            "analysis": analysis,
            "resumeText": resume_text,
        }
        if self.ai_client.configured:
            try:
                ai_result = self.ai_client.generate_opening(context)
                opening_line = str(ai_result.get("openingLine", "")).strip()
                first_question = str(ai_result.get("firstQuestion", "")).strip()
                if opening_line and first_question:
                    return {
                        "openingLine": opening_line,
                        "firstQuestion": first_question,
                        "focusPoints": ai_result.get("focusPoints") or analysis["followUpFocus"],
                        "topic": "opening",
                    }
            except AIClientError:
                pass

        return {
            "openingLine": interviewer.get("opening_line", "我们开始。"),
            "firstQuestion": self._local_opening_question(role, interviewer, theme_keyword),
            "focusPoints": analysis["followUpFocus"],
            "topic": "opening",
        }

    def _build_final_report(
        self,
        session: dict[str, Any],
        forced_end_reason: str | None,
    ) -> dict[str, Any]:
        total_rounds = max(1, len(session["roundScores"]))
        session_score = int(
            round(sum(item["score"] for item in session["roundScores"]) / total_rounds)
        ) if session["roundScores"] else 0

        pass_score = int(session["interviewer"].get("pass_score", 70))
        verdict = "offer" if session_score >= pass_score else "reject"
        if verdict == "offer" and session_score < pass_score + 10:
            verdict_label = "正式 Offer"
        elif verdict == "offer":
            verdict_label = "直通复试 · Offer"
        else:
            verdict_label = "未被录用"

        context = {
            "role": session["role"],
            "interviewer": {
                "id": session["interviewer"]["id"],
                "name": session["interviewer"]["name"],
                "style": session["interviewer"]["style"],
            },
            "difficulty": session["difficulty"],
            "sessionScore": session_score,
            "passScore": pass_score,
            "verdict": verdict,
            "roundScores": session["roundScores"],
            "dimensions": session["dimensions"],
            "analysis": session["analysis"],
            "forcedEndReason": forced_end_reason,
        }

        summary_payload: dict[str, Any] | None = None
        if self.ai_client.configured:
            try:
                summary_payload = self.ai_client.summarize_session(context)
            except AIClientError:
                summary_payload = None

        summary_data = self._normalize_summary(summary_payload) or self._local_final_report(
            session, session_score, verdict
        )

        offer_letter = None
        if verdict == "offer":
            offer_letter = self._build_offer_letter(session, session_score)

        return {
            "verdict": verdict,
            "verdictLabel": summary_data.get("verdictLabel") or verdict_label,
            "sessionScore": session_score,
            "passScore": pass_score,
            "summary": summary_data["summary"],
            "interviewerQuote": summary_data["interviewerQuote"],
            "highlight": summary_data["highlight"],
            "flop": summary_data["flop"],
            "tips": summary_data["tips"],
            "shareLines": summary_data["shareLines"],
            "dimensions": copy.deepcopy(session["dimensions"]),
            "roundScores": session["roundScores"],
            "forcedEndReason": forced_end_reason,
            "offerLetter": offer_letter,
        }

    def _build_offer_letter(self, session: dict[str, Any], session_score: int) -> dict[str, Any]:
        context = {
            "role": session["role"],
            "interviewer": {
                "id": session["interviewer"]["id"],
                "name": session["interviewer"]["name"],
            },
            "difficulty": session["difficulty"],
            "sessionScore": session_score,
            "dimensions": session["dimensions"],
        }
        if self.ai_client.configured:
            try:
                letter = self.ai_client.build_offer_letter(context)
                if isinstance(letter, dict) and letter.get("company") and letter.get("body"):
                    return {
                        "company": str(letter.get("company", "")),
                        "position": str(letter.get("position", session["role"]["title"])),
                        "salaryRange": str(letter.get("salaryRange", "")),
                        "startDate": str(letter.get("startDate", "两周内")),
                        "signature": str(letter.get("signature", "")),
                        "body": str(letter.get("body", "")),
                    }
            except AIClientError:
                pass
        return self._local_offer_letter(session, session_score)

    def _local_offer_letter(self, session: dict[str, Any], session_score: int) -> dict[str, Any]:
        company_pool = ["望海科技", "炽岚互动", "临界智能", "风洞 Labs", "岐光 AI"]
        band = "20K-35K·14薪" if session_score < 85 else "30K-50K·15薪"
        return {
            "company": random.choice(company_pool),
            "position": session["role"]["title"],
            "salaryRange": band,
            "startDate": "两周内",
            "signature": f"—— {session['interviewer']['name']}",
            "body": (
                f"很高兴通知你，经过本轮面试评估，我们决定向你发出 {session['role']['title']} "
                f"岗位的录用意向。综合评分 {session_score} 分，超过通过线 "
                f"{session['interviewer'].get('pass_score', 70)} 分。期待与你共事。"
            ),
        }

    def _normalize_summary(self, payload: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        required = ["summary", "interviewerQuote", "highlight", "flop", "tips", "shareLines"]
        if any(not payload.get(key) for key in required):
            return None
        return {
            "verdictLabel": str(payload.get("verdictLabel", "")) or None,
            "summary": str(payload["summary"]),
            "interviewerQuote": str(payload["interviewerQuote"]),
            "highlight": str(payload["highlight"]),
            "flop": str(payload["flop"]),
            "tips": str(payload["tips"]),
            "shareLines": [str(item) for item in payload.get("shareLines", [])][:3],
        }

    def _local_final_report(
        self,
        session: dict[str, Any],
        session_score: int,
        verdict: str,
    ) -> dict[str, Any]:
        if session["roundScores"]:
            best = max(session["roundScores"], key=lambda item: item["score"])
            worst = min(session["roundScores"], key=lambda item: item["score"])
        else:
            best = worst = {"question": "（无）", "score": 0}

        if verdict == "offer":
            summary = "整体表现稳，关键轮次给出了具体动作、依据和结果。"
        else:
            summary = "回答缺少支撑，逻辑和一致性不够稳定，没能撑住连续追问。"

        return {
            "summary": summary,
            "interviewerQuote": self._pick_quote(session["interviewer"]["id"], verdict),
            "highlight": f"第 {best['round']} 轮（{best['score']} 分）题目：{best['question']}" if "round" in best else best["question"],
            "flop": f"第 {worst['round']} 轮（{worst['score']} 分）题目：{worst['question']}" if "round" in worst else worst["question"],
            "tips": self._build_tips(session),
            "shareLines": [
                f"{session['role']['title']} 面试结果：{'Offer' if verdict == 'offer' else '未录用'}",
                f"综合分 {session_score}，通过线 {session['interviewer'].get('pass_score', 70)}",
                session["analysis"]["themeBlurb"],
            ],
        }

    # ------------------------------------------------------------------ descriptor

    def _descriptor(
        self,
        session: dict[str, Any],
        phase: str,
        question: str | None = None,
        timer_ms: int | None = None,
        event: dict[str, Any] | None = None,
        report: dict[str, Any] | None = None,
        hint: str | None = None,
    ) -> dict[str, Any]:
        session["currentPhase"] = phase
        selected = {
            "role": session["role"],
            "interviewer": public_card(session["interviewer"]),
            "difficulty": session["difficulty"],
            "themeKeyword": session["themeKeyword"],
            "resumeMode": session["resumeMode"],
        }
        metrics = {
            "roundIndex": session["roundIndex"],
            "totalRounds": session["totalRounds"],
            "drillDepth": session["drillDepth"],
            "hintsUsed": session["hintsUsed"],
            "hintsRemaining": max(0, 3 - session["hintsUsed"]),
            "roundScore": session["roundScore"],
            "sessionScore": self._current_session_score(session),
            "passScore": session["interviewer"].get("pass_score", 70),
            "stress": session["sessionStress"],
            "dimensions": copy.deepcopy(session["dimensions"]),
        }
        return {
            "sessionId": session["id"],
            "runtime": self.ai_client.runtime_status(),
            "phase": phase,
            "isFinal": phase == "final",
            "question": question,
            "hint": hint,
            "timerMs": timer_ms,
            "event": event,
            "report": report,
            "selected": selected,
            "metrics": metrics,
            "resumeText": session["resumeText"],
            "analysis": session["analysis"],
            "transcript": copy.deepcopy(session["transcript"]),
            "roundHistory": copy.deepcopy(session["roundScores"]),
        }

    def _current_session_score(self, session: dict[str, Any]) -> int:
        scores = session["roundScores"]
        if not scores:
            return int(session["roundScore"])
        cumulative = [item["score"] for item in scores]
        if session["currentPhase"] == "awaiting_answer":
            cumulative.append(session["roundScore"])
        return int(round(sum(cumulative) / len(cumulative)))

    # ------------------------------------------------------------------ analysis / feedback helpers

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

    def _local_drill_question(self, session: dict[str, Any]) -> str:
        topic = session.get("currentTopic") or (session.get("focusPoints") or ["项目经历"])[0]
        interviewer_id = session["interviewer"]["id"]
        depth = session["drillDepth"]
        bank = {
            "cold-judge": [
                f"别绕。就说“{topic}”，你亲自拍板的那个决定是什么？",
                f"再往深一点：“{topic}”里最容易失控的环节是什么？你当时怎么兜？",
                f"最后一刀：假如“{topic}”结果不达预期，你要对谁负责，怎么负责？",
            ],
            "spark-hr": [
                f"我们顺着“{topic}”再聊一层。你当时最纠结的那一步是什么？",
                f"那如果让你重来，“{topic}”里你会先改什么？为什么？",
                f"最后一个问题：你觉得“{topic}”里你真正成长的点是什么？",
            ],
            "tactical-lead": [
                f"请继续拆“{topic}”。你的判断依据是什么？",
                f"再下一层：“{topic}”的风险矩阵里，哪个象限你最担心？",
                f"终极：如果“{topic}”失败，你的复盘路径是什么？",
            ],
            "blackbox-ai": [
                f"请深化对“{topic}”的描述，补充可验证指标。",
                f"继续：“{topic}”中不可替代环节的证据是什么？",
                f"最后采样：请以反事实方式说明“{topic}”若无你会如何。",
            ],
        }
        variants = bank.get(interviewer_id, bank["cold-judge"])
        return variants[min(depth - 1, len(variants) - 1)]

    def _local_hint(self, session: dict[str, Any]) -> str:
        interviewer_id = session["interviewer"]["id"]
        used = session["hintsUsed"]
        bank = {
            "cold-judge": [
                "换个角度。我要的是你亲手做的动作，不是部门做了什么。",
                "再具体点：一个动作 + 一个依据 + 一个结果，就行。",
                "最后给你一次：用一个数字或一个对比来证明。",
            ],
            "spark-hr": [
                "别急~ 把时间拉回到当时那个场景，你先做了什么？",
                "可以先讲你当时看到了什么信号，然后怎么反应的。",
                "最后一次提示：能不能给我一个具体的人或具体的数字？",
            ],
            "tactical-lead": [
                "提示：先给结论，再给路径，最后补依据。",
                "提示：把步骤拆开，标出关键判断点。",
                "最后提示：请选择一条最能代表方法论的分支重答。",
            ],
            "blackbox-ai": [
                "提示：请补充一个可量化指标。",
                "提示：请给出时间戳、角色、动作三要素。",
                "最后提示：请输出反事实验证样本。",
            ],
        }
        variants = bank.get(interviewer_id, bank["cold-judge"])
        return variants[min(used, len(variants) - 1)]

    def _timeout_feedback(self, session: dict[str, Any]) -> str:
        table = {
            "cold-judge": "时间到了。沉默不是答案。",
            "spark-hr": "哎，时间到啦~ 咱们先过，下一题一起加油。",
            "tactical-lead": "超时。默认按放弃处理。",
            "blackbox-ai": "系统：回答超时，视作零响应。",
        }
        return table.get(session["interviewer"]["id"], "时间到了。")

    def _local_opening_question(self, role: dict[str, Any], interviewer: dict[str, Any], theme_keyword: str) -> str:
        if theme_keyword:
            return (
                f"先做个开场。你要应聘“{role['title']}”，本场关键词是“{theme_keyword}”。"
                f"请介绍你自己，并说明你会怎样把“{theme_keyword}”落进一个真实产品。"
            )
        bank = interviewer.get("question_bank", [])
        if bank:
            return bank[0]["q"]
        return role["opening_questions"][0]

    def _build_interviewer_feedback(self, interviewer_id: str, verdict: str) -> str:
        table = {
            "cold-judge": {
                "correct": "这次像样了。有动作、有判断，也有结果。",
                "partial": "方向对，但还不够硬。把依据讲得再扎实一点。",
                "wrong": "这段回答站不住。你需要更具体的职责、依据和结果。",
            },
            "spark-hr": {
                "correct": "这次就很清楚了，像一次完整复盘~",
                "partial": "整体方向没问题，但细节再落一点会更有说服力。",
                "wrong": "这段还比较虚，我没听到具体动作和结果。",
            },
            "tactical-lead": {
                "correct": "结构清楚，判断过程完整。",
                "partial": "基本思路成立，但论证链条还差一截。",
                "wrong": "缺少决策逻辑，更像参与过而不是主导过。",
            },
            "blackbox-ai": {
                "correct": "回答质量提升。信息密度与因果链达到较优水平。",
                "partial": "回答有效，但证据密度不足。",
                "wrong": "回答可信度偏低。缺少可验证动作、依据与结果样本。",
            },
        }
        return table.get(interviewer_id, table["cold-judge"])[verdict]

    def _pick_quote(self, interviewer_id: str, verdict: str) -> str:
        quotes = {
            "cold-judge": {
                "offer": "你不是最会说的人，但你有判断力。这比漂亮话值钱。",
                "reject": "简历写得比回答更像你本人。",
            },
            "spark-hr": {
                "offer": "你挺会讲故事，但更重要的是，你讲得出细节。",
                "reject": "别紧张，你只是还没有把经历讲成可信的经历。",
            },
            "tactical-lead": {
                "offer": "结构、取舍、复盘都在线，这是能落地的人。",
                "reject": "你更像参与者，而不是能独立负责的人。",
            },
            "blackbox-ai": {
                "offer": "可信度校验通过。你不仅会说，也能自证。",
                "reject": "叙述连续性不足。建议重建样本。",
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

    def _event_choice_label(self, event: dict[str, Any], choice_id: str) -> str:
        interaction = event.get("interaction") or {}
        for option in interaction.get("options", []):
            if option.get("id") == choice_id:
                return str(option.get("label", ""))
        return ""

    # ------------------------------------------------------------------ util

    def _question_seen_recently(self, session: dict[str, Any], question: str) -> bool:
        normalized = self._normalize_question(question)
        recent = [self._normalize_question(item) for item in session.get("questionHistory", [])[-3:]]
        return normalized in recent

    def _normalize_question(self, question: str) -> str:
        return "".join(question.split())

    def _require_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = payload.get("sessionId", "")
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError("会话不存在，请重新开始。")
        return session

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
