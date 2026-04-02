import httpx

from app.config import settings


async def complete_chat(messages: list[dict[str, str]], model: str | None = None) -> str:
    """
    调用 OpenAI 兼容 API 获取模型回复。

    参数:
        messages: 消息列表，格式 [{role, content}, ...]
        model:    本次请求使用的模型名称；为 None 时使用配置中的默认模型
    """
    effective_model = (model or "").strip() or settings.openai_model
    model_cfg = settings.get_model_config(effective_model)
    api_key = model_cfg["api_key"]
    base_url = model_cfg["base_url"]

    # 未配置 API Key 时进入演示模式，直接返回提示文字
    if not api_key:
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return (
            f"[演示模式] 模型 \"{effective_model}\" 未配置 api_key。你的消息：\n"
            f"「{last_user[:500]}{'…' if len(last_user) > 500 else ''}」\n\n"
            "在 config.json 中为该模型设置 api_key 后即可调用真实模型。"
        )

    payload = {
        "model": effective_model,
        "messages": messages,
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            json=payload,
            headers=headers,
        )
        r.raise_for_status()
        data = r.json()
    return data["choices"][0]["message"]["content"].strip()
