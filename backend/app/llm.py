"""
与 LLM（OpenAI 兼容接口）交互的最小封装。

约定：
- 读取 `config.json` 中对应模型的 `api_key` 与 `base_url`。
- 当 api_key 为空时进入“演示模式”，避免本地首次启动就因为未配置密钥而报错。
"""

import httpx

from app.config import settings


async def complete_chat(messages: list[dict[str, str]], model: str | None = None) -> str:
    """
    调用 OpenAI 兼容 API 获取模型回复。

    参数:
        messages: 消息列表，格式 [{role, content}, ...]
        model:    本次请求使用的模型名称；为 None 时使用配置中的默认模型
    """
    # 前端可传入模型名；若为空/全空白则回退到后端默认模型。
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

    # 使用 OpenAI Chat Completions 兼容协议。
    payload = {
        "model": effective_model,
        "messages": messages,
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    # 120s 为保守超时：避免长输出/慢模型导致前端一直等待无反馈。
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            json=payload,
            headers=headers,
        )
        r.raise_for_status()
        data = r.json()
    return data["choices"][0]["message"]["content"].strip()
