const axios = require("axios");
const { openaiApiKey, openaiBaseUrl, openaiModel } = require("./config");

async function completeChat(messages) {
  if (!openaiApiKey) {
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    const text = lastUser ? lastUser.content : "";
    const short = text.length > 500 ? `${text.slice(0, 500)}...` : text;
    return `[演示模式] 未配置 OPENAI_API_KEY。你的消息：\n「${short}」\n\n在 backend-node/.env 中设置 OPENAI_API_KEY 后即可调用真实模型。`;
  }

  const resp = await axios.post(
    `${openaiBaseUrl.replace(/\/$/, "")}/chat/completions`,
    {
      model: openaiModel,
      messages,
      temperature: 0.7,
    },
    {
      timeout: 120000,
      headers: {
        Authorization: `Bearer ${openaiApiKey}`,
        "Content-Type": "application/json",
      },
    }
  );

  const content = resp?.data?.choices?.[0]?.message?.content;
  console.log("resp.data", resp.data);
  return typeof content === "string" ? content.trim() : "";
}

module.exports = { completeChat };
