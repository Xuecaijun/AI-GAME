from __future__ import annotations

import importlib
from io import BytesIO


def extract_text(filename: str, raw_bytes: bytes) -> str:
    suffix = _suffix_of(filename)

    if suffix == ".pdf":
        return _extract_pdf(raw_bytes)
    if suffix == ".docx":
        return _extract_docx(raw_bytes)
    if suffix in {".txt", ".md"}:
        return _extract_text_file(raw_bytes)

    raise ValueError("暂不支持该格式")


def _suffix_of(filename: str) -> str:
    cleaned = (filename or "").strip().lower()
    if "." not in cleaned:
        raise ValueError("暂不支持该格式")
    return cleaned[cleaned.rfind(".") :]


def _extract_pdf(raw_bytes: bytes) -> str:
    importlib.invalidate_caches()
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - import error depends on env
        raise ValueError("PDF 解析依赖未安装") from exc

    try:
        reader = PdfReader(BytesIO(raw_bytes))
        text = "\n".join((page.extract_text() or "").strip() for page in reader.pages)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("PDF 解析失败") from exc

    return _ensure_text(text)


def _extract_docx(raw_bytes: bytes) -> str:
    importlib.invalidate_caches()
    try:
        from docx import Document
    except ImportError as exc:  # pragma: no cover - import error depends on env
        raise ValueError("DOCX 解析依赖未安装") from exc

    try:
        document = Document(BytesIO(raw_bytes))
        text = "\n".join(paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip())
    except Exception as exc:  # noqa: BLE001
        raise ValueError("DOCX 解析失败") from exc

    return _ensure_text(text)


def _extract_text_file(raw_bytes: bytes) -> str:
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("文本文件需为 UTF-8 编码") from exc
    return _ensure_text(text)


def _ensure_text(text: str) -> str:
    normalized = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if not normalized:
        raise ValueError("文件里没有解析出可用文字")
    return normalized
