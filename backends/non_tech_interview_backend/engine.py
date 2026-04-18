from __future__ import annotations

import copy
import importlib.util
import random
import time
import uuid
from pathlib import Path
from typing import Any

from backends.tech_interview_backend.ai_client import AIClient
from backends.tech_interview_backend.interviewers import (
    all_interviewers as base_all_interviewers,
    get_interviewer as base_get_interviewer,
    public_card as base_public_card,
)

try:
    # Optional extra pool from local custom directory
    from backend.interviewers import all_interviewers as extra_all_interviewers
except Exception:  # noqa: BLE001
    extra_all_interviewers = None


def _load_legacy_interviewers() -> list[dict[str, Any]]:
    """Load optional legacy interviewer files from ./backend/interviewers/*.py."""

    root = Path(__file__).resolve().parents[2]
    legacy_dir = root / "backend" / "interviewers"
    if not legacy_dir.exists():
        return []

    loaded: list[dict[str, Any]] = []
    for path in legacy_dir.glob("*.py"):
        if path.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"legacy_nontech_{path.stem}", path)
            if not spec or not spec.loader:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            data = getattr(module, "INTERVIEWER", None)
            if isinstance(data, dict) and data.get("id") and data.get("name"):
                loaded.append(data)
        except Exception:  # noqa: BLE001
            continue
    return loaded

DIMENSION_KEYS = ["roleFit", "logic", "depth", "consistency", "composure", "adaptability"]

ROUND_BASE_SCORE = 100
PARTIAL_PENALTY = 12
WRONG_PENALTY = 30
HINT_PENALTY = 8
TIMEOUT_SCORE = 10
MAX_HINTS = 2
PREVIEW_PRIORITY_IDS = ["master-strategist", "queen-of-order", "detective-kid"]

DIFFICULTIES = {
    "easy": {"id": "easy", "label": "轻松", "description": "追问温和，节奏较慢", "max_turns": 3, "starting_stress": 15},
    "normal": {"id": "normal", "label": "标准", "description": "正常面试压强", "max_turns": 4, "starting_stress": 22},
    "hard": {"id": "hard", "label": "硬核", "description": "追问更紧，容错更低", "max_turns": 5, "starting_stress": 30},
}

def _preview_nontech_pool(limit: int = 3) -> list[dict[str, Any]]:
def _nontech_pool() -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in base_all_interviewers("non-technical"):
        if item.get("featured_role"):
            merged[str(item.get("id"))] = item

    if extra_all_interviewers is not None:
        try:
            for item in extra_all_interviewers("non-technical"):
                if item.get("featured_role"):
                    merged[str(item.get("id"))] = item
        except Exception:  # noqa: BLE001
            pass

    for item in _load_legacy_interviewers():
        tracks = item.get("interview_tracks") or ["technical"]
        if "non-technical" in tracks and item.get("featured_role"):
            merged[str(item.get("id"))] = item

    return list(merged.values())


def _public_card(interviewer: dict[str, Any]) -> dict[str, Any]:
    # base formatter first
    card = base_public_card(interviewer)
    # ensure avatar from source data is preserved (some registries may normalize it away)
    card["avatar"] = str(interviewer.get("avatar") or card.get("avatar") or "")
    return card


def _get_nontech_interviewer(interviewer_id: str) -> dict[str, Any]:
    iid = str(interviewer_id or "").strip()
    pool = _nontech_pool()
    if iid:
        for item in pool:
            if str(item.get("id")) == iid:
                return item
    # fallback to base registry behavior if possible
    picked = base_get_interviewer(iid, "non-technical")
    if picked.get("featured_role"):
        return picked
    return random.choice(pool) if pool else picked

