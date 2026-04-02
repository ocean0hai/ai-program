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
  model: string;
  base_url: string;
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

export async function sendChat(
  message: string,
  sessionId: string | null
): Promise<{ session_id: string; reply: string; messages: Message[] }> {
  const r = await fetch(`${base}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const r = await fetch(`${base}/api/sessions/${sessionId}`, { method: "DELETE" });
  if (!r.ok) throw new Error(await r.text());
}
