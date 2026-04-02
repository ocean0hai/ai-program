import httpx

from app.config import settings


async def complete_chat(messages: list[dict[str, str]]) -> str:
    """messages: [{role, content}, ...]"""
    if not settings.openai_api_key:
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return (
            "[演示模式] 未配置 OPENAI_API_KEY。你的消息：\n"
            f"「{last_user[:500]}{'…' if len(last_user) > 500 else ''}」\n\n"
            "在 backend/.env 中设置 OPENAI_API_KEY 后即可调用真实模型。"
        )

    payload = {
        "model": settings.openai_model,
        "messages": messages,
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{settings.openai_base_url.rstrip('/')}/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
    return data["choices"][0]["message"]["content"].strip()
