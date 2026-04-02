const axios = require("axios");
const { openaiModel, getModelConfig } = require("./config");

/**
 * 调用 OpenAI 兼容接口获取模型回复。
 *
 * @param {Array<{role: string, content: string}>} messages - 对话历史
 * @param {string|null} model - 本次使用的模型名称；为空时使用配置默认值
 * @returns {Promise<string>} 模型回复文本
 */
async function completeChat(messages, model) {
  // 优先使用调用方指定的模型，否则回退到配置默认值
  const effectiveModel = (model || "").trim() || openaiModel;
  const { apiKey, baseUrl } = getModelConfig(effectiveModel);

  // 未配置 API Key 时进入演示模式
  if (!apiKey) {
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    const text = lastUser ? lastUser.content : "";
    const short = text.length > 500 ? `${text.slice(0, 500)}...` : text;
    return `[演示模式] 模型 "${effectiveModel}" 未配置 api_key。你的消息：\n「${short}」\n\n在 config.json 中为该模型设置 api_key 后即可调用真实模型。`;
  }

  const resp = await axios.post(
    `${baseUrl.replace(/\/$/, "")}/chat/completions`,
    {
      model: effectiveModel,
      messages,
      temperature: 0.7,
    },
    {
      timeout: 120000,
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
    }
  );

  const content = resp?.data?.choices?.[0]?.message?.content;
  console.log("resp.data", resp.data);
  return typeof content === "string" ? content.trim() : "";
}

module.exports = { completeChat };
