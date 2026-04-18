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
import re
import time
import uuid
from typing import Any

from .ai_client import AIClient, AIClientError
from .events import public_event_payload, resolve_event, roll_event
from .interviewers import all_interviewers, get_interviewer, public_card
from .mock_content import (
    CODE_QUESTION_BANK,
    COMMON_SKILLS,
    DIFFICULTIES,
    ROLE_LIBRARY,
    TECHNICAL_ROLES,
    build_theme_blurb,
    generate_mock_resume,
    get_difficulty,
    get_tech_questions,
    get_workplace_questions,
    resolve_role,
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
MAX_HINTS = 2


class GameEngine:
    def __init__(self) -> None:
        self.ai_client = AIClient()
        self.sessions: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------ bootstrap

    def get_bootstrap(self) -> dict[str, Any]:
        non_technical_cards = [public_card(item) for item in all_interviewers("non-technical")]
        return {
            "appName": "终面：AI面试官",
            "tagline": "AI 驱动的动态面试生存游戏",
            "roles": ROLE_LIBRARY,
            "technicalRoles": TECHNICAL_ROLES,
            "nonTechnicalInterviewers": non_technical_cards,
            "interviewTracks": [
                {
                    "id": "technical",
                    "label": "技术面",
                    "description": "沿用当前技术面试玩法，收到不同技术面试官邀请后择一进入。",
                    "enabled": True,
                },
                {
                    "id": "non-technical",
                    "label": "非技术面",
                    "description": "不用带简历，三位角色面试官会各带一份岗位邀约登场，选中谁就进入谁的面试。",
                    "enabled": True,
                },
            ],
            "difficulties": [{"id": key, **value} for key, value in DIFFICULTIES.items()],
            "runtime": self.ai_client.runtime_status(),
        }

    def generate_mock_resume(self, payload: dict[str, Any]) -> dict[str, Any]:
        interview_track = str(payload.get("interviewTrack", "") or "").strip()
        role = resolve_role(
            payload.get("roleId", ""),
            payload.get("roleTitle", ""),
            interview_track=interview_track,
        )
        difficulty = get_difficulty(payload.get("difficulty", "normal"))
        keyword = (payload.get("themeKeyword") or "").strip()
        return {
            "resumeText": generate_mock_resume(role, keyword, difficulty),
            "role": role,
            "difficulty": difficulty,
        }

    # ------------------------------------------------------------------ invitation

    def build_invitations(self, payload: dict[str, Any]) -> dict[str, Any]:
        interview_track = str(payload.get("interviewTrack", "technical")).strip() or "technical"
        difficulty = get_difficulty(payload.get("difficulty", "normal"))
        resume_text = (payload.get("resumeText") or "").strip()
        theme_keyword = (payload.get("themeKeyword") or "").strip()

        if interview_track != "technical":
            picked = list(all_interviewers("non-technical"))
            if not picked:
                raise ValueError("非技术面试官卡池为空，请检查 backend/interviewers/ 目录。")
            return {
                "role": None,
                "difficulty": difficulty,
                "analysis": self._build_nontechnical_lobby_analysis(picked),
                "interviewTrack": interview_track,
                "comingSoon": False,
                "placeholder": None,
                "invitations": [public_card(item) for item in picked[:3]],
            }

        if not resume_text:
            raise ValueError("请先填写或生成简历。")

        role = resolve_role(
            payload.get("roleId", ""),
            payload.get("roleTitle", ""),
            interview_track=interview_track,
        )
        analysis = self._analyze_resume(resume_text, role, theme_keyword)

        all_items = list(all_interviewers("technical"))
        if not all_items:
            raise ValueError("面试官池为空，请检查 backend/interviewers/ 目录。")

        count = min(3, len(all_items))
        random.shuffle(all_items)
        picked = all_items[:count]

        return {
            "role": role,
            "difficulty": difficulty,
            "analysis": analysis,
            "interviewTrack": interview_track,
            "comingSoon": False,
            "invitations": [public_card(item) for item in picked],
        }

    # ------------------------------------------------------------------ session lifecycle

    def start_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        interview_track = str(payload.get("interviewTrack", "technical")).strip() or "technical"
        difficulty = get_difficulty(payload.get("difficulty", "normal"))
        interviewer = get_interviewer(payload.get("interviewerId", ""), interview_track=interview_track)
        theme_keyword = (payload.get("themeKeyword") or "").strip()
        resume_mode = payload.get("resumeMode", "custom")
        provided_resume = (payload.get("resumeText") or "").strip()
        role = self._resolve_session_role(payload, interview_track, interviewer)

        if interview_track != "technical":
            resume_mode = "system-generated"
            resume_text = provided_resume or generate_mock_resume(role, theme_keyword, difficulty)
        elif resume_mode == "ai-generated":
            resume_text = provided_resume or generate_mock_resume(role, theme_keyword, difficulty)
        else:
            resume_text = provided_resume

        if not resume_text:
            raise ValueError("简历内容不能为空。")

        analysis = self._analyze_resume(resume_text, role, theme_keyword)
        resume_profile = (
            self._empty_resume_profile(role)
            if interview_track != "technical"
            else self._build_resume_profile(resume_text, role, theme_keyword)
        )

        min_rounds = int(interviewer.get("min_rounds", 3))
        max_rounds = int(interviewer.get("max_rounds", 5))
        difficulty_boost = int(difficulty.get("max_turns", min_rounds)) - 3
        total_rounds = random.randint(
            min_rounds,
            max(min_rounds, min(max_rounds, max_rounds + max(0, difficulty_boost))),
        )

        first = self._build_opening(
            role,
            interviewer,
            difficulty,
            theme_keyword,
            analysis,
            resume_text,
            resume_profile,
        )

        first_question = first["firstQuestion"]
        first_target_id = str(first.get("drillTargetId", "") or "")
        first_bound_project_id = str(first.get("boundProjectId", "") or "")
        question_links = {first_question: first_target_id} if first_target_id else {}

        session_id = str(uuid.uuid4())
        session: dict[str, Any] = {
            "id": session_id,
            "createdAt": time.time(),
            "interviewTrack": interview_track,
            "role": role,
            "interviewer": interviewer,
            "difficulty": difficulty,
            "themeKeyword": theme_keyword,
            "resumeMode": resume_mode,
            "resumeText": resume_text,
            "analysis": analysis,
            "resumeProfile": resume_profile,
            # 状态机
            "currentPhase": "awaiting_answer",
            "roundIndex": 1,
            "totalRounds": total_rounds,
            "drillDepth": 0,
            "hintsUsed": 0,
            "currentQuestion": first_question,
            "currentQuestionType": "normal",
            "currentQuestionKind": first.get("questionKind", "resume"),
            "currentCodeQuestion": None,
            "currentTopic": first.get("topic", ""),
            "currentHintDirections": first.get("hintDirections", []),
            "hintHistory": [],
            "currentDrillTargetId": first_target_id or None,
            "currentBoundProjectId": first_bound_project_id,
            "roundScore": ROUND_BASE_SCORE,
            "roundScores": [],
            "roundFlags": [],
            "sessionStress": int(difficulty.get("starting_stress", 20)),
            "dimensions": {key: 60 for key in DIMENSION_KEYS},
            "transcript": [
                {"speaker": "interviewer", "text": first["openingLine"]},
                {"speaker": "question", "text": first_question},
            ],
            "questionHistory": [first_question],
            "focusPoints": first.get("focusPoints") or self._resume_focus_points(resume_profile, analysis),
            "usedFocusPoints": [],
            "usedDrillTargetIds": [first_target_id] if first_target_id else [],
            "usedTechQuestions": [],
            "usedWorkplaceQuestions": [],
            "workplaceAsked": False,
            "questionLinks": question_links,
            "lastAnswerHighlights": [],
            "lastAnswerGaps": [],
            "roundStartTranscriptIndex": 1,
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
        session["lastAnswerHighlights"] = [
            str(item).strip() for item in judge.get("answerHighlights", []) if str(item).strip()
        ][:3]
        session["lastAnswerGaps"] = [
            str(item).strip() for item in judge.get("answerGaps", []) if str(item).strip()
        ][:3]
        session["transcript"].append({"speaker": "feedback", "text": judge["feedback"]})

        for key, delta in judge["dimensionDelta"].items():
            session["dimensions"][key] = self._clamp(session["dimensions"][key] + delta, 0, 100)
        session["sessionStress"] = self._clamp(
            session["sessionStress"] + int(judge.get("stressDelta", 0)), 0, 100
        )
        session["roundScore"] = self._clamp(
            session["roundScore"] + int(judge.get("scoreDelta", 0)),
            0,
            120,
        )
        session["roundFlags"].extend(judge.get("flags", []))

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
                event_note=result["note"],
            )
        return self._start_next_round_or_final(session, event_note=result["note"])

    # ------------------------------------------------------------------ state transitions

    def _advance_drill(self, session: dict[str, Any]) -> dict[str, Any]:
        session["drillDepth"] += 1
        session["hintsUsed"] = 0
        session["hintHistory"] = []
        payload = self._build_drill_question(session)
        question = payload["question"]
        session["currentQuestionType"] = "normal"
        session["currentQuestionKind"] = "resume"
        session["currentQuestion"] = question
        session["currentTopic"] = payload.get("topic", session.get("currentTopic", ""))
        session["currentHintDirections"] = []
        self._bind_question_link(session, question, payload.get("drillTarget"))
        session["questionHistory"].append(question)
        session["transcript"].append({"speaker": "question", "text": question})

        # 深挖阶段也可能触发轮内事件
        if session["pendingEvent"] is None and self._events_enabled(session):
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
        session.setdefault("hintHistory", []).append(hint)
        session["transcript"].append({"speaker": "interviewer", "text": hint})
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
        return self._start_next_round_or_final(session)

    def _start_next_round_or_final(
        self,
        session: dict[str, Any],
        event_note: str | None = None,
    ) -> dict[str, Any]:
        if session["roundIndex"] >= session["totalRounds"]:
            return self._finalize(session)

        # 轮间事件
        event = roll_event(session["interviewer"], "inter_round", session) if self._events_enabled(session) else None
        if event:
            if event.get("impact"):
                return self._attach_event(session, event, trigger="inter_round")

        session["roundIndex"] += 1
        session["drillDepth"] = 0
        session["hintsUsed"] = 0
        session["hintHistory"] = []
        session["roundScore"] = ROUND_BASE_SCORE
        session["roundFlags"] = []
        session["currentCodeQuestion"] = None
        session["currentDrillTargetId"] = None
        session["currentBoundProjectId"] = ""
        session["lastAnswerHighlights"] = []
        session["lastAnswerGaps"] = []

        # 每轮开题前 roll 一次编程题概率（第 1 轮不出编程题，留给常规开场）
        if session["roundIndex"] > 1 and self._roll_code_question(session):
            code_q = self._build_code_question(session)
            session["currentQuestionType"] = "code"
            session["currentQuestionKind"] = "code"
            session["currentCodeQuestion"] = code_q
            question_text = self._format_code_question_text(code_q)
            session["currentQuestion"] = question_text
            session["currentTopic"] = code_q.get("topic") or "编程题"
            session["currentHintDirections"] = []
            session["hintHistory"] = []
            self._bind_question_link(session, question_text, None)
            session["questionHistory"].append(question_text)
            session["transcript"].append(
                {"speaker": "question", "text": question_text}
            )
            session["roundStartTranscriptIndex"] = len(session["transcript"]) - 1
            question = question_text
        else:
            session["currentQuestionType"] = "normal"
            payload = self._build_round_question(session)
            question = payload["question"]
            session["currentQuestion"] = question
            session["currentQuestionKind"] = payload.get("questionKind", "resume")
            session["currentTopic"] = payload.get("topic", session.get("currentTopic", ""))
            session["currentHintDirections"] = [
                str(item).strip()
                for item in payload.get("hintDirections", [])
                if str(item).strip()
            ][:3]
            session["hintHistory"] = []
            self._bind_question_link(session, question, payload.get("drillTarget"))
            if session["currentQuestionKind"] == "knowledge":
                used_tech_questions = session.setdefault("usedTechQuestions", [])
                if question not in used_tech_questions:
                    used_tech_questions.append(question)
            if session["currentQuestionKind"] == "workplace":
                used_workplace_questions = session.setdefault("usedWorkplaceQuestions", [])
                if question not in used_workplace_questions:
                    used_workplace_questions.append(question)
                session["workplaceAsked"] = True
            session["questionHistory"].append(question)
            session["transcript"].append(
                {"speaker": "question", "text": question}
            )
            session["roundStartTranscriptIndex"] = len(session["transcript"]) - 1

        # 轮内事件
        intra = roll_event(session["interviewer"], "intra_round", session) if self._events_enabled(session) else None
        if intra:
            if intra.get("impact"):
                return self._attach_event(session, intra, trigger="intra_round")

        return self._descriptor(
            session,
            phase="awaiting_answer",
            question=question,
            timer_ms=int(session["interviewer"].get("answer_time_ms", 90_000)),
            event_note=event_note,
        )

    def _attach_event(
        self,
        session: dict[str, Any],
        event: dict[str, Any],
        trigger: str,
    ) -> dict[str, Any]:
        session["pendingEvent"] = event
        session["pendingEventTrigger"] = trigger
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
        if session.get("currentQuestionType") == "code" and session.get("currentCodeQuestion"):
            return self._judge_code_answer(session, answer)

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
            "resumeProfile": session.get("resumeProfile", {}),
            "boundProject": self._bound_project(session),
            "roundIndex": session["roundIndex"],
            "drillDepth": session["drillDepth"],
            "currentQuestion": session["currentQuestion"],
            "currentQuestionType": session.get("currentQuestionType", "normal"),
            "currentQuestionKind": session.get("currentQuestionKind", "resume"),
            "currentTopic": session.get("currentTopic", ""),
            "transcriptTail": session["transcript"][-8:],
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
            "answerHighlights": [
                str(item).strip() for item in payload.get("answerHighlights", []) if str(item).strip()
            ][:3],
            "answerGaps": [
                str(item).strip() for item in payload.get("answerGaps", []) if str(item).strip()
            ][:3],
            "dimensionDelta": {
                key: int(dimension_delta.get(key, 0)) for key in DIMENSION_KEYS
            },
        }

    def _judge_code_answer(self, session: dict[str, Any], answer: str) -> dict[str, Any]:
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
            "resumeProfile": session.get("resumeProfile", {}),
            "roundIndex": session["roundIndex"],
            "codeQuestion": session["currentCodeQuestion"],
            "transcriptTail": session["transcript"][-8:],
        }
        if self.ai_client.configured:
            try:
                result = self.ai_client.judge_code_answer(context, answer)
                normalized = self._normalize_judge(result)
                if normalized:
                    return normalized
            except AIClientError:
                pass
        return self._local_code_judge_answer(session, answer)

    def _local_judge_answer(self, session: dict[str, Any], answer: str) -> dict[str, Any]:
        role_keywords = session["role"]["keywords"]
        theme_keyword = session["themeKeyword"]
        length = len(answer)

        dimension_delta = {key: 0 for key in DIMENSION_KEYS}
        score_delta = 0
        flags: list[str] = []
        answer_highlights = self._extract_answer_highlights(answer, session)
        answer_gaps = self._build_answer_gaps(session, answer, answer_highlights)
        conflict = self._detect_resume_conflict(session, answer)

        if session.get("currentQuestionKind") == "workplace":
            if length < 18:
                score_delta -= 10
                dimension_delta["logic"] -= 5
                dimension_delta["composure"] -= 3
                flags.append("回答过短")
            elif length < 50:
                score_delta += 1
                flags.append("细节不足")
            else:
                score_delta += 5
                dimension_delta["logic"] += 3
                dimension_delta["composure"] += 2

            if any(token in answer for token in ["我会", "可以", "先", "再", "优先", "沟通", "协调", "安排"]):
                score_delta += 5
                dimension_delta["adaptability"] += 3
                dimension_delta["logic"] += 1
            if any(token in answer for token in ["时间", "到岗", "边界", "优先级", "冲突", "安排"]):
                score_delta += 4
                dimension_delta["consistency"] += 2
            if any(token in answer for token in ["不知道", "看情况", "随便", "都行", "不确定"]):
                score_delta -= 10
                dimension_delta["consistency"] -= 5
                dimension_delta["composure"] -= 3
                flags.append("态度不明确")
            if any(token in answer for token in ["大概", "差不多", "应该"]):
                score_delta -= 4
                dimension_delta["consistency"] -= 2
                flags.append("表达模糊")

            if score_delta >= 10 and len(answer_gaps) <= 1 and "态度不明确" not in flags:
                verdict = "correct"
            elif score_delta >= 0:
                verdict = "partial"
            else:
                verdict = "wrong"

            feedback = self._build_local_answer_feedback(
                session,
                verdict,
                answer_highlights,
                answer_gaps,
                "",
            )
            stress_delta = 4 if verdict == "wrong" else (-2 if verdict == "correct" else 0)
            return {
                "verdict": verdict,
                "feedback": feedback,
                "scoreDelta": score_delta,
                "stressDelta": stress_delta,
                "flags": flags[:3],
                "answerHighlights": answer_highlights[:3],
                "answerGaps": answer_gaps[:3],
                "dimensionDelta": dimension_delta,
            }

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
        if answer_highlights:
            score_delta += min(4, len(answer_highlights) * 2)
            dimension_delta["depth"] += min(4, len(answer_highlights))
        if any(token in answer for token in ["不知道", "忘了", "不太清楚", "没做过"]):
            score_delta -= 12
            dimension_delta["consistency"] -= 6
            dimension_delta["composure"] -= 4
            flags.append("暴露不确定性")
        if any(token in answer for token in ["大概", "差不多", "应该"]):
            score_delta -= 4
            dimension_delta["consistency"] -= 3
            flags.append("表达模糊")
        if conflict:
            score_delta -= 16
            dimension_delta["consistency"] -= 8
            dimension_delta["roleFit"] -= 4
            flags.append("简历回答不一致")
            answer_gaps = [conflict] + [item for item in answer_gaps if item != conflict]

        if conflict:
            verdict = "wrong"
        elif score_delta >= 10 and "暴露不确定性" not in flags and len(answer_gaps) <= 1:
            verdict = "correct"
        elif score_delta >= 0:
            verdict = "partial"
        else:
            verdict = "wrong"

        feedback = self._build_local_answer_feedback(
            session,
            verdict,
            answer_highlights,
            answer_gaps,
            conflict,
        )
        stress_delta = 5 if verdict == "wrong" else (-3 if verdict == "correct" else 0)

        return {
            "verdict": verdict,
            "feedback": feedback,
            "scoreDelta": score_delta,
            "stressDelta": stress_delta,
            "flags": flags[:3],
            "answerHighlights": answer_highlights[:3],
            "answerGaps": answer_gaps[:3],
            "dimensionDelta": dimension_delta,
        }

    def _local_code_judge_answer(self, session: dict[str, Any], answer: str) -> dict[str, Any]:
        code = answer.strip()
        question = session.get("currentCodeQuestion") or {}
        signature = str(question.get("signature", ""))
        title = str(question.get("title", "编程题"))
        topic = str(question.get("topic", ""))

        dimension_delta = {key: 0 for key in DIMENSION_KEYS}
        flags: list[str] = []
        score_delta = 0

        if len(code) < 20:
            flags.append("代码过短")
            score_delta -= 12
            dimension_delta["logic"] -= 5
            dimension_delta["depth"] -= 6
        else:
            score_delta += 2
            dimension_delta["composure"] += 1

        if "def " in code or "class " in code:
            score_delta += 5
            dimension_delta["logic"] += 3
            dimension_delta["roleFit"] += 2
        else:
            flags.append("缺少函数骨架")
            score_delta -= 6
            dimension_delta["logic"] -= 3

        if "return" in code:
            score_delta += 4
            dimension_delta["consistency"] += 2
        else:
            flags.append("未见返回结果")
            score_delta -= 4

        if "O(" in code or "复杂度" in code:
            score_delta += 3
            dimension_delta["depth"] += 2

        if "#" in code or '"""' in code or "'''" in code:
            score_delta += 1
            dimension_delta["adaptability"] += 1

        normalized = code.lower()
        signature_lower = signature.lower()
        if "class " in signature_lower and "class " in normalized:
            score_delta += 3
            dimension_delta["depth"] += 2
        if "lru" in title.lower() or "缓存" in title:
            if all(token in normalized for token in ["class", "get", "put"]):
                score_delta += 5
            else:
                flags.append("LRU 关键接口不完整")
                score_delta -= 5
        if "两数之和" in title or "two_sum" in signature_lower:
            if "dict" in normalized or "{}" in normalized or "hash" in normalized:
                score_delta += 4
                dimension_delta["depth"] += 2
        if "链表" in title or "reverse_list" in signature_lower:
            if "next" in normalized and ("prev" in normalized or "pre" in normalized):
                score_delta += 4
                dimension_delta["depth"] += 2
        if "限流" in title or "tokenbucket" in normalized:
            if "time" in normalized or "timestamp" in normalized or "last_refill" in normalized:
                score_delta += 4
                dimension_delta["depth"] += 2
        if "最长无重复字符子串" in title:
            if "left" in normalized and ("set(" in normalized or "dict" in normalized):
                score_delta += 4
                dimension_delta["depth"] += 2
        if "有效的括号" in title:
            if "stack" in normalized or ".append(" in normalized:
                score_delta += 3
                dimension_delta["logic"] += 1

        if topic and topic in code:
            score_delta += 1

        if score_delta >= 10:
            verdict = "correct"
        elif score_delta >= 0:
            verdict = "partial"
        else:
            verdict = "wrong"

        feedback_bank = {
            "gentle-senior": {
                "correct": "嗯，这版思路是顺的，关键结构也立住了。",
                "partial": "大方向没跑偏，不过还有几处我想听你再补严一点。",
                "wrong": "这版还不太稳，骨架有了，但关键逻辑我暂时没法放心。",
            },
            "steady-engineer": {
                "correct": "可以，这份代码至少能让我看清你的判断路径。",
                "partial": "思路看得出来，但边界和完整性还差一口气。",
                "wrong": "这份实现还支撑不住题目要求，关键路径不够完整。",
            },
            "strict-architect": {
                "correct": "能看，结构和关键操作基本对上了。",
                "partial": "思路有，但你这份代码还没严谨到能上线讨论。",
                "wrong": "不行，这份代码里缺口太明显了。",
            },
        }
        feedback = feedback_bank.get(session["interviewer"]["id"], feedback_bank["steady-engineer"])[verdict]
        stress_delta = 5 if verdict == "wrong" else (-2 if verdict == "correct" else 1)

        return {
            "verdict": verdict,
            "feedback": feedback,
            "scoreDelta": score_delta,
            "stressDelta": stress_delta,
            "flags": flags[:3],
            "answerHighlights": [],
            "answerGaps": [],
            "dimensionDelta": dimension_delta,
        }

    def _build_code_question(self, session: dict[str, Any]) -> dict[str, Any]:
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
            "resumeProfile": session.get("resumeProfile", {}),
            "roundIndex": session["roundIndex"],
            "resumeText": session["resumeText"],
            "focusPoints": session.get("focusPoints", []),
        }
        if self.ai_client.configured:
            try:
                payload = self.ai_client.generate_code_question(context)
                normalized = self._normalize_code_question(payload)
                if normalized:
                    return normalized
            except AIClientError:
                pass

        bank = list(CODE_QUESTION_BANK)
        role_id = session["role"]["id"]
        preferred_topic = {
            "frontend-engineer": ["数组", "栈", "二分"],
            "backend-engineer": ["哈希", "限流", "缓存"],
            "algorithm-engineer": ["链表", "滑动窗口", "排序"],
            "fullstack-engineer": ["数组", "缓存", "限流"],
            "ai-application-engineer": ["缓存", "限流", "哈希"],
            "client-engineer": ["数组", "链表", "二分"],
            "test-engineer": ["数组", "二分", "栈"],
        }.get(role_id, [])

        weighted = [
            item for item in bank if any(topic in item.get("topic", "") for topic in preferred_topic)
        ] or bank
        picked = copy.deepcopy(random.choice(weighted))
        picked["difficulty"] = str(picked.get("difficulty", "medium"))
        return picked

    def _normalize_code_question(self, payload: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        title = str(payload.get("title", "")).strip()
        description = str(payload.get("description", "")).strip()
        signature = str(payload.get("signature", "")).strip()
        difficulty = str(payload.get("difficulty", "medium")).strip().lower() or "medium"
        examples_raw = payload.get("examples")
        if not title or not description or not signature or difficulty not in {"easy", "medium", "hard"}:
            return None
        if not isinstance(examples_raw, list) or not examples_raw:
            return None

        examples = []
        for item in examples_raw[:3]:
            if not isinstance(item, dict):
                continue
            input_text = str(item.get("input", "")).strip()
            output_text = str(item.get("output", "")).strip()
            if input_text and output_text:
                examples.append({"input": input_text, "output": output_text})
        if not examples:
            return None

        return {
            "title": title,
            "description": description,
            "signature": signature,
            "examples": examples,
            "difficulty": difficulty,
            "topic": str(payload.get("topic", title)).strip() or title,
        }

    def _format_code_question_text(self, code_question: dict[str, Any]) -> str:
        difficulty = {"easy": "简单", "medium": "中等", "hard": "偏难"}.get(
            str(code_question.get("difficulty", "medium")),
            "中等",
        )
        return f"来，我们做一道{difficulty}编程题：{code_question.get('title', '编程题')}。你边写边讲思路。"

    def _build_drill_question(self, session: dict[str, Any]) -> dict[str, Any]:
        current_target = self._current_drill_target(session)
        fallback_target = self._pick_round_drill_target(session)
        bound_project = self._bound_project(session, current_target)
        context = {
            "mode": "drill",
            "role": session["role"],
            "interviewer": {
                "id": session["interviewer"]["id"],
                "style": session["interviewer"]["style"],
                "tone": session["interviewer"]["tone"],
            },
            "drillDepth": session["drillDepth"],
            "currentQuestion": session["currentQuestion"],
            "currentQuestionType": session.get("currentQuestionType", "normal"),
            "codeQuestion": session.get("currentCodeQuestion"),
            "resumeProfile": session.get("resumeProfile", {}),
            "boundProject": bound_project,
            "currentDrillTarget": current_target,
            "fallbackDrillTarget": fallback_target,
            "drillStack": self._build_drill_stack(session),
            "answerHighlights": session.get("lastAnswerHighlights", []),
            "answerGaps": session.get("lastAnswerGaps", []),
            "latestCandidateAnswer": self._latest_candidate_text(session),
            "transcriptTail": session["transcript"][-8:],
            "focusPoints": session.get("focusPoints", []),
        }
        if self.ai_client.configured:
            for _ in range(2):
                try:
                    result = self.ai_client.generate_question(context)
                    question = str(result.get("question", "")).strip()
                    anchor = str(result.get("anchor", "")).strip()
                    if (
                        question
                        and anchor
                        and self._anchor_matches_recent_answer(session, anchor)
                        and not self._question_seen_recently(session, question)
                    ):
                        linked_target = current_target
                        if not linked_target and fallback_target:
                            linked_target = fallback_target
                        return {
                            "question": question,
                            "drillTarget": linked_target,
                            "topic": (linked_target or {}).get("topic") or anchor,
                        }
                except AIClientError:
                    break
        return self._local_drill_question(session)

    def _build_round_question(self, session: dict[str, Any]) -> dict[str, Any]:
        drill_target = self._pick_round_drill_target(session)
        workplace_question = None if session.get("interviewTrack") == "non-technical" else self._pick_workplace_question(session)
        tech_question = self._pick_tech_question(session)
        workplace_probability = 0.45 if session.get("interviewTrack") == "non-technical" else 0.15
        use_workplace = bool(workplace_question) and session["roundIndex"] > 1 and random.random() < workplace_probability
        resume_has_tech_anchor = self._resume_has_tech_anchor(session, drill_target)
        use_knowledge = bool(tech_question) and (not drill_target or resume_has_tech_anchor or random.random() < 0.5)

        if use_workplace and workplace_question:
            topic = workplace_question.get("topic") or "职场问题"
            base_question = workplace_question["q"]
            question_kind = "workplace"
            hint_directions = [
                str(item).strip()
                for item in workplace_question.get("hint_directions", [])
                if str(item).strip()
            ][:3]
            drill_target = None
        elif use_knowledge and tech_question:
            topic = tech_question.get("topic") or "技术原理"
            base_question = tech_question["q"]
            question_kind = "knowledge"
            hint_directions = [
                str(item).strip()
                for item in tech_question.get("hint_directions", [])
                if str(item).strip()
            ][:3]
            drill_target = None
        elif drill_target:
            topic = drill_target.get("topic") or drill_target.get("anchor") or "简历追问"
            base_question = drill_target["question"]
            question_kind = "resume"
            hint_directions = []
        else:
            bank = session["interviewer"].get("question_bank", [])
            asked = set(session.get("questionHistory", []))
            candidates = [item for item in bank if item.get("q") not in asked]
            if not candidates:
                candidates = bank
            if candidates:
                choice = random.choice(candidates)
                topic = choice.get("topic", "")
                base_question = choice["q"]
                hint_directions = [
                    str(item).strip()
                    for item in choice.get("hint_directions", [])
                    if str(item).strip()
                ][:3]
                question_kind = "workplace" if session.get("interviewTrack") == "non-technical" else "knowledge"
                drill_target = None
            else:
                topic = "开场"
                base_question = session["role"]["opening_questions"][0]
                question_kind = "resume"
                hint_directions = []

        if self.ai_client.configured:
            try:
                context = {
                    "mode": "round_open",
                    "questionKind": question_kind,
                    "role": session["role"],
                    "interviewer": {
                        "id": session["interviewer"]["id"],
                        "style": session["interviewer"]["style"],
                        "tone": session["interviewer"]["tone"],
                    },
                    "roundIndex": session["roundIndex"],
                    "baseQuestion": base_question,
                    "topic": topic,
                    "hintDirections": hint_directions,
                    "workplaceQuestionCandidate": workplace_question if use_workplace else None,
                    "techQuestionCandidate": tech_question if use_knowledge else None,
                    "resumeProfile": session.get("resumeProfile", {}),
                    "availableDrillTargets": self._available_drill_targets(session)[:5],
                    "recentTranscript": session["transcript"][-8:],
                    "transcriptTail": session["transcript"][-8:],
                    "focusPoints": session.get("focusPoints", []),
                }
                result = self.ai_client.generate_question(context)
                question = str(result.get("question", "")).strip()
                if (
                    question
                    and not self._question_seen_recently(session, question)
                    and self._question_mentions_resume_fact(
                        question,
                        session.get("resumeProfile", {}),
                        self._bound_project(session, drill_target),
                        drill_target,
                        question_kind=question_kind,
                    )
                ):
                    return {
                        "question": question,
                        "drillTarget": drill_target,
                        "topic": topic,
                        "questionKind": question_kind,
                        "hintDirections": hint_directions,
                    }
            except AIClientError:
                pass

        return {
            "question": base_question,
            "drillTarget": drill_target,
            "topic": topic,
            "questionKind": question_kind,
            "hintDirections": hint_directions,
        }

    def _pick_tech_question(self, session: dict[str, Any]) -> dict[str, Any] | None:
        role_bank = get_tech_questions(session["role"]["id"])
        interviewer_bank = [
            dict(item)
            for item in session["interviewer"].get("question_bank", [])
            if isinstance(item, dict) and item.get("q")
        ]
        bank = role_bank + interviewer_bank
        if not bank:
            return None

        asked = set(session.get("questionHistory", [])) | set(session.get("usedTechQuestions", []))
        candidates = [item for item in bank if str(item.get("q", "")).strip() and item.get("q") not in asked]
        if not candidates:
            candidates = bank
        if not candidates:
            return None

        anchors = self._resume_tech_anchors(session, session.get("currentTopic", ""))
        scored: list[tuple[int, int, dict[str, Any]]] = []
        for index, item in enumerate(candidates):
            related = [
                self._normalize_free_text(token)
                for token in item.get("related_skills", [])
                if str(token).strip()
            ]
            topic = self._normalize_free_text(item.get("topic", ""))
            question = self._normalize_free_text(item.get("q", ""))
            score = 0
            for anchor in anchors:
                if not anchor:
                    continue
                if anchor in related:
                    score += 4
                if anchor and (anchor in topic or anchor in question):
                    score += 2
            scored.append((score, -index, item))
        scored.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
        return copy.deepcopy(scored[0][2]) if scored else None

    def _pick_workplace_question(self, session: dict[str, Any]) -> dict[str, Any] | None:
        if session.get("workplaceAsked"):
            return None
        bank = get_workplace_questions()
        asked = set(session.get("questionHistory", [])) | set(session.get("usedWorkplaceQuestions", []))
        candidates = [item for item in bank if str(item.get("q", "")).strip() and item.get("q") not in asked]
        if not candidates:
            return None
        return copy.deepcopy(random.choice(candidates))

    def _build_hint(self, session: dict[str, Any]) -> str:
        context = {
            "role": session["role"],
            "interviewer": {
                "id": session["interviewer"]["id"],
                "style": session["interviewer"]["style"],
                "tone": session["interviewer"]["tone"],
            },
            "currentQuestion": session["currentQuestion"],
            "currentQuestionKind": session.get("currentQuestionKind", "resume"),
            "currentTopic": session.get("currentTopic", ""),
            "hintDirections": session.get("currentHintDirections", []),
            "priorHints": session.get("hintHistory", []),
            "transcriptTail": session["transcript"][-4:],
            "hintsUsed": session["hintsUsed"],
            "latestCandidateAnswer": self._latest_candidate_text(session),
            "answerGaps": session.get("lastAnswerGaps", []),
        }
        if self.ai_client.configured:
            try:
                result = self.ai_client.generate_hint(context)
                hint = str(result.get("hint", "")).strip()
                if hint and not self._hint_seen(session, hint):
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
        prob = float(probs[idx])
        if session.get("currentQuestionType") == "code":
            prob *= 0.5
        return random.random() <= prob

    def _roll_hint(self, session: dict[str, Any]) -> bool:
        if session.get("currentQuestionType") == "code":
            return False
        if session["hintsUsed"] >= MAX_HINTS:
            return False
        prob = float(session["interviewer"].get("hint_probability", 0.5))
        return random.random() <= prob

    def _roll_code_question(self, session: dict[str, Any]) -> bool:
        prob = float(session["interviewer"].get("code_question_probability", 0))
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
        resume_profile: dict[str, Any],
    ) -> dict[str, Any]:
        opening_target = self._opening_drill_target(resume_profile)
        focus_points = self._resume_focus_points(resume_profile, analysis)
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
            "resumeProfile": resume_profile,
            "openingDrillTarget": opening_target,
        }
        if self.ai_client.configured:
            try:
                ai_result = self.ai_client.generate_opening(context)
                opening_line = str(ai_result.get("openingLine", "")).strip()
                first_question = str(ai_result.get("firstQuestion", "")).strip()
                if (
                    opening_line
                    and first_question
                    and self._question_mentions_resume_fact(
                        first_question,
                        resume_profile,
                        self._resume_project_by_id(
                            resume_profile,
                            str((opening_target or {}).get("sourceProjectId", "")),
                        ),
                        opening_target,
                    )
                ):
                    return {
                        "openingLine": opening_line,
                        "firstQuestion": first_question,
                        "focusPoints": ai_result.get("focusPoints") or focus_points,
                        "topic": (opening_target or {}).get("topic") or "opening",
                        "drillTargetId": str((opening_target or {}).get("id", "") or ""),
                        "boundProjectId": str((opening_target or {}).get("sourceProjectId", "") or ""),
                    }
            except AIClientError:
                pass

        if opening_target:
            opening_kind = "resume"
        elif session_track := interviewer.get("interview_tracks", []):
            opening_kind = "workplace" if "non-technical" in session_track else "knowledge"
        else:
            opening_kind = "knowledge"
        opening_hint_directions = []
        if not opening_target:
            opening_bank = interviewer.get("question_bank", [])
            if opening_bank:
                opening_hint_directions = [
                    str(item).strip()
                    for item in opening_bank[0].get("hint_directions", [])
                    if str(item).strip()
                ][:3]

        return {
            "openingLine": interviewer.get("opening_line", "我们开始。"),
            "firstQuestion": self._local_opening_question(role, interviewer, theme_keyword, resume_profile),
            "focusPoints": focus_points,
            "questionKind": opening_kind,
            "hintDirections": opening_hint_directions,
            "topic": (opening_target or {}).get("topic") or "opening",
            "drillTargetId": str((opening_target or {}).get("id", "") or ""),
            "boundProjectId": str((opening_target or {}).get("sourceProjectId", "") or ""),
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

    def _resolve_session_role(
        self,
        payload: dict[str, Any],
        interview_track: str,
        interviewer: dict[str, Any],
    ) -> dict[str, Any]:
        if interview_track == "non-technical" and interviewer.get("featured_role"):
            return copy.deepcopy(interviewer["featured_role"])
        return resolve_role(
            payload.get("roleId", ""),
            payload.get("roleTitle", ""),
            interview_track=interview_track,
        )

    def _events_enabled(self, session: dict[str, Any]) -> bool:
        return session.get("interviewTrack") != "non-technical"

    def _empty_resume_profile(self, role: dict[str, Any]) -> dict[str, Any]:
        return {
            "headline": f"{role['title']} 候选人，擅长 {', '.join(role.get('keywords', [])[:3])}",
            "skills": {
                "proficient": list(role.get("keywords", [])[:4]),
                "familiar": list(role.get("keywords", [])[4:6]),
                "claimedButUnverified": [],
            },
            "projects": [],
            "metrics": [],
            "drillTargets": [],
            "inconsistencies": [],
        }

    def _build_nontechnical_lobby_analysis(self, interviewers: list[dict[str, Any]]) -> dict[str, Any]:
        names = [str(item.get("name", "")).strip() for item in interviewers[:3] if str(item.get("name", "")).strip()]
        openings = [
            str((item.get("featured_role") or {}).get("title", "")).strip()
            for item in interviewers[:3]
            if str((item.get("featured_role") or {}).get("title", "")).strip()
        ]
        summary = "非技术面改成了角色卡选秀场。每位面试官都会带着符合人设的岗位进场，你挑中哪一张，就进哪一场戏。"
        if names and openings:
            summary = f"今晚到场的是 {', '.join(names)}，他们分别带来了 {', '.join(openings)} 这些岗位。"
        return {
            "themeBlurb": summary,
            "strengths": [
                "不用准备简历，直接按兴趣挑岗位开聊。",
                "同一套面试流程，但问题会明显带人设语气和戏剧感。",
                "每张卡都把面试官身份和招聘岗位绑在一起，选人也等于选岗。",
            ],
            "riskPoints": [
                "非技术面更看临场表达、判断依据和角色匹配，不容易靠背模板过关。",
                "同一位面试官会持续按自己的人设追问，回答太空容易被拆穿。",
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
        event_note: str | None = None,
    ) -> dict[str, Any]:
        session["currentPhase"] = phase
        selected = {
            "role": session["role"],
            "interviewer": public_card(session["interviewer"]),
            "difficulty": session["difficulty"],
            "themeKeyword": session["themeKeyword"],
            "resumeMode": session["resumeMode"],
            "interviewTrack": session.get("interviewTrack", "technical"),
        }
        metrics = {
            "roundIndex": session["roundIndex"],
            "totalRounds": session["totalRounds"],
            "drillDepth": session["drillDepth"],
            "hintsUsed": session["hintsUsed"],
            "hintsRemaining": max(0, MAX_HINTS - session["hintsUsed"]),
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
            "questionType": session.get("currentQuestionType", "normal"),
            "codeQuestion": self._public_code_question(session),
            "hint": hint,
            "eventNote": event_note,
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

    def _build_resume_profile(
        self,
        resume_text: str,
        role: dict[str, Any],
        theme_keyword: str,
    ) -> dict[str, Any]:
        fallback = self._fallback_resume_profile(resume_text, role, theme_keyword)
        if self.ai_client.configured:
            try:
                payload = self.ai_client.parse_resume(
                    {
                        "resumeText": resume_text,
                        "role": role,
                        "themeKeyword": theme_keyword,
                    }
                )
                normalized = self._normalize_resume_profile(payload, fallback)
                if normalized.get("drillTargets"):
                    return normalized
            except AIClientError:
                pass
        return fallback

    def _normalize_resume_profile(
        self,
        payload: dict[str, Any] | None,
        fallback: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return fallback

        projects: list[dict[str, Any]] = []
        for index, item in enumerate(payload.get("projects") or [], start=1):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            project_id = str(item.get("id", "")).strip() or f"p{index}"
            stack = self._dedupe(
                [str(token).strip() for token in item.get("stack", []) if str(token).strip()]
            )[:6]
            role_text = str(item.get("role", "")).strip()
            highlights = self._dedupe(
                [str(token).strip() for token in item.get("highlights", []) if str(token).strip()]
            )[:3]
            metrics = self._dedupe(
                [str(token).strip() for token in item.get("metrics", []) if str(token).strip()]
                + [metric for highlight in highlights for metric in self._extract_resume_metrics(highlight)]
            )[:4]
            suspects = self._dedupe(
                [str(token).strip() for token in item.get("suspects", []) if str(token).strip()]
            )[:3]
            projects.append(
                {
                    "id": project_id,
                    "name": name,
                    "stack": stack,
                    "role": role_text,
                    "highlights": highlights,
                    "metrics": metrics,
                    "suspects": suspects,
                }
            )
        if not projects:
            projects = copy.deepcopy(fallback["projects"])

        fallback_skills = fallback.get("skills", {})
        skills_raw = payload.get("skills") or {}
        skills = {
            key: self._dedupe(
                [str(item).strip() for item in skills_raw.get(key, []) if str(item).strip()]
                + list(fallback_skills.get(key, []))
            )[:8]
            for key in ("proficient", "familiar", "claimedButUnverified")
        }

        metrics = self._dedupe(
            [str(item).strip() for item in payload.get("metrics", []) if str(item).strip()]
            + [metric for project in projects for metric in project.get("metrics", [])]
            + list(fallback.get("metrics", []))
        )[:8]
        inconsistencies = self._dedupe(
            [str(item).strip() for item in payload.get("inconsistencies", []) if str(item).strip()]
            + list(fallback.get("inconsistencies", []))
        )[:5]

        project_ids = {project["id"] for project in projects}
        skill_tokens = {
            self._normalize_free_text(token)
            for key in ("proficient", "familiar", "claimedButUnverified")
            for token in skills.get(key, [])
        }
        drill_targets: list[dict[str, Any]] = []
        for index, item in enumerate(payload.get("drillTargets") or [], start=1):
            if not isinstance(item, dict):
                continue
            question = str(item.get("question", "")).strip()
            anchor = str(item.get("anchor", "")).strip()
            if not question or not anchor:
                continue
            project_id = str(item.get("sourceProjectId", "")).strip()
            if project_id and project_id not in project_ids:
                project_id = ""
            if not project_id and self._normalize_free_text(anchor) not in skill_tokens:
                continue
            drill_targets.append(
                {
                    "id": str(item.get("id", "")).strip() or f"t{index}",
                    "topic": str(item.get("topic", "")).strip() or anchor,
                    "question": question,
                    "anchor": anchor,
                    "sourceProjectId": project_id,
                }
            )
        if len(drill_targets) < 3:
            seen_questions = {item["question"] for item in drill_targets}
            for item in fallback.get("drillTargets", []):
                if item["question"] in seen_questions:
                    continue
                drill_targets.append(copy.deepcopy(item))
                seen_questions.add(item["question"])
                if len(drill_targets) >= 8:
                    break

        headline = str(payload.get("headline", "")).strip() or str(fallback.get("headline", ""))
        if not headline:
            headline = fallback["headline"]

        return {
            "headline": headline,
            "projects": projects,
            "skills": skills,
            "metrics": metrics,
            "drillTargets": drill_targets[:8],
            "inconsistencies": inconsistencies,
        }

    def _fallback_resume_profile(
        self,
        resume_text: str,
        role: dict[str, Any],
        theme_keyword: str,
    ) -> dict[str, Any]:
        lines = self._resume_candidate_lines(resume_text)
        projects: list[dict[str, Any]] = []
        for index, line in enumerate(lines[:3], start=1):
            name_match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9]+(?:项目|系统|平台|模块|中心|重构|优化))", line)
            quoted = re.search(r"[“\"《【](.{2,20}?)[”\"》】]", line)
            if quoted:
                name = quoted.group(1).strip()
            elif name_match:
                name = name_match.group(1).strip()
            else:
                name = re.split(r"[，。；：:（）()\s]", line, maxsplit=1)[0].strip()[:16] or f"项目{index}"
            name = re.sub(r"^(负责|主导|参与|独立)", "", name).strip() or f"项目{index}"
            role_match = re.search(r"(负责[^，。；]{2,24}|主导[^，。；]{2,24}|参与[^，。；]{2,24}|独立[^，。；]{2,24})", line)
            role_text = role_match.group(1).strip() if role_match else "核心参与"
            stack = self._extract_stack_tokens(line, role)[:5]
            metrics = self._extract_resume_metrics(line)[:3]
            suspects = []
            if not metrics:
                suspects.append("结果指标没写清楚")
            if not role_match:
                suspects.append("个人职责边界不够清楚")
            if not stack:
                suspects.append("技术方案写得偏泛")
            projects.append(
                {
                    "id": f"p{index}",
                    "name": name,
                    "stack": stack,
                    "role": role_text,
                    "highlights": [line],
                    "metrics": metrics,
                    "suspects": suspects[:3],
                }
            )

        proficient = self._extract_stack_tokens(resume_text, role)[:8]
        familiar = [item for item in role.get("keywords", []) if item in resume_text and item not in proficient][:5]
        claimed = []
        for token in self._dedupe(role.get("keywords", []) + COMMON_SKILLS):
            pattern = rf"(?:熟悉|了解|接触|使用).{{0,6}}{re.escape(token)}|{re.escape(token)}.{{0,6}}(?:熟悉|了解|接触)"
            if re.search(pattern, resume_text, re.IGNORECASE) and token not in proficient and token not in familiar:
                claimed.append(token)
        metrics = self._extract_resume_metrics(resume_text)[:8]
        inconsistencies = self._infer_resume_inconsistencies(resume_text, projects, proficient, theme_keyword)

        drill_targets: list[dict[str, Any]] = []

        def add_target(topic: str, question: str, anchor: str, source_project_id: str = "") -> None:
            if not question or not anchor or len(drill_targets) >= 8:
                return
            drill_targets.append(
                {
                    "id": f"t{len(drill_targets) + 1}",
                    "topic": topic,
                    "question": question,
                    "anchor": anchor,
                    "sourceProjectId": source_project_id,
                }
            )

        for project in projects:
            if project["metrics"]:
                metric = project["metrics"][0]
                add_target(
                    project["name"],
                    f"你在 {project['name']} 里写到 {metric}，这个结果是怎么一步步做出来的？",
                    metric,
                    project["id"],
                )
            if project["stack"]:
                stack_name = project["stack"][0]
                add_target(
                    stack_name,
                    f"{project['name']} 里你为什么选 {stack_name}，当时的核心取舍是什么？",
                    stack_name,
                    project["id"],
                )
            if project["suspects"]:
                suspect = project["suspects"][0]
                add_target(
                    project["name"],
                    f"{project['name']} 这段里 {suspect}，你现在把当时的真实做法讲具体一点。",
                    project["name"],
                    project["id"],
                )

        for skill in proficient + claimed:
            if len(drill_targets) >= 6:
                break
            add_target(
                skill,
                f"你简历里提到 {skill}，具体是在什么项目里真正用它解决了什么问题？",
                skill,
            )

        while len(drill_targets) < 3:
            fallback_anchor = role["keywords"][min(len(drill_targets), len(role["keywords"]) - 1)]
            add_target(
                fallback_anchor,
                f"你简历里和 {fallback_anchor} 相关的经历具体落在了哪个项目、什么动作和什么结果上？",
                fallback_anchor,
            )

        skills = {
            "proficient": proficient,
            "familiar": familiar,
            "claimedButUnverified": claimed[:5],
        }
        return {
            "headline": self._build_resume_headline(resume_text, role, skills, projects),
            "projects": projects,
            "skills": skills,
            "metrics": metrics,
            "drillTargets": drill_targets[:8],
            "inconsistencies": inconsistencies,
        }

    def _resume_candidate_lines(self, resume_text: str) -> list[str]:
        raw_lines = [
            re.sub(r"^[\-•*\d\s\.、）)]+", "", line).strip()
            for line in resume_text.splitlines()
            if line.strip()
        ]
        meta_prefixes = (
            "姓名",
            "电话",
            "邮箱",
            "教育",
            "应聘岗位",
            "核心技能",
            "核心能力",
            "技能",
            "补充说明",
            "潜在风险",
            "个人评价",
        )
        candidates = []
        for line in raw_lines:
            if any(line.startswith(prefix) for prefix in meta_prefixes):
                continue
            if len(line) < 12:
                continue
            if any(
                token in line
                for token in ["项目", "系统", "平台", "模块", "重构", "优化", "上线", "搭建", "设计", "开发", "落地", "负责", "主导", "参与", "治理", "改造"]
            ):
                candidates.append(line)
        return candidates or [line for line in raw_lines if len(line) >= 12][:3]

    def _extract_resume_metrics(self, text: str) -> list[str]:
        if not text:
            return []
        patterns = [
            r"(?:P\d{2,3}|QPS|TPS|PV|UV|DAU|MAU|延迟|耗时|命中率|成功率|转化率|留存率|崩溃率|覆盖率|准确率|召回率|成本)\s*[=:：]?\s*\d+(?:\.\d+)?(?:ms|s|秒|分钟|小时|天|周|月|年|%|倍|次|个|人|w|W|k|K|万|亿)?",
            r"\d+(?:\.\d+)?(?:ms|s|秒|分钟|小时|天|周|月|年|%|倍|次|个|人|w|W|k|K|万|亿|QPS|TPS)",
        ]
        hits: list[str] = []
        for pattern in patterns:
            hits.extend(re.findall(pattern, text, re.IGNORECASE))
        cleaned = [str(item).strip() for item in hits if str(item).strip()]
        return self._dedupe(cleaned)

    def _extract_stack_tokens(self, text: str, role: dict[str, Any]) -> list[str]:
        if not text:
            return []
        catalog = self._dedupe(
            list(role.get("keywords", []))
            + COMMON_SKILLS
            + [
                "Python",
                "Java",
                "Go",
                "C++",
                "Redis",
                "MySQL",
                "Postgres",
                "PostgreSQL",
                "MongoDB",
                "Elasticsearch",
                "Kafka",
                "RabbitMQ",
                "Docker",
                "Kubernetes",
                "FastAPI",
                "Django",
                "Flask",
                "React",
                "Vue",
                "TypeScript",
                "JavaScript",
                "PyTorch",
                "TensorFlow",
                "LangChain",
                "RAG",
                "LLM",
                "Prompt",
                "gRPC",
                "Nginx",
                "ClickHouse",
                "Spark",
                "Flink",
                "Linux",
            ]
        )
        lowered = text.lower()
        positions = []
        for token in catalog:
            pos = lowered.find(str(token).lower())
            if pos >= 0:
                positions.append((pos, str(token)))
        positions.sort(key=lambda item: item[0])
        return self._dedupe([token for _, token in positions])

    def _expand_tech_tokens(self, values: list[str]) -> set[str]:
        aliases = {
            "fastapi": {"python"},
            "django": {"python"},
            "flask": {"python"},
            "spring": {"java"},
            "springboot": {"java"},
            "react": {"javascript", "typescript"},
            "vue": {"javascript", "typescript"},
            "node.js": {"javascript", "typescript"},
            "nodejs": {"javascript", "typescript"},
            "mysql": {"sql"},
            "postgresql": {"sql"},
            "postgres": {"sql", "postgresql"},
        }
        expanded: set[str] = set()
        for value in values:
            normalized = self._normalize_free_text(value)
            if not normalized:
                continue
            expanded.add(normalized)
            expanded.update(aliases.get(normalized, set()))
        return expanded

    def _infer_resume_inconsistencies(
        self,
        resume_text: str,
        projects: list[dict[str, Any]],
        proficient: list[str],
        theme_keyword: str,
    ) -> list[str]:
        inconsistencies = []
        lowered = resume_text.lower()
        if re.search(r"llm|大模型|ai", resume_text, re.IGNORECASE) and not any(
            token.lower() in lowered for token in ["prompt", "rag", "langchain", "gpt", "qwen", "glm", "claude"]
        ):
            inconsistencies.append("写了 AI/大模型经历，但没写清具体模型、框架或链路。")
        if any(token in resume_text for token in ["优化", "提升", "降低", "压到"]) and not self._extract_resume_metrics(resume_text):
            inconsistencies.append("写了优化或提升，但缺少量化结果。")
        if theme_keyword and theme_keyword not in resume_text:
            inconsistencies.append(f"关键词“{theme_keyword}”没有直接落在简历事实里。")
        if projects and not proficient:
            inconsistencies.append("项目写了不少，但技术栈标签不够清晰。")
        return inconsistencies[:5]

    def _build_resume_headline(
        self,
        resume_text: str,
        role: dict[str, Any],
        skills: dict[str, list[str]],
        projects: list[dict[str, Any]],
    ) -> str:
        years_match = re.search(r"(\d+(?:\.\d+)?)\s*年", resume_text)
        years_text = f"{years_match.group(1)} 年" if years_match else ""
        focus = " + ".join((skills.get("proficient") or role.get("keywords", []))[:3])
        project_name = projects[0]["name"] if projects else role["title"]
        prefix = f"{years_text}{role['title']}" if years_text else role["title"]
        return f"{prefix}，经历集中在 {project_name}，擅长 {focus or role['title']}。"

    def _resume_focus_points(self, resume_profile: dict[str, Any], analysis: dict[str, Any]) -> list[str]:
        anchors = [
            str(item.get("anchor", "")).strip()
            for item in resume_profile.get("drillTargets", [])
            if isinstance(item, dict) and str(item.get("anchor", "")).strip()
        ]
        if anchors:
            return self._dedupe(anchors)[:5]
        project_names = [
            str(item.get("name", "")).strip()
            for item in resume_profile.get("projects", [])
            if isinstance(item, dict) and str(item.get("name", "")).strip()
        ]
        if project_names:
            return self._dedupe(project_names)[:5]
        return list(analysis.get("followUpFocus", []))[:5]

    def _resume_project_by_id(self, resume_profile: dict[str, Any], project_id: str) -> dict[str, Any] | None:
        if not project_id:
            return None
        for item in resume_profile.get("projects", []):
            if isinstance(item, dict) and str(item.get("id", "")).strip() == project_id:
                return item
        return None

    def _resume_target_by_id(self, resume_profile: dict[str, Any], target_id: str) -> dict[str, Any] | None:
        if not target_id:
            return None
        for item in resume_profile.get("drillTargets", []):
            if isinstance(item, dict) and str(item.get("id", "")).strip() == target_id:
                return item
        return None

    def _available_drill_targets(self, session: dict[str, Any]) -> list[dict[str, Any]]:
        used = set(session.get("usedDrillTargetIds", []))
        result = []
        for item in session.get("resumeProfile", {}).get("drillTargets", []):
            if not isinstance(item, dict):
                continue
            if str(item.get("id", "")).strip() and item.get("id") not in used:
                result.append(copy.deepcopy(item))
        return result

    def _pick_round_drill_target(self, session: dict[str, Any]) -> dict[str, Any] | None:
        targets = self._available_drill_targets(session)
        if not targets:
            return None
        interviewer_id = session["interviewer"]["id"]
        scored: list[tuple[int, int, dict[str, Any]]] = []
        for index, target in enumerate(targets):
            project = self._resume_project_by_id(
                session.get("resumeProfile", {}),
                str(target.get("sourceProjectId", "")),
            )
            score = 0
            if project:
                score += len(project.get("metrics", [])) * 2
                score += len(project.get("highlights", []))
                score += len(project.get("suspects", []))
                if project.get("stack"):
                    score += 1
            if interviewer_id == "strict-architect":
                score += len((project or {}).get("suspects", [])) * 2
            elif interviewer_id == "gentle-senior":
                score += len((project or {}).get("highlights", []))
            else:
                score += len((project or {}).get("metrics", []))
            if any(char.isdigit() for char in f"{target.get('anchor', '')}{target.get('question', '')}"):
                score += 1
            scored.append((score, -index, target))
        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return copy.deepcopy(scored[0][2]) if scored else None

    def _opening_drill_target(self, resume_profile: dict[str, Any]) -> dict[str, Any] | None:
        projects = resume_profile.get("projects", [])
        first_project_id = str(projects[0].get("id", "")) if projects else ""
        for item in resume_profile.get("drillTargets", []):
            if isinstance(item, dict) and str(item.get("sourceProjectId", "")) == first_project_id:
                return copy.deepcopy(item)
        for item in resume_profile.get("drillTargets", []):
            if isinstance(item, dict):
                return copy.deepcopy(item)
        return None

    def _current_drill_target(self, session: dict[str, Any]) -> dict[str, Any] | None:
        target_id = str(session.get("currentDrillTargetId") or "")
        if not target_id:
            target_id = str(session.get("questionLinks", {}).get(session.get("currentQuestion", ""), ""))
        return self._resume_target_by_id(session.get("resumeProfile", {}), target_id)

    def _bound_project(
        self,
        session: dict[str, Any],
        target: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        project_id = str(session.get("currentBoundProjectId", ""))
        if not project_id and target:
            project_id = str(target.get("sourceProjectId", ""))
        if not project_id:
            current_target = target or self._current_drill_target(session)
            project_id = str((current_target or {}).get("sourceProjectId", ""))
        return self._resume_project_by_id(session.get("resumeProfile", {}), project_id)

    def _build_drill_stack(self, session: dict[str, Any]) -> list[dict[str, Any]]:
        start = max(0, int(session.get("roundStartTranscriptIndex", 0)))
        items = []
        for item in session.get("transcript", [])[start:]:
            speaker = str(item.get("speaker", "")).strip()
            text = str(item.get("text", "")).strip()
            if speaker and text:
                items.append({"speaker": speaker, "text": text})
        return items[-8:]

    def _bind_question_link(
        self,
        session: dict[str, Any],
        question: str,
        target: dict[str, Any] | None,
    ) -> None:
        if target and str(target.get("id", "")).strip():
            target_id = str(target["id"])
            session.setdefault("questionLinks", {})[question] = target_id
            if target_id not in session.setdefault("usedDrillTargetIds", []):
                session["usedDrillTargetIds"].append(target_id)
            session["currentDrillTargetId"] = target_id
            session["currentBoundProjectId"] = str(target.get("sourceProjectId", "") or "")
        else:
            session["currentDrillTargetId"] = None
            session["currentBoundProjectId"] = ""

    def _question_mentions_resume_fact(
        self,
        question: str,
        resume_profile: dict[str, Any],
        bound_project: dict[str, Any] | None = None,
        drill_target: dict[str, Any] | None = None,
        question_kind: str = "resume",
    ) -> bool:
        if question_kind == "knowledge":
            return True
        normalized_question = self._normalize_free_text(question)
        if not normalized_question:
            return False
        candidates: list[str] = []
        if drill_target:
            candidates.extend(
                [
                    str(drill_target.get("anchor", "")),
                    str(drill_target.get("topic", "")),
                ]
            )
        if bound_project:
            candidates.extend(
                [
                    str(bound_project.get("name", "")),
                    *[str(item) for item in bound_project.get("stack", [])],
                    *[str(item) for item in bound_project.get("metrics", [])],
                ]
            )
        for item in resume_profile.get("projects", []):
            if not isinstance(item, dict):
                continue
            candidates.extend(
                [
                    str(item.get("name", "")),
                    *[str(token) for token in item.get("stack", [])],
                    *[str(token) for token in item.get("metrics", [])],
                ]
            )
        candidates.extend(str(item) for item in resume_profile.get("metrics", []))
        for item in resume_profile.get("drillTargets", []):
            if isinstance(item, dict):
                candidates.append(str(item.get("anchor", "")))
        for candidate in candidates:
            normalized_candidate = self._normalize_free_text(candidate)
            if len(normalized_candidate) < 2:
                continue
            if normalized_candidate in normalized_question or normalized_question in normalized_candidate:
                return True
        return False

    def _extract_answer_highlights(self, answer: str, session: dict[str, Any]) -> list[str]:
        if not answer:
            return []
        highlights = []
        highlights.extend(self._extract_resume_metrics(answer)[:2])
        highlights.extend(self._extract_stack_tokens(answer, session["role"])[:2])
        for pattern in [
            r"(?:负责|主导|设计|优化|排查|搭建|重构|验证|协作)[^，。；]{4,24}",
            r"[\u4e00-\u9fa5]{3,12}(?:方案|指标|链路|缓存|索引|接口|模型|队列|监控)",
        ]:
            for hit in re.findall(pattern, answer):
                highlights.append(str(hit).strip())
        cleaned = [item for item in self._dedupe(highlights) if len(self._normalize_free_text(item)) >= 2]
        return cleaned[:3]

    def _build_answer_gaps(
        self,
        session: dict[str, Any],
        answer: str,
        answer_highlights: list[str],
    ) -> list[str]:
        gaps = []
        if session.get("currentQuestionKind") == "workplace":
            if len(answer) < 16:
                gaps.append("回答太短，没有给出明确态度")
            if not any(token in answer for token in ["我会", "可以", "优先", "先", "再", "沟通", "协调", "安排"]):
                gaps.append("缺少具体处理方式或沟通动作")
            if not any(token in answer for token in ["时间", "边界", "安排", "到岗", "冲突", "优先级"]):
                gaps.append("没有回应题目里的现实约束")
            return self._dedupe(gaps)[:3]

        if session.get("currentQuestionKind") == "knowledge":
            if len(answer) < 24:
                gaps.append("回答太短，关键技术点没展开")
            if not answer_highlights:
                gaps.append("没有提到关键技术概念、机制或实现细节")
            if not any(token in answer for token in ["因为", "所以", "比如", "例如", "会", "导致", "如果"]):
                gaps.append("只有结论，没有解释原理、条件或影响")
            vague = next((token for token in ["很多", "一些", "大概", "差不多", "可能", "应该"] if token in answer), "")
            if vague:
                gaps.append(f"“{vague}”这种表述太泛，缺少明确技术依据")
            return self._dedupe(gaps)[:3]

        bound_project = self._bound_project(session)
        if len(answer) < 40:
            gaps.append("只给了结论，没有展开动作和结果")
        if not any(token in answer for token in ["负责", "主导", "设计", "优化", "排查", "搭建", "验证", "复盘"]):
            gaps.append("没讲你亲手做了什么")
        if not any(char.isdigit() for char in answer):
            if bound_project and bound_project.get("metrics"):
                gaps.append(f"没交代 {bound_project['metrics'][0]} 是怎么做到的")
            else:
                gaps.append("没有给出可验证的数字或结果")
        vague = next((token for token in ["很多", "一些", "大概", "差不多", "比较好", "还不错"] if token in answer), "")
        if vague:
            gaps.append(f"“{vague}”这种说法太虚，缺少可验证细节")
        if not answer_highlights and len(answer) >= 40:
            gaps.append("没有落到一个可继续深挖的具体短语")
        return self._dedupe(gaps)[:3]

    def _detect_resume_conflict(self, session: dict[str, Any], answer: str) -> str:
        if session.get("currentQuestionKind") in {"knowledge", "workplace"}:
            return ""
        if not answer or not any(token in answer for token in ["主要", "核心", "技术栈", "当时用", "一直用", "实际用"]):
            return ""
        answer_tokens = self._extract_stack_tokens(answer, session["role"])
        if not answer_tokens:
            return ""
        resume_profile = session.get("resumeProfile", {})
        bound_project = self._bound_project(session)
        resume_tokens = self._expand_tech_tokens(
            list(resume_profile.get("skills", {}).get("proficient", []))
            + list(resume_profile.get("skills", {}).get("familiar", []))
            + [stack for project in resume_profile.get("projects", []) for stack in project.get("stack", [])]
        )
        for token in answer_tokens:
            normalized = self._normalize_free_text(token)
            if bound_project and bound_project.get("stack"):
                bound_stack = self._expand_tech_tokens(list(bound_project.get("stack", [])))
                if normalized not in bound_stack:
                    return f"你回答里强调 {token}，但简历里 {bound_project['name']} 写的是 {', '.join(bound_project['stack'][:3])}"
            if resume_tokens and normalized not in resume_tokens:
                return f"你回答里把 {token} 说成核心经历，但简历里没有对应项目或技术栈"
        return ""

    def _build_local_answer_feedback(
        self,
        session: dict[str, Any],
        verdict: str,
        highlights: list[str],
        gaps: list[str],
        conflict: str,
    ) -> str:
        interviewer_id = session["interviewer"]["id"]
        if conflict:
            table = {
                "gentle-senior": f"嗯，这里我得停一下，{conflict}，这会让我分不清你到底做的是哪一套。",
                "steady-engineer": f"这段前后对不上。{conflict}，所以我暂时不能把它当成可信经历。",
                "strict-architect": f"不行，{conflict}。这不是细节没讲清，是事实都没对上。",
                "master-strategist": f"此处前后失据。{conflict}。若连军报都对不上，我如何敢把筹策托付于你？",
                "queen-of-order": f"这话前后失统。{conflict}。连事实都压不住，何谈替我理事？",
                "detective-kid": f"等等，这里不对劲。{conflict}。证词一旦对不上，我就不能把它当成真相。",
            }
            return table.get(interviewer_id, table["steady-engineer"])

        if session.get("currentQuestionKind") == "workplace":
            detail = highlights[0] if highlights else "态度和安排"
            gap = gaps[0] if gaps else "回答还不够直接"
            table = {
                "gentle-senior": {
                    "correct": f"嗯，可以，你把“{detail}”说得比较实，也有现实感。",
                    "partial": f"方向还行，不过 {gap}，你可以再说清楚一点。",
                    "wrong": f"这题你答得有点飘，尤其是 {gap}。",
                },
                "steady-engineer": {
                    "correct": f"可以，这题你的态度、边界和处理方式都比较清楚。",
                    "partial": f"回答不算跑偏，但 {gap}，所以说服力还差一点。",
                    "wrong": f"这题答得不够稳，{gap}，我听不出你会怎么处理现实问题。",
                },
                "strict-architect": {
                    "correct": f"行，至少不是空表态，安排和边界都说到了。",
                    "partial": f"别只讲态度，{gap}，我还没听到你的处理方式。",
                    "wrong": f"不行，{gap}。这种题我想听明确结论，不是套话。",
                },
                "master-strategist": {
                    "correct": f"可以，你把“{detail}”这一步讲出了军令和取舍，不是纸上谈兵。",
                    "partial": f"方向未偏，不过 {gap}，这一步还缺落子与后手。",
                    "wrong": f"这答法还立不住，{gap}。我听见了态度，却没听见真正的布阵。",
                },
                "queen-of-order": {
                    "correct": f"这才像样。“{detail}”里有裁断、有分责，也看得见你压场的手腕。",
                    "partial": f"意思到了，但 {gap}，威信和执行还没被你讲实。",
                    "wrong": f"不够。{gap}。若只会讲漂亮话，场子一乱你就镇不住。",
                },
                "detective-kid": {
                    "correct": f"这次能听出来了，你把“{detail}”说成了线索、判断和验证，不只是感觉。",
                    "partial": f"推理方向没跑偏，但 {gap}，证据链还差关键一环。",
                    "wrong": f"这题你说得太像猜测了，{gap}。没有证据链，我不会采信。",
                },
            }
            return table.get(interviewer_id, table["steady-engineer"])[verdict]

        if session.get("currentQuestionKind") == "knowledge":
            detail = highlights[0] if highlights else (session.get("currentTopic") or "关键技术点")
            gap = gaps[0] if gaps else "核心概念还没讲到位"
            table = {
                "gentle-senior": {
                    "correct": f"嗯，这次把“{detail}”讲到点上了，至少不是只背名词。",
                    "partial": f"方向差不多，但 {gap}，你把机制再讲清一点。",
                    "wrong": f"这题你还没答到关键处，尤其是 {gap}。",
                },
                "steady-engineer": {
                    "correct": f"可以，像“{detail}”这种关键点你讲出来了，说明理解不是飘的。",
                    "partial": f"思路沾边了，不过 {gap}，所以还不够扎实。",
                    "wrong": f"这题没立住，{gap}，我还听不出你对原理的把握。",
                },
                "strict-architect": {
                    "correct": f"这次还行，“{detail}”这种关键机制你至少没讲错。",
                    "partial": f"别急着收，{gap}，这还撑不起一个完整技术判断。",
                    "wrong": f"不行，{gap}。这题你现在属于概念都没压住。",
                },
            }
            return table.get(interviewer_id, table["steady-engineer"])[verdict]

        detail = highlights[0] if highlights else "具体动作"
        gap = gaps[0] if gaps else "动作、依据和结果还不够具体"
        table = {
            "gentle-senior": {
                "correct": f"嗯，这次像“{detail}”这种细节说出来，我就能判断你是真的做过。",
                "partial": f"方向没偏，不过 {gap}，你再把你自己的动作说实一点。",
                "wrong": f"这段还是偏虚，比如 {gap}，我还没法确认你真正做了什么。",
            },
            "steady-engineer": {
                "correct": f"可以，这次至少把“{detail}”这种可验证细节讲出来了，链条是顺的。",
                "partial": f"思路有了，但 {gap}，所以论证还差一截。",
                "wrong": f"这段回答还站不住，{gap}，结果也没被你撑起来。",
            },
            "strict-architect": {
                "correct": f"这次还行，“{detail}”这种细节拿得出来，才像你真做过。",
                "partial": f"别急着下结论，{gap}，这点还撑不起你的说法。",
                "wrong": f"不行，{gap}。你这段话经不起继续追。",
            },
        }
        return table.get(interviewer_id, table["steady-engineer"])[verdict]

    def _public_code_question(self, session: dict[str, Any]) -> dict[str, Any] | None:
        code_question = session.get("currentCodeQuestion")
        if session.get("currentQuestionType") != "code" or not isinstance(code_question, dict):
            return None
        return {
            "title": str(code_question.get("title", "")),
            "description": str(code_question.get("description", "")),
            "signature": str(code_question.get("signature", "")),
            "examples": copy.deepcopy(code_question.get("examples", [])),
            "difficulty": str(code_question.get("difficulty", "medium")),
        }

    def _latest_candidate_text(self, session: dict[str, Any]) -> str:
        for item in reversed(session.get("transcript", [])):
            if item.get("speaker") == "candidate":
                return str(item.get("text", ""))
        return ""

    def _anchor_matches_recent_answer(self, session: dict[str, Any], anchor: str) -> bool:
        normalized_anchor = self._normalize_free_text(anchor)
        if not normalized_anchor:
            return False
        candidates = [self._latest_candidate_text(session)]
        candidates.extend(session.get("lastAnswerHighlights", []))
        candidates.extend(session.get("lastAnswerGaps", []))
        if not session.get("lastAnswerHighlights"):
            bound_project = self._bound_project(session)
            if bound_project:
                candidates.extend(bound_project.get("suspects", []))
        for candidate in candidates:
            normalized_candidate = self._normalize_free_text(candidate)
            if not normalized_candidate:
                continue
            if normalized_anchor in normalized_candidate or normalized_candidate in normalized_anchor:
                return True
        return False

    def _extract_anchor_from_answer(self, answer: str) -> str:
        if not answer:
            return ""

        patterns = [
            r"\d+(?:\.\d+)?(?:ms|s|秒|分钟|小时|天|周|月|年|%|倍|次|个)?",
            r"[A-Za-z][A-Za-z0-9_.+#/-]{1,24}",
            r"(?:缓存|索引|组件|接口|链路|队列|并发|日志|模型|训练|部署|监控|性能优化|限流|数据库|前端|后端|测试|埋点|脚本)",
            r"[\u4e00-\u9fa5]{2,8}",
        ]
        for pattern in patterns:
            hits = re.findall(pattern, answer)
            if hits:
                return str(hits[-1]).strip()
        chunks = [chunk.strip() for chunk in re.split(r"[，。；、\s]+", answer) if chunk.strip()]
        return chunks[-1] if chunks else ""

    def _local_drill_question(self, session: dict[str, Any]) -> dict[str, Any]:
        interviewer_id = session["interviewer"]["id"]
        if interviewer_id in {"master-strategist", "queen-of-order", "detective-kid"}:
            return self._nontechnical_local_drill_question(session)
        depth = max(1, int(session["drillDepth"]))
        current_target = self._current_drill_target(session)
        bound_project = self._bound_project(session, current_target)
        highlight = (session.get("lastAnswerHighlights") or [""])[0]
        gap = (session.get("lastAnswerGaps") or [""])[0]
        suspect = ""
        if bound_project and bound_project.get("suspects"):
            suspect = str(bound_project["suspects"][0])

        if session.get("currentQuestionType") == "code":
            anchor = highlight or gap or self._extract_anchor_from_answer(self._latest_candidate_text(session))
            if not anchor:
                anchor = session.get("currentTopic") or "这一步"
            bank = {
                "gentle-senior": [
                    f"嗯，那你顺着“{anchor}”再说一下，时间复杂度和你为什么这么写？",
                    f"如果输入再大一点，“{anchor}”这块会不会先出问题？",
                    f"要是现在让你当场改，“{anchor}”这里你会先补哪种边界？",
                ],
                "steady-engineer": [
                    f"你刚提到“{anchor}”，那这一步的复杂度和边界你怎么判断？",
                    f"如果“{anchor}”这块出现异常输入，你的处理分支会怎么补？",
                    f"我继续追一下，“{anchor}”为什么是这里而不是别的结构？",
                ],
                "strict-architect": [
                    f"别泛泛讲，就盯着“{anchor}”。最坏情况复杂度是多少？",
                    f"如果“{anchor}”这里出 bug，第一类错会是什么？",
                    f"再往下说，“{anchor}”这块你凭什么确定它撑得住边界？",
                ],
            }
            variants = bank.get(interviewer_id, bank["steady-engineer"])
            return {
                "question": variants[min(depth - 1, len(variants) - 1)],
                "drillTarget": current_target,
                "topic": (current_target or {}).get("topic") or anchor,
            }

        anchor = highlight or gap or suspect
        if not anchor:
            fallback_target = self._pick_round_drill_target(session)
            if fallback_target and not self._question_seen_recently(session, fallback_target["question"]):
                return {
                    "question": fallback_target["question"],
                    "drillTarget": fallback_target,
                    "topic": fallback_target.get("topic") or fallback_target.get("anchor") or "简历追问",
                }
            anchor = (current_target or {}).get("anchor") or self._extract_anchor_from_answer(
                self._latest_candidate_text(session)
            )
        if not anchor:
            anchor = session.get("currentTopic") or (session.get("focusPoints") or ["这个点"])[0]

        if gap or suspect:
            bank = {
                "gentle-senior": [
                    f"嗯，你刚才这段里“{anchor}”还比较虚，你补一下具体场景和结果？",
                    f"那“{anchor}”如果真是你做的，你当时第一步动作是什么？",
                    f"如果现在复盘“{anchor}”，你会用哪个数字证明它真的成立？",
                ],
                "steady-engineer": [
                    f"你这段里“{anchor}”没讲透，我想听你把动作、依据和结果补完整。",
                    f"别换话题，就围绕“{anchor}”说，你当时到底做了什么？",
                    f"如果“{anchor}”是真的，给我一个指标、日志或取舍依据来证明。",
                ],
                "strict-architect": [
                    f"别糊弄，刚才“{anchor}”这句是空的。你亲手做了什么，直接说。",
                    f"你现在把“{anchor}”拆开讲，不要再给我抽象结论。",
                    f"如果“{anchor}”真发生过，代价、指标和判断依据分别是什么？",
                ],
            }
        else:
            bank = {
                "gentle-senior": [
                    f"嗯，我想顺着你刚才说的“{anchor}”再问一下，这一步你是怎么定下来的？",
                    f"那“{anchor}”当时最难的地方是什么，你是怎么把它推进去的？",
                    f"如果“{anchor}”这件事再来一次，你会先改哪一步？",
                ],
                "steady-engineer": [
                    f"你刚提到“{anchor}”，我想再听具体一点，你当时的判断依据是什么？",
                    f"那围绕“{anchor}”，你实际做的动作和最后结果分别是什么？",
                    f"如果“{anchor}”没达到预期，你准备怎么复盘和兜底？",
                ],
                "strict-architect": [
                    f"就盯着“{anchor}”说，你亲自拍板的点到底是什么？",
                    f"“{anchor}”这里最容易被追责的地方在哪，你当时怎么扛住的？",
                    f"如果“{anchor}”最后做坏了，代价是什么，谁来背？",
                ],
            }
        variants = bank.get(interviewer_id, bank["steady-engineer"])
        return {
            "question": variants[min(depth - 1, len(variants) - 1)],
            "drillTarget": current_target,
            "topic": (current_target or {}).get("topic") or anchor,
        }

    def _local_hint(self, session: dict[str, Any]) -> str:
        interviewer_id = session["interviewer"]["id"]
        if interviewer_id in {"master-strategist", "queen-of-order", "detective-kid"}:
            return self._nontechnical_local_hint(session)
        used = session["hintsUsed"]
        if session.get("currentQuestionKind") == "workplace":
            bank = {
                "gentle-senior": [
                    "你先直接给结论，再补你会怎么安排和沟通。",
                    "把边界说清楚就行，比如时间、优先级或者你会先和谁对齐。",
                ],
                "steady-engineer": [
                    "别铺陈背景，先说你的处理原则，再说现实安排。",
                    "直接回答你会怎么做，并补一句你会怎么沟通边界。",
                ],
                "strict-architect": [
                    "少讲态度，直接给结论，再说你的边界和动作。",
                    "就回答三个点：怎么选、怎么沟通、风险怎么兜。",
                ],
            }
            variants = bank.get(interviewer_id, bank["steady-engineer"])
            for variant in variants:
                if not self._hint_seen(session, variant):
                    return variant
            return "直接给结论，再补你的边界和沟通方式。"

        if session.get("currentQuestionKind") == "knowledge":
            directions = [
                str(item).strip()
                for item in session.get("currentHintDirections", [])
                if str(item).strip() and not self._hint_direction_used(session, str(item).strip())
            ]
            direction = directions[0] if directions else session.get("currentTopic", "这个技术点")
            bank = {
                "gentle-senior": [
                    f"别急，你可以先从“{direction}”这个角度开讲，慢一点没关系。",
                    f"你就盯着“{direction}”拆一下，先解释它为什么会这样。",
                    f"最后一次提示了，我想听到“{direction}”背后的机制或代价。",
                ],
                "steady-engineer": [
                    f"先别发散，就围绕“{direction}”回答，这题核心在这里。",
                    f"把“{direction}”讲清楚，再顺手补它带来的影响或取舍。",
                    f"最后一次，至少给我一个围绕“{direction}”的明确判断点。",
                ],
                "strict-architect": [
                    f"别背套话，就盯着“{direction}”讲，这题先把关键机制压住。",
                    f"继续收窄，围绕“{direction}”回答，不要再飘到别的概念上。",
                    f"最后一次提示，把“{direction}”的原理、风险或代价直接说出来。",
                ],
            }
            variants = bank.get(interviewer_id, bank["steady-engineer"])
            for variant in variants:
                if not self._hint_seen(session, variant):
                    return variant
            return f"你就围绕“{direction}”回答，把关键机制和影响讲清楚。"

        bank = {
            "gentle-senior": [
                "别急，你先把场景说清楚，再补你当时最关键的处理点。",
                "你就盯着一个具体决策往下讲，不用一下铺太开。",
            ],
            "steady-engineer": [
                "先别铺太开，你先把你负责的那一段讲清楚。",
                "别一直讲团队整体，直接落到你的判断点和处理细节。",
            ],
            "strict-architect": [
                "别绕，直接说你拍板的点和你怎么验证的。",
                "继续压缩废话，给我一个具体判断点和一个代价。",
            ],
        }
        variants = bank.get(interviewer_id, bank["steady-engineer"])
        for variant in variants:
            if not self._hint_seen(session, variant):
                return variant
        return "直接回答最关键的判断点，并补一个能验证的细节。"

    def _nontechnical_local_drill_question(self, session: dict[str, Any]) -> dict[str, Any]:
        interviewer_id = session["interviewer"]["id"]
        depth = max(1, int(session["drillDepth"]))
        anchor = (
            (session.get("lastAnswerHighlights") or [""])[0]
            or (session.get("lastAnswerGaps") or [""])[0]
            or self._extract_anchor_from_answer(self._latest_candidate_text(session))
            or session.get("currentTopic")
            or "刚才那一步"
        )

        if interviewer_id == "master-strategist":
            variants = [
                f"围绕“{anchor}”，你别再讲大势，直接告诉我你第一道军令是什么，为什么是这道令先下。",
                f"若把“{anchor}”当作这一局的关键落子，你舍了什么，换来了什么？",
                f"再往深一层说，“{anchor}”这一步若失手，整盘局最先崩的是哪一环，你如何设后手？",
            ]
        elif interviewer_id == "queen-of-order":
            variants = [
                f"就盯着“{anchor}”回答。你当时到底定了什么规矩，谁必须服从，谁需要安抚？",
                f"围绕“{anchor}”，你拍板的依据是什么？别讲大家意见，讲你自己的裁断。",
                f"若“{anchor}”引来反弹，你如何既不失威信，又不让执行失速？",
            ]
        else:
            variants = [
                f"等等，“{anchor}”这里像有一块拼图没补上。你最先发现的异常线索到底是什么？",
                f"围绕“{anchor}”，你是怎么排除其他嫌疑解释，最后锁到这条真相链上的？",
                f"如果“{anchor}”是误导线索，你原本准备怎么验证并推翻它？",
            ]

        return {
            "question": variants[min(depth - 1, len(variants) - 1)],
            "drillTarget": self._current_drill_target(session),
            "topic": anchor,
        }

    def _nontechnical_local_hint(self, session: dict[str, Any]) -> str:
        interviewer_id = session["interviewer"]["id"]
        anchor = session.get("currentTopic") or "这一点"
        banks = {
            "master-strategist": [
                f"先别铺全局，就围着“{anchor}”说。先讲你的主目标，再讲调度和取舍。",
                f"把它讲成一场布阵: 谁先动，谁后动，为什么这样排。",
            ],
            "queen-of-order": [
                f"少讲气氛，多讲掌控。围绕“{anchor}”直接说你怎么定规、分责、推进。",
                f"先给裁断，再讲安抚。我要听见你如何拍板，不是大家如何讨论。",
            ],
            "detective-kid": [
                f"把“{anchor}”当成案发现场。先说异常，再说推理，最后说验证。",
                f"别先给结论，先给证据。你最确信的那条线索是什么？",
            ],
        }
        variants = banks.get(interviewer_id, banks["master-strategist"])
        for variant in variants:
            if not self._hint_seen(session, variant):
                return variant
        return variants[-1]

    def _timeout_feedback(self, session: dict[str, Any]) -> str:
        table = {
            "gentle-senior": "时间到了，没事，我们先过这一题。",
            "steady-engineer": "时间到，这题我先按没答完整处理。",
            "strict-architect": "超时了，这题按放弃算。",
            "master-strategist": "时机已过。这一题我先按你未及下令处理。",
            "queen-of-order": "时间到了。临场若迟疑太久，局面就不会等你。",
            "detective-kid": "时间到。还没来得及把证据链补全，这一题我只能先记下疑点。",
        }
        return table.get(session["interviewer"]["id"], "时间到了。")

    def _local_opening_question(
        self,
        role: dict[str, Any],
        interviewer: dict[str, Any],
        theme_keyword: str,
        resume_profile: dict[str, Any],
    ) -> str:
        projects = resume_profile.get("projects", [])
        if projects:
            first_project = projects[0]
            anchor = (
                (first_project.get("metrics") or [""])[0]
                or (first_project.get("highlights") or [first_project.get("name", "")])[0]
            )
            return (
                f"我们先从 {first_project.get('name', '这个项目')} 开始。"
                f"你简历里提到“{anchor}”，这件事里你亲手做的关键动作是什么？"
            )
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
            "gentle-senior": {
                "correct": "嗯，这次我能听明白了，动作和结果都对上了。",
                "partial": "方向是对的，不过你再讲实一点会更有说服力。",
                "wrong": "这段还比较虚，我没听到你真正做了什么。",
            },
            "steady-engineer": {
                "correct": "可以，这次逻辑和依据都比较完整。",
                "partial": "思路有了，但论证链条还差一点。",
                "wrong": "这段回答还站不住，关键依据和结果都不够具体。",
            },
            "strict-architect": {
                "correct": "这次还行，至少不是空话。",
                "partial": "方向没全错，但细节还撑不起这个结论。",
                "wrong": "不行，这段回答经不起追问。",
            },
            "master-strategist": {
                "correct": "这一答有章法，进退与取舍都不是乱的。",
                "partial": "局势你看到了，但落子还不够准。",
                "wrong": "这番话还像空城鼓噪，听不出你真能定策。",
            },
            "queen-of-order": {
                "correct": "可以，听得出你能断事，不只是随声附和。",
                "partial": "意思有了，但威信、规矩和执行还没立住。",
                "wrong": "不够。若真把场交给你，局面多半先乱。",
            },
            "detective-kid": {
                "correct": "这次像侦探了，你给的是线索和判断，不是拍脑袋。",
                "partial": "推理方向对，但证据链还没扣紧。",
                "wrong": "这不行，像猜，不像查出来的。",
            },
        }
        return table.get(interviewer_id, table["steady-engineer"])[verdict]

    def _pick_quote(self, interviewer_id: str, verdict: str) -> str:
        quotes = {
            "gentle-senior": {
                "offer": "你不是靠背稿在答，你是真做过，所以细节是活的。",
                "reject": "底子是有的，就是还没把经历讲到让人放心。",
            },
            "steady-engineer": {
                "offer": "你的判断、动作和结果能接上，这就够有说服力了。",
                "reject": "你不是完全不会，只是证据链还没搭起来。",
            },
            "strict-architect": {
                "offer": "能扛住追问，说明你手上真有活。",
                "reject": "简历写得挺满，但回答没把它撑住。",
            },
            "master-strategist": {
                "offer": "你不是只会谈势，你是真能在乱局里定先后、分轻重的人。",
                "reject": "你看见了几分局势，却还没有把筹策真正落到手上。",
            },
            "queen-of-order": {
                "offer": "你说话能立规矩，做事能压住场，这才是可用之才。",
                "reject": "你有几分胆气，但还没练到能在众声里把秩序立稳。",
            },
            "detective-kid": {
                "offer": "你没有急着站队，而是一路把线索查到能还原真相，这点很厉害。",
                "reject": "你不是完全没感觉，只是很多判断还停在直觉，没有变成证据链。",
            },
        }
        return quotes.get(interviewer_id, quotes["steady-engineer"]).get(verdict, "")

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
        return f"下一次优先补强：{'、'.join(tips)}。回答时先命中问题核心，再补原因、机制、细节或取舍。"

    def _event_choice_label(self, event: dict[str, Any], choice_id: str) -> str:
        interaction = event.get("interaction") or {}
        for option in interaction.get("options", []):
            if option.get("id") == choice_id:
                return str(option.get("label", ""))
        return ""

    def _resume_tech_anchors(
        self,
        session: dict[str, Any],
        extra_anchor: str = "",
    ) -> list[str]:
        resume_profile = session.get("resumeProfile", {})
        anchors = []
        for key in ("proficient", "familiar", "claimedButUnverified"):
            anchors.extend(resume_profile.get("skills", {}).get(key, []))
        for project in resume_profile.get("projects", []):
            anchors.extend(project.get("stack", []))
        if extra_anchor:
            anchors.append(extra_anchor)
        return [
            self._normalize_free_text(item)
            for item in self._dedupe([str(item).strip() for item in anchors if str(item).strip()])
            if self._normalize_free_text(item)
        ]

    def _resume_has_tech_anchor(
        self,
        session: dict[str, Any],
        drill_target: dict[str, Any] | None,
    ) -> bool:
        if not drill_target:
            return False
        bound_project = self._bound_project(session, drill_target)
        if bound_project and bound_project.get("stack"):
            return True
        anchor = self._normalize_free_text(drill_target.get("anchor", ""))
        return bool(anchor and anchor in self._resume_tech_anchors(session))

    def _hint_seen(self, session: dict[str, Any], hint: str) -> bool:
        normalized_hint = self._normalize_free_text(hint)
        if not normalized_hint:
            return False
        return normalized_hint in {
            self._normalize_free_text(item)
            for item in session.get("hintHistory", [])
            if str(item).strip()
        }

    def _hint_direction_used(self, session: dict[str, Any], direction: str) -> bool:
        normalized_direction = self._normalize_free_text(direction)
        if not normalized_direction:
            return False
        for hint in session.get("hintHistory", []):
            if normalized_direction in self._normalize_free_text(hint):
                return True
        return False

    # ------------------------------------------------------------------ util

    def _question_seen_recently(self, session: dict[str, Any], question: str) -> bool:
        normalized = self._normalize_question(question)
        recent = [self._normalize_question(item) for item in session.get("questionHistory", [])[-3:]]
        return normalized in recent

    def _normalize_free_text(self, text: str) -> str:
        normalized = re.sub(r"\s+", "", str(text or "")).lower()
        replacements = {
            "毫秒": "ms",
            "msec": "ms",
            "秒钟": "s",
            "秒": "s",
            "分钟": "min",
            "百分比": "%",
            "％": "%",
            "postgres": "postgresql",
        }
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        return normalized

    def _normalize_question(self, question: str) -> str:
        return self._normalize_free_text(question)

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