def _preview_nontech_pool(limit: int = 3) -> list[dict[str, Any]]:
    pool = _nontech_pool()
    if not pool:
        return []

    by_id = {str(item.get("id")): item for item in pool}
    preview: list[dict[str, Any]] = []
    seen: set[str] = set()

    for interviewer_id in PREVIEW_PRIORITY_IDS:
        item = by_id.get(interviewer_id)
        if not item:
            continue
        preview.append(item)
        seen.add(interviewer_id)

    remaining = sorted(
        (item for item in pool if str(item.get("id")) not in seen),
        key=lambda item: (int(item.get("order", 999)), str(item.get("id", ""))),
    )
    preview.extend(remaining)
    return preview[:limit]

class GameEngine:
    def __init__(self) -> None:
        self.ai_client = AIClient()
        self.sessions: dict[str, dict[str, Any]] = {}

    def has_session(self, session_id: str) -> bool:
        return str(session_id or "") in self.sessions

    def get_bootstrap(self) -> dict[str, Any]:
        preview = _preview_nontech_pool()
        return {
            "nonTechnicalInterviewers": [_public_card(item) for item in preview],
            "interviewTracks": [
                {
                    "id": "non-technical",
                    "label": "非技术面",
                    "description": "娱乐化三选一卡池：角色自带岗位，不需简历。",
                    "enabled": True,
                }
            ],
            "difficulties": [{"id": key, **value} for key, value in DIFFICULTIES.items()],
            "runtime": self.ai_client.runtime_status(),
        }

    def build_invitations(self, payload: dict[str, Any]) -> dict[str, Any]:
        difficulty = self._difficulty(payload.get("difficulty", "normal"))
        pool = _nontech_pool()
        if not pool:
            raise ValueError("非技术面试官卡池为空，请检查 interviewers 目录。")
        random.shuffle(pool)
        picked = pool[:3]
        return {
            "role": None,
            "difficulty": difficulty,
            "analysis": {
                "themeBlurb": "三位来自不同世界观的面试官已入场。选一张卡，拿下他/她的岗位。",
                "strengths": ["无需简历", "岗位与题目贴合角色背景", "流程与技术面一致，易上手"],
                "riskPoints": ["不讲现代职场黑话，只讲角色时代语境", "追问会盯执行细节", "超时会被直接扣分"],
            },
            "interviewTrack": "non-technical",
            "comingSoon": False,
            "placeholder": None,
            "invitations": [_public_card(item) for item in picked],
        }

    def start_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        interviewer_id = str(payload.get("interviewerId") or "").strip()
        if interviewer_id:
            interviewer = _get_nontech_interviewer(interviewer_id)
        else:
            candidates = _nontech_pool()
            if not candidates:
                raise ValueError("非技术面试官卡池为空，请检查 interviewers 目录。")
            interviewer = random.choice(candidates)

        if not interviewer.get("featured_role"):
            raise ValueError("该面试官缺少 featured_role，无法开启非技术面。")

        difficulty = self._difficulty(payload.get("difficulty", "normal"))
        role = copy.deepcopy(interviewer["featured_role"])
        min_rounds = int(interviewer.get("min_rounds", 3))
        max_rounds = int(interviewer.get("max_rounds", 5))
        total_rounds = random.randint(min_rounds, max_rounds)

        first = self._pick_question(interviewer, used=[])
        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "createdAt": time.time(),
            "interviewTrack": "non-technical",
            "role": role,
            "interviewer": interviewer,
            "difficulty": difficulty,
            "themeKeyword": "",
            "resumeMode": "none",
            "resumeText": "",
            "analysis": {
                "themeBlurb": "非技术面：角色岗位制",
                "strengths": ["题目围绕角色岗位", "强调临场判断"],
                "riskPoints": ["答案空泛会被连续追问"],
            },
            "currentPhase": "awaiting_answer",
            "roundIndex": 1,
            "totalRounds": total_rounds,
            "drillDepth": 0,
            "hintsUsed": 0,
            "hintHistory": [],
            "currentQuestion": first["q"],
            "currentQuestionType": "normal",
            "currentQuestionKind": "workplace",
            "currentTopic": first.get("topic", ""),
            "currentHintDirections": first.get("hint_directions", []),
            "roundScore": ROUND_BASE_SCORE,
            "roundScores": [],
            "sessionStress": int(difficulty.get("starting_stress", 20)),
            "dimensions": {key: 60 for key in DIMENSION_KEYS},
            "usedQuestions": [first["q"]],
            "transcript": [
                {"speaker": "interviewer", "text": interviewer.get("opening_line") or f"我是{interviewer['name']}。先让我看看你是否真能担这份差事。"},
                {"speaker": "question", "text": f"[第 1 轮] {first['q']}"},
            ],
        }
        self.sessions[session_id] = session
        return self._descriptor(
            session,
            phase="awaiting_answer",
            question=first["q"],
            timer_ms=int(interviewer.get("answer_time_ms", 90_000)),
        )

    def submit_answer(self, payload: dict[str, Any]) -> dict[str, Any]:
        session = self._session(payload.get("sessionId"))
        answer = str(payload.get("answer") or "").strip()
        if not answer:
            raise ValueError("回答不能为空。")

        session["transcript"].append({"speaker": "candidate", "text": answer})
        verdict = self._judge_answer(session, answer)
        session["transcript"].append({"speaker": "feedback", "text": verdict["feedback"]})
        self._apply_dimension_delta(session, verdict["score_delta"])

        if verdict["status"] in {"correct", "partial"} and session["drillDepth"] < 3 and random.random() < self._drill_prob(session):
            session["drillDepth"] += 1
            drill_q = self._build_drill_question(session, answer)
            session["currentQuestion"] = drill_q
            session["transcript"].append({"speaker": "question", "text": f"[追问 {session['drillDepth']}] {drill_q}"})
            return self._descriptor(session, phase="awaiting_answer", question=drill_q, timer_ms=int(session["interviewer"].get("answer_time_ms", 90_000)))

        if verdict["status"] == "wrong" and session["hintsUsed"] < MAX_HINTS and random.random() < float(session["interviewer"].get("hint_probability", 0.3)):
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

        self._close_round(session)
        if session["roundIndex"] > session["totalRounds"]:
            return self._finalize(session)

        nxt = self._pick_question(session["interviewer"], used=session["usedQuestions"])
        session["drillDepth"] = 0
        session["hintsUsed"] = 0
        session["hintHistory"] = []
        session["roundScore"] = ROUND_BASE_SCORE
        session["currentQuestion"] = nxt["q"]
        session["currentHintDirections"] = nxt.get("hint_directions", [])
        session["currentTopic"] = nxt.get("topic", "")
        session["usedQuestions"].append(nxt["q"])
        session["transcript"].append({"speaker": "question", "text": f"[第 {session['roundIndex']} 轮] {nxt['q']}"})
        return self._descriptor(session, phase="awaiting_answer", question=nxt["q"], timer_ms=int(session["interviewer"].get("answer_time_ms", 90_000)))

    def submit_timeout(self, payload: dict[str, Any]) -> dict[str, Any]:
        session = self._session(payload.get("sessionId"))
        session["roundScore"] = TIMEOUT_SCORE
        session["transcript"].append({"speaker": "feedback", "text": self._timeout_line(session)})
        self._close_round(session)
        if session["roundIndex"] > session["totalRounds"]:
            return self._finalize(session)

        nxt = self._pick_question(session["interviewer"], used=session["usedQuestions"])
        session["drillDepth"] = 0
        session["hintsUsed"] = 0
        session["hintHistory"] = []
        session["roundScore"] = ROUND_BASE_SCORE
        session["currentQuestion"] = nxt["q"]
        session["currentHintDirections"] = nxt.get("hint_directions", [])
        session["currentTopic"] = nxt.get("topic", "")
        session["usedQuestions"].append(nxt["q"])
        session["transcript"].append({"speaker": "question", "text": f"[第 {session['roundIndex']} 轮] {nxt['q']}"})
        return self._descriptor(session, phase="awaiting_answer", question=nxt["q"], timer_ms=int(session["interviewer"].get("answer_time_ms", 90_000)))

    def submit_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        session = self._session(payload.get("sessionId"))
        return self._descriptor(
            session,
            phase="awaiting_answer",
            question=session.get("currentQuestion"),
            timer_ms=int(session["interviewer"].get("answer_time_ms", 90_000)),
        )

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
            "interviewer": _public_card(session["interviewer"]),
            "difficulty": session["difficulty"],
            "themeKeyword": "",
            "resumeMode": "none",
            "interviewTrack": "non-technical",
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
            "questionType": "normal",
            "codeQuestion": None,
            "hint": hint,
            "eventNote": event_note,
            "timerMs": timer_ms,
            "event": event,
            "report": report,
            "selected": selected,
            "metrics": metrics,
            "resumeText": "",
            "analysis": session["analysis"],
            "transcript": copy.deepcopy(session["transcript"]),
            "roundHistory": copy.deepcopy(session["roundScores"]),
        }

    def _finalize(self, session: dict[str, Any]) -> dict[str, Any]:
        score = self._current_session_score(session)
        pass_score = int(session["interviewer"].get("pass_score", 70))
        verdict = "offer" if score >= pass_score else "reject"
        quote = session["interviewer"].get("offer_reject_commentary", {})
        interviewer_quote = quote.get("offer" if verdict == "offer" else "reject") or "这份差事，能不能交给你，我心里有数了。"
        report = {
            "verdict": verdict,
            "verdictLabel": "通过" if verdict == "offer" else "未录用",
            "summary": "你在这场角色面试中展现了稳定判断与表达。" if verdict == "offer" else "你的回答有思路，但在取舍与落地上仍需加强。",
            "interviewerQuote": interviewer_quote,
            "highlight": "能把复杂局面拆成可执行步骤。",
            "flop": "在高压追问下有时会变空泛。",
            "tips": "建议继续练习：先判断、再行动、最后复盘。",
            "shareLines": ["我刚打完一场娱乐化非技术面。", f"综合分 {score} / 通过线 {pass_score}。", "你也来试试哪张卡面最适合你。"],
            "dimensions": copy.deepcopy(session["dimensions"]),
            "roundScores": copy.deepcopy(session["roundScores"]),
            "sessionScore": score,
            "passScore": pass_score,
            "offerLetter": None,
            "forcedEndReason": "",
        }
        return self._descriptor(session, phase="final", report=report)

    def _close_round(self, session: dict[str, Any]) -> None:
        session["roundScores"].append(
            {
                "round": session["roundIndex"],
                "score": int(max(0, min(100, session["roundScore"]))),
                "drillDepth": session["drillDepth"],
                "hintsUsed": session["hintsUsed"],
            }
        )
        session["roundIndex"] += 1

    def _judge_answer(self, session: dict[str, Any], answer: str) -> dict[str, Any]:
        text = answer.strip()
        hints = [str(item) for item in session.get("currentHintDirections", []) if str(item).strip()]
        hit = sum(1 for token in hints if token in text)

        if len(text) >= 60 and hit >= 1:
            return {"status": "correct", "feedback": "回答有判断、有步骤，也考虑了后果。", "score_delta": 6}
        if len(text) >= 30:
            session["roundScore"] = max(0, session["roundScore"] - PARTIAL_PENALTY)
            return {"status": "partial", "feedback": "方向基本对，但还缺关键落地动作。", "score_delta": 2}

        session["roundScore"] = max(0, session["roundScore"] - WRONG_PENALTY)
        return {"status": "wrong", "feedback": "答案过于笼统，无法支撑岗位决策。", "score_delta": -4}

    def _apply_dimension_delta(self, session: dict[str, Any], delta: int) -> None:
        for key in DIMENSION_KEYS:
            session["dimensions"][key] = max(0, min(100, session["dimensions"][key] + delta))
        session["sessionStress"] = max(0, min(100, session["sessionStress"] + (3 if delta < 0 else -2)))

    def _build_drill_question(self, session: dict[str, Any], answer: str) -> str:
        interviewer_id = str(session["interviewer"].get("id") or "")
        topic = session.get("currentTopic") or "当前问题"
        anchor = answer[:18] if answer else "你的方案"
        persona_lines = {
            "master-strategist": f"围绕“{topic}”，你提到“{anchor}”。若局势突变，你先稳哪一路、谁来执行、谁来背责？",
            "queen-of-order": f"你说“{anchor}”。若下属当场不服令，如何不失威信地把“{topic}”压进执行？",
            "detective-kid": f"围绕“{topic}”，把“{anchor}”补成证据链：线索、验证、反证各是什么？",
            "jackeylove": f"把“{anchor}”讲成下路语音：先报信息、再报动作、最后谁来兜底？",
            "song-jiang": f"围绕“{topic}”，你先安谁的心、先定谁的责、再怎么让众人服？",
            "sun-wukong": f"若“{anchor}”是障眼法，你先试哪一下、再怎么变招，才能把“{topic}”破开？",
            "donald-trump": f"你提到“{anchor}”。这在谈判桌上是势还是筹码？怎么逼出对方回应？",
        }
        return persona_lines.get(interviewer_id, f"围绕“{topic}”，请补充失败预案与执行人分工。")

    def _build_hint(self, session: dict[str, Any]) -> str:
        directions = [str(item) for item in session.get("currentHintDirections", []) if str(item).strip()]
        interviewer_id = str(session["interviewer"].get("id") or "")
        topic = str(session.get("currentTopic") or "这题").strip()
        answer = self._latest_candidate_text(session)
        anchor = self._answer_anchor(answer)
        focus = directions[0] if directions else ""
        variants_by_persona = {
            "master-strategist": [
                f"你刚才提到“{anchor}”，但我还没听到你怎么把{topic}真正排进局里。别铺太大，顺着你最先动的那一步往下说。",
                f"先别把话说满。围绕“{focus or topic}”补一句：你到底先稳什么、动谁、怎么防局势反噬？",
            ],
            "queen-of-order": [
                f"你这段里态度有了，但“{focus or topic}”还没落到掌控上。我想听你怎么定规则、压分歧、让人照着执行。",
                f"别急着讲大道理，顺着“{anchor}”往下说清楚：真到现场有人不服，你怎么把{topic}压进秩序里？",
            ],
            "detective-kid": [
                f"你先别急着下结论。围绕“{anchor}”补一口证据链给我听，尤其是你拿什么验证“{focus or topic}”。",
                f"我现在听到的是判断，还没听到你怎么证明。顺着“{focus or topic}”说说，哪条线索最先让你确认方向？",
            ],
            "jackeylove": [
                f"你这波像在报想法，还不像在打配合。围绕“{focus or topic}”说清楚，你先给什么信号、队友怎么接、谁来兜底。",
                f"别只说能打。你刚才那句“{anchor}”落地以后，下路语音里第一句会怎么报？",
            ],
            "song-jiang": [
                f"这话能听，但还没把人心和分工拢住。顺着“{focus or topic}”说，你先安谁、先定谁、再怎么让大家服气。",
                f"别只讲义气，讲安排。围绕“{anchor}”补一句：真要你来扛这摊子，第一步你会先稳住哪拨人？",
            ],
            "sun-wukong": [
                f"别绕，直接说破局手。围绕“{focus or topic}”讲你先试哪一下，不成再怎么变招。",
                f"你刚才那句“{anchor}”像个念头，还不像招。给我补清楚：真撞上硬仗，你第一反应怎么动？",
            ],
            "donald-trump": [
                f"这段有气势，但筹码还没亮出来。顺着“{focus or topic}”说，你拿什么逼对面给反应？",
                f"别只说你会谈。围绕“{anchor}”补清楚，这件事里你的 leverage 到底是什么，怎么把场子带回你手里？",
            ],
        }
        variants = variants_by_persona.get(
            interviewer_id,
            [
                f"你刚才这段还差一点落地。别改成分点背稿，顺着“{focus or topic}”往下说清楚你会怎么做。",
                f"我现在听到的是方向，还没听到现场动作。围绕“{anchor}”补一句：真轮到你拍板，第一步怎么落？",
            ],
        )
        for variant in variants:
            if not self._hint_seen(session, variant):
                return variant
        return variants[-1]

    def _pick_question(self, interviewer: dict[str, Any], used: list[str]) -> dict[str, Any]:
        bank = interviewer.get("question_bank") or []
        if not bank:
            return {"q": "请介绍你在该岗位里最关键的一次决策。", "topic": "岗位决策", "hint_directions": ["背景", "动作", "结果"]}

        used_set = set(str(item) for item in used)
        unused = [item for item in bank if str(item.get("q") or "") not in used_set]
        pool = unused or bank
        picked = random.choice(pool)
        return {
            "q": str(picked.get("q") or "请介绍你在该岗位里最关键的一次决策。"),
            "topic": str(picked.get("topic") or "岗位决策"),
            "hint_directions": [str(token) for token in (picked.get("hint_directions") or []) if str(token).strip()],
        }

    def _drill_prob(self, session: dict[str, Any]) -> float:
        table = session["interviewer"].get("drill_probability", [0.7, 0.45, 0.25])
        depth = max(0, min(2, int(session.get("drillDepth", 0))))
        try:
            return float(table[depth])
        except Exception:  # noqa: BLE001
            return 0.3

    def _timeout_line(self, session: dict[str, Any]) -> str:
        table = {
            "master-strategist": "时机已过。这题按你未及时下令处理。",
            "queen-of-order": "时间到了。临场若迟疑，秩序就会先散。",
            "detective-kid": "时间到。证据链没补全，这题先记疑点。",
            "jackeylove": "时间到了。这波你信息没报清，我只能当你没跟上。",
            "song-jiang": "时间到了。聚义堂里拿不出安排，人心会先散。",
            "sun-wukong": "时间到了。妖风不会等你慢慢想。",
            "donald-trump": "Time's up. If the room moves before you do, you lose control.",
        }
        return table.get(str(session["interviewer"].get("id") or ""), "时间到了。本轮按超时处理。")

    def _current_session_score(self, session: dict[str, Any]) -> int:
        scores = session["roundScores"]
        if not scores:
            return int(session["roundScore"])
        values = [int(item["score"]) for item in scores]
        if session.get("currentPhase") == "awaiting_answer":
            values.append(int(session["roundScore"]))
        return int(round(sum(values) / len(values)))

    def _session(self, session_id: Any) -> dict[str, Any]:
        key = str(session_id or "").strip()
        if not key or key not in self.sessions:
            raise ValueError("会话不存在或已过期。")
        return self.sessions[key]

    def _difficulty(self, value: Any) -> dict[str, Any]:
        key = str(value or "normal").strip()
        return DIFFICULTIES.get(key, DIFFICULTIES["normal"])

    def _latest_candidate_text(self, session: dict[str, Any]) -> str:
        for item in reversed(session.get("transcript", [])):
            if item.get("speaker") == "candidate":
                return str(item.get("text") or "").strip()
        return ""

    def _answer_anchor(self, text: str) -> str:
        compact = " ".join(str(text or "").split())
        return compact[:16] if compact else "你刚才的说法"

    def _hint_seen(self, session: dict[str, Any], hint: str) -> bool:
        normalized_hint = self._normalize_free_text(hint)
        if not normalized_hint:
            return False
        return normalized_hint in {
            self._normalize_free_text(item)
            for item in session.get("hintHistory", [])
            if str(item).strip()
        }

    def _normalize_free_text(self, text: str) -> str:
        return "".join(ch.lower() for ch in str(text or "") if ch.isalnum())
