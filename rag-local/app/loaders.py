from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


@dataclass(frozen=True)
class LoadedDoc:
    text: str
    source: str


def _read_txt_md(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        t = page.extract_text() or ""
        if t.strip():
            parts.append(t)
    return "\n\n".join(parts)


def _read_docx(path: Path) -> str:
    doc = DocxDocument(str(path))
    parts = [p.text for p in doc.paragraphs if (p.text or "").strip()]
    return "\n".join(parts)


def load_file(path: str | Path) -> LoadedDoc:
    """
    单文件加载器（最小实现）。

    约定：
    - `source` 保存文件路径（后续可替换为 URL、对象存储 key、数据库主键等）
    - 若文本为空直接报错，避免向量库里塞入大量空 chunk
    """
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(str(p))

    ext = p.suffix.lower()
    if ext in {".txt", ".md"}:
        text = _read_txt_md(p)
    elif ext == ".pdf":
        text = _read_pdf(p)
    elif ext == ".docx":
        text = _read_docx(p)
    else:
        raise ValueError(f"不支持的文件类型: {ext}")

    text = (text or "").strip()
    if not text:
        raise ValueError(f"文件内容为空: {p.name}")

    return LoadedDoc(text=text, source=str(p))


def load_folder(folder: str | Path) -> list[LoadedDoc]:
    f = Path(folder)
    if not f.exists() or not f.is_dir():
        raise FileNotFoundError(str(f))

    exts = {".txt", ".md", ".pdf", ".docx"}
    docs: list[LoadedDoc] = []
    for p in sorted(f.rglob("*")):
        if p.is_file() and p.suffix.lower() in exts:
            docs.append(load_file(p))
    return docs

