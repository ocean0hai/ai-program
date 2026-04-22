from __future__ import annotations

"""
运行时配置读取（根目录 config.json）。

为什么要单独做一层 runtime config：
- 你希望“随时切换本地模型”，这属于运行时开关，适合放在仓库统一配置 `config.json`
- 但 `rag-local/.env` 仍可作为兜底（例如仅运行子目录、不带根配置时）

约定：
- 根目录 `config.json` 的 `rag_local.llm_models` 用于声明可选 LLM
- 请求里传 `llm_model`（即 name）可覆盖默认值
"""

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
    # 这里通过当前文件路径定位仓库根目录，避免依赖工作目录（cwd）。
    # rag-local/app -> rag-local -> repo root
    return Path(__file__).resolve().parents[2]


def load_repo_config() -> dict[str, Any]:
    """读取仓库根目录的 `config.json`，不存在则返回空 dict。"""
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
    """列出 `config.json -> rag_local.llm_models` 中声明的 LLM。"""
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
    """
    解析最终使用的 LLM：
    - 若传入 name，则优先按 name 精确匹配
    - 否则使用 rag_local.default_llm
    - 再否则返回列表中的第一个
    """
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

