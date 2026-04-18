from __future__ import annotations

import base64
import json
import os
import time
import uuid
from typing import Any
from urllib import error, request


class TTSClientError(RuntimeError):
    pass


def configured() -> bool:
    return bool(os.getenv("VOLC_TTS_API_KEY", "").strip() and os.getenv("VOLC_TTS_SPEAKER", "").strip())


def synthesize_mp3_v3(text: str) -> bytes:
    """Volcengine OpenSpeech TTS v3 (HTTP Chunked) -> return full audio bytes (mp3 by default)."""

    api_key = os.getenv("VOLC_TTS_API_KEY", "").strip()
    resource_id = os.getenv("VOLC_TTS_RESOURCE_ID", "seed-tts-2.0").strip() or "seed-tts-2.0"
    speaker = os.getenv("VOLC_TTS_SPEAKER", "").strip()
    fmt = (os.getenv("VOLC_TTS_FORMAT", "mp3").strip() or "mp3").lower()
    sample_rate = int(os.getenv("VOLC_TTS_SAMPLE_RATE", "24000").strip() or "24000")

    if not api_key:
        raise TTSClientError("Missing VOLC_TTS_API_KEY.")
    if not speaker:
        raise TTSClientError("Missing VOLC_TTS_SPEAKER.")

    clean = (text or "").strip()
    if not clean:
        raise TTSClientError("Text is empty.")
    # Doc suggests 1024 bytes utf-8, keep it conservative.
    if len(clean.encode("utf-8")) > 1024:
        raise TTSClientError("Text too long for TTS (exceeds 1024 bytes).")

    url = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Request-Id": str(uuid.uuid4()),
    }

    payload: dict[str, Any] = {
        "user": {"uid": "ai-game"},
        "req_params": {
            "text": clean,
            "speaker": speaker,
            "audio_params": {
                "format": fmt,
                "sample_rate": sample_rate,
            },
            # small QoL: read markdown more naturally
            "additions": json.dumps({"disable_markdown_filter": True}),
        },
    }

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(url=url, data=body, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=60) as resp:
            return _read_chunked_tts_response(resp)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise TTSClientError(f"TTS HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise TTSClientError(f"TTS network error: {exc.reason}") from exc


def _read_chunked_tts_response(resp) -> bytes:
    """Parse chunked stream of JSON objects; concatenate base64 audio frames."""

    out = bytearray()
    buf = ""
    last_data_at = time.time()

    # The response is chunked; each chunk is JSON (often delimited by newlines).
    # We'll incrementally decode utf-8 and scan for complete JSON objects.
    decoder = None
    try:
        import codecs

        decoder = codecs.getincrementaldecoder("utf-8")()
    except Exception:  # noqa: BLE001
        decoder = None

    while True:
        chunk = resp.read(4096)
        if not chunk:
            break

        last_data_at = time.time()

        if decoder:
            buf += decoder.decode(chunk)
        else:
            buf += chunk.decode("utf-8", errors="ignore")

        # Fast-path: split by newlines; try parse line-by-line
        lines = buf.splitlines(keepends=False)
        if not lines:
            continue

        # Keep last partial line in buf
        if buf and not buf.endswith("\n") and not buf.endswith("\r"):
            buf = lines[-1]
            lines = lines[:-1]
        else:
            buf = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                # If the server doesn't strictly newline-delimit JSON objects,
                # fall back to accumulating in buf and keep going.
                buf = (buf + "\n" + line) if buf else line
                continue

            code = obj.get("code")
            if isinstance(code, int) and code not in (0, 20000000):
                raise TTSClientError(f"TTS error code={code}, message={obj.get('message')}")

            data = obj.get("data")
            if isinstance(data, str) and data:
                try:
                    out.extend(base64.b64decode(data))
                except Exception:  # noqa: BLE001
                    pass

            if code == 20000000:
                return bytes(out)

        # Avoid hanging forever if stream stalls
        if time.time() - last_data_at > 55:
            break

    if not out:
        raise TTSClientError("TTS returned empty audio.")
    return bytes(out)

