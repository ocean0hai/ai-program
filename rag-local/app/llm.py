from __future__ import annotations

import httpx

from app.config_runtime import resolve_llm
from app.settings import settings


async def chat(*, system: str, user: str, llm_model: str | None = None) -> str:
    """
    运行时选择本地 LLM：
    - 优先读取仓库根目录 config.json 的 rag_local.llm_models
    - 支持通过 llm_model 指定具体模型 name
    - 若未配置，则回退到 .env 的 ollama_base_url / ollama_model
    """
    resolved = resolve_llm(llm_model)
    provider = (resolved.provider if resolved else "ollama").lower()

    if provider != "ollama":
        raise ValueError(f"暂不支持的 provider: {provider}")

    base_url = (resolved.base_url if resolved else None) or settings.ollama_base_url
    model = (resolved.model if resolved else None) or settings.ollama_model

    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False,
        "options": {"temperature": 0.2},
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{base_url.rstrip('/')}/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
    msg = (data.get("message") or {}).get("content") or ""
    return str(msg).strip()

