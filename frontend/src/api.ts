// 开发环境下通过 Vite 代理转发请求，生产环境可通过 VITE_API_BASE 指定后端地址
const base = import.meta.env.DEV ? "" : (import.meta.env.VITE_API_BASE ?? "");

export type Message = {
  id: number;
  role: string;
  content: string;
  created_at: string;
};

export type Session = {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
};

export type Meta = {
  model: string;       // 服务端默认模型
  base_url: string;    // LLM 接口地址
  models: string[];    // 前端可选的模型列表
};

export async function listSessions(): Promise<Session[]> {
  const r = await fetch(`${base}/api/sessions`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getMeta(): Promise<Meta> {
  const r = await fetch(`${base}/api/meta`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function createSession(): Promise<Session> {
  const r = await fetch(`${base}/api/sessions`, { method: "POST" });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getMessages(sessionId: string): Promise<Message[]> {
  const r = await fetch(`${base}/api/sessions/${sessionId}/messages`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

/**
 * 发送消息并获取模型回复。
 * @param message   用户输入文本
 * @param sessionId 当前会话 ID，null 时后端自动创建新会话
 * @param model     本次使用的模型名称，null 时使用服务端默认模型
 */
export async function sendChat(
  message: string,
  sessionId: string | null,
  model: string | null = null,
): Promise<{ session_id: string; reply: string; messages: Message[] }> {
  const r = await fetch(`${base}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId, model }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const r = await fetch(`${base}/api/sessions/${sessionId}`, { method: "DELETE" });
  if (!r.ok) throw new Error(await r.text());
}
