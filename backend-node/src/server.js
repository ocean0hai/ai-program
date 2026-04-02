const express = require("express");
const cors = require("cors");
const {
  port,
  corsOrigins,
  historyLimit,
  openaiBaseUrl,
  openaiModel,
  availableModels,
} = require("./config");
const {
  createSession,
  listSessions,
  getSessionById,
  getMessagesBySessionId,
  addMessage,
  updateSessionTitleIfNew,
  deleteSession,
} = require("./store");
const { completeChat } = require("./llm");

const app = express();
app.use(express.json({ limit: "1mb" }));
app.use(cors({ origin: corsOrigins, credentials: true }));

app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

app.get("/api/meta", (_req, res) => {
  // 返回默认模型、接口地址及前端可选的模型列表
  res.json({
    model: openaiModel,
    base_url: openaiBaseUrl,
    models: availableModels,
  });
});

app.get("/api/sessions", (req, res) => {
  const limit = Number(req.query.limit || 50);
  res.json(listSessions(limit));
});

app.post("/api/sessions", (_req, res) => {
  const session = createSession("新对话");
  res.json(session);
});

app.get("/api/sessions/:sessionId/messages", (req, res) => {
  const { sessionId } = req.params;
  const session = getSessionById(sessionId);
  if (!session) {
    return res.status(404).json({ detail: "会话不存在" });
  }
  return res.json(getMessagesBySessionId(sessionId));
});

app.delete("/api/sessions/:sessionId", (req, res) => {
  const { sessionId } = req.params;
  const ok = deleteSession(sessionId);
  if (!ok) {
    return res.status(404).json({ detail: "会话不存在" });
  }
  return res.json({ ok: true });
});

app.post("/api/chat", async (req, res) => {
  try {
    const text = String(req.body?.message || "").trim();
    if (!text) {
      return res.status(400).json({ detail: "消息不能为空" });
    }

    let sessionId = req.body?.session_id || null;
    let session = sessionId ? getSessionById(sessionId) : null;
    if (sessionId && !session) {
      return res.status(404).json({ detail: "会话不存在" });
    }

    if (!session) {
      const title = text.length > 40 ? `${text.slice(0, 40)}...` : text;
      session = createSession(title);
      sessionId = session.id;
    }

    addMessage(sessionId, "user", text);

    const history = getMessagesBySessionId(sessionId);
    const recent = history.slice(Math.max(0, history.length - historyLimit));
    const llmMessages = recent
      .filter((m) => ["user", "assistant", "system"].includes(m.role))
      .map((m) => ({ role: m.role, content: m.content }));

    // 将前端选择的模型（若有）传入 LLM 调用，覆盖服务端默认值
    const model = req.body?.model || null;
    const reply = await completeChat(llmMessages, model);
    addMessage(sessionId, "assistant", reply);

    updateSessionTitleIfNew(sessionId, text.length > 40 ? `${text.slice(0, 40)}...` : text);

    const messages = getMessagesBySessionId(sessionId);
    return res.json({ session_id: sessionId, reply, messages });
  } catch (error) {
    const message = error?.response?.data?.error?.message || error?.message || "服务异常";
    return res.status(500).json({ detail: message });
  }
});

app.listen(port, () => {
  console.log(`Node backend listening on http://127.0.0.1:${port}`);
});
