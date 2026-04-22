from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LlmConfig:
    name: str
    provider: str
    base_url: str | None
    model: str | None


def _repo_root_from_here() -> Path:
    # rag-local/app -> rag-local -> repo root
    return Path(__file__).resolve().parents[2]


def load_repo_config() -> dict[str, Any]:
    cfg_path = _repo_root_from_here() / "config.json"
    if not cfg_path.exists():
        return {}
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def rag_section() -> dict[str, Any]:
    cfg = load_repo_config()
    return (cfg.get("rag_local") or {}) if isinstance(cfg, dict) else {}


def get_default_llm_name() -> str | None:
    rag = rag_section()
    name = rag.get("default_llm")
    return str(name) if name else None


def list_llms() -> list[LlmConfig]:
    rag = rag_section()
    items = rag.get("llm_models") or []
    out: list[LlmConfig] = []
    if not isinstance(items, list):
        return out
    for x in items:
        if not isinstance(x, dict):
            continue
        out.append(
            LlmConfig(
                name=str(x.get("name") or ""),
                provider=str(x.get("provider") or ""),
                base_url=str(x.get("base_url") or "") or None,
                model=str(x.get("model") or "") or None,
            )
        )
    return [o for o in out if o.name and o.provider]


def resolve_llm(name: str | None) -> LlmConfig | None:
    llms = list_llms()
    if not llms:
        return None

    if name:
        for l in llms:
            if l.name == name:
                return l

    default_name = get_default_llm_name()
    if default_name:
        for l in llms:
            if l.name == default_name:
                return l

    for l in llms:
        if l.name:
            return l
    return None

