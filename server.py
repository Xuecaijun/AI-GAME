from __future__ import annotations

import base64
import json
import os
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from backend.engine import GameEngine
from backend.resume_parser import extract_text
from backend.tts_client import TTSClientError, configured as tts_configured, synthesize_mp3_v3


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
engine: GameEngine | None = None


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        # Always honor project .env values so stale shell variables
        # (including empty values) do not disable runtime features.
        os.environ[key.strip()] = value.strip()


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/bootstrap":
                self._send_json(engine.get_bootstrap())
                return
            if parsed.path == "/api/health":
                self._send_json({"ok": True, "runtime": engine.ai_client.runtime_status()})
                return
            if parsed.path == "/api/tts/status":
                self._send_json({"ok": True, "configured": bool(tts_configured())})
                return

            self.path = "/index.html" if parsed.path == "/" else parsed.path
            return super().do_GET()
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # noqa: BLE001
            self._send_json({"error": f"Server error: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self._read_json()
            if parsed.path == "/api/resume/mock":
                self._send_json(engine.generate_mock_resume(payload))
                return
            if parsed.path == "/api/resume/upload":
                self._send_json(_handle_resume_upload(payload))
                return
            if parsed.path == "/api/invitations":
                self._send_json(engine.build_invitations(payload))
                return
            if parsed.path == "/api/session/start":
                self._send_json(engine.start_session(payload))
                return
            if parsed.path == "/api/session/answer":
                self._send_json(engine.submit_answer(payload))
                return
            if parsed.path == "/api/session/timeout":
                self._send_json(engine.submit_timeout(payload))
                return
            if parsed.path == "/api/session/event":
                self._send_json(engine.submit_event(payload))
                return
            if parsed.path == "/api/tts":
                text = str(payload.get("text") or "").strip()
                preview = text.replace("\n", " ")[:40]
                started_at = time.perf_counter()
                print(f"[TTS] request text_len={len(text)} preview={preview!r}")
                audio = synthesize_mp3_v3(text)
                elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                print(f"[TTS] success bytes={len(audio)} elapsed_ms={elapsed_ms}")
                self._send_bytes(audio, content_type="audio/mpeg")
                return
            self._send_json({"error": "Not Found"}, status=HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except TTSClientError as exc:
            print(f"[TTS] failed error={exc}")
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # noqa: BLE001
            self._send_json({"error": f"Server error: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length).decode("utf-8")
        if not raw:
            return {}
        return json.loads(raw)

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=_json_default).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, payload: bytes, content_type: str, status: int = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)


def _json_default(value):
    if isinstance(value, set):
        return list(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _handle_resume_upload(payload: dict) -> dict[str, str]:
    filename = str(payload.get("filename") or "").strip()
    raw_base64 = str(payload.get("base64") or "").strip()
    if not filename or not raw_base64:
        raise ValueError("请上传文件内容。")

    if "," in raw_base64 and "base64" in raw_base64[:32].lower():
        raw_base64 = raw_base64.split(",", 1)[1]

    try:
        raw_bytes = base64.b64decode(raw_base64, validate=True)
    except ValueError as exc:
        raise ValueError("上传内容不是合法的 base64 数据。") from exc

    resume_text = extract_text(filename, raw_bytes)
    return {"resumeText": resume_text}


def main() -> None:
    load_env()
    global engine
    engine = GameEngine()
    port = int(os.getenv("PORT", "8765"))
    server = ThreadingHTTPServer(("127.0.0.1", port), AppHandler)
    print(f"终面：AI面试官 已启动 -> http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
