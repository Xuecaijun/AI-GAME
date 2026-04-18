from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib import error, request

from .prompts import (
    build_code_judge_prompts,
    build_code_question_prompts,
    build_hint_prompts,
    build_judge_prompts,
    build_offer_prompts,
    build_opening_prompts,
    build_question_prompts,
    build_resume_profile_prompts,
    build_summary_prompts,
)


class AIClientError(RuntimeError):
    pass


_DEFAULT_OPENROUTER_BASE = "https://openrouter.ai/api/v1"
_DEFAULT_OPENROUTER_MODEL = "z-ai/glm-5.1"


class AIClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip() or os.getenv("OPENROUTER_API_KEY", "").strip()
        self.base_url = os.getenv("OPENAI_BASE_URL", _DEFAULT_OPENROUTER_BASE).rstrip("/")
        self.model = os.getenv("OPENAI_MODEL", _DEFAULT_OPENROUTER_MODEL).strip()
        self.force_mock = os.getenv("AI_GAME_FORCE_MOCK", "0").strip() == "1"

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model) and not self.force_mock

    def runtime_status(self) -> dict[str, Any]:
        if self.force_mock:
            return {"mode": "mock", "reason": "AI_GAME_FORCE_MOCK=1"}
        if self.configured:
            return {"mode": "llm", "reason": f"已配置模型 {self.model}"}
        return {"mode": "mock", "reason": "未检测到 OPENAI_API_KEY / OPENROUTER_API_KEY（OpenRouter 密钥）或未配置模型"}

    def parse_resume(self, context: dict[str, Any]) -> dict[str, Any]:
        system_prompt, user_prompt = build_resume_profile_prompts(
            str(context.get("resumeText", "")),
            context.get("role") or {},
            str(context.get("themeKeyword", "")),
        )
        return self._chat_json(system_prompt, user_prompt, temperature=0.3)

    def generate_opening(self, context: dict[str, Any]) -> dict[str, Any]:
        system_prompt, user_prompt = build_opening_prompts(context)
        return self._chat_json(system_prompt, user_prompt, temperature=0.9)

    def generate_question(self, context: dict[str, Any]) -> dict[str, Any]:
        system_prompt, user_prompt = build_question_prompts(context)
        return self._chat_json(system_prompt, user_prompt, temperature=0.85)

    def judge_answer(self, context: dict[str, Any], answer: str) -> dict[str, Any]:
        system_prompt, user_prompt = build_judge_prompts(context, answer)
        return self._chat_json(system_prompt, user_prompt, temperature=0.55)

    def generate_hint(self, context: dict[str, Any]) -> dict[str, Any]:
        system_prompt, user_prompt = build_hint_prompts(context)
        return self._chat_json(system_prompt, user_prompt, temperature=0.7)

    def generate_code_question(self, context: dict[str, Any]) -> dict[str, Any]:
        system_prompt, user_prompt = build_code_question_prompts(context)
        return self._chat_json(system_prompt, user_prompt, temperature=0.85)

    def judge_code_answer(self, context: dict[str, Any], code: str) -> dict[str, Any]:
        system_prompt, user_prompt = build_code_judge_prompts(context, code)
        return self._chat_json(system_prompt, user_prompt, temperature=0.5)

    def summarize_session(self, context: dict[str, Any]) -> dict[str, Any]:
        system_prompt, user_prompt = build_summary_prompts(context)
        return self._chat_json(system_prompt, user_prompt, temperature=0.8)

    def build_offer_letter(self, context: dict[str, Any]) -> dict[str, Any]:
        system_prompt, user_prompt = build_offer_prompts(context)
        return self._chat_json(system_prompt, user_prompt, temperature=0.9)

    def _chat_json(self, system_prompt: str, user_prompt: str, temperature: float) -> dict[str, Any]:
        if not self.configured:
            raise AIClientError("AI client is not configured.")

        payload = {
            "model": self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        body = json.dumps(payload).encode("utf-8")
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        referer = os.getenv("OPENROUTER_HTTP_REFERER", "").strip()
        if referer:
            headers["HTTP-Referer"] = referer
        app_title = os.getenv("OPENROUTER_X_TITLE", "").strip()
        if app_title:
            headers["X-Title"] = app_title

        req = request.Request(
            url=f"{self.base_url}/chat/completions",
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=45) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise AIClientError(f"HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise AIClientError(f"Network error: {exc.reason}") from exc

        try:
            parsed = json.loads(raw)
            content = self._extract_content(parsed)
            return self._load_json_content(content)
        except (KeyError, ValueError, TypeError) as exc:
            raise AIClientError(f"Unable to parse AI response: {raw[:300]}") from exc

    def _extract_content(self, payload: dict[str, Any]) -> str:
        message = payload["choices"][0]["message"]["content"]
        if isinstance(message, str):
            return message
        if isinstance(message, list):
            text_parts = []
            for item in message:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            return "\n".join(text_parts)
        raise AIClientError("Unsupported message content format.")

    def _load_json_content(self, content: str) -> dict[str, Any]:
        content = content.strip()
        if content.startswith("{"):
            return json.loads(content)

        fenced_match = re.search(r"\{.*\}", content, re.DOTALL)
        if fenced_match:
            return json.loads(fenced_match.group(0))

        raise AIClientError(f"Model did not return JSON: {content[:200]}")
