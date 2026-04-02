const fs = require("fs");
const { dataFile } = require("./config");

function nowIso() {
  return new Date().toISOString();
}

function defaultData() {
  return { sessions: [], messages: [] };
}

function ensureDataFile() {
  if (!fs.existsSync(dataFile)) {
    fs.writeFileSync(dataFile, JSON.stringify(defaultData(), null, 2), "utf8");
  }
}

function readData() {
  ensureDataFile();
  const raw = fs.readFileSync(dataFile, "utf8");
  try {
    const parsed = JSON.parse(raw || "{}");
    return {
      sessions: Array.isArray(parsed.sessions) ? parsed.sessions : [],
      messages: Array.isArray(parsed.messages) ? parsed.messages : [],
    };
  } catch {
    return defaultData();
  }
}

function writeData(data) {
  fs.writeFileSync(dataFile, JSON.stringify(data, null, 2), "utf8");
}

function createSession(title) {
  const data = readData();
  const ts = nowIso();
  const session = {
    id: require("uuid").v4(),
    title: title || "新对话",
    created_at: ts,
    updated_at: ts,
  };
  data.sessions.push(session);
  writeData(data);
  return session;
}

function listSessions(limit) {
  const data = readData();
  return [...data.sessions]
    .sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1))
    .slice(0, Math.min(limit || 50, 100));
}

function getSessionById(sessionId) {
  const data = readData();
  return data.sessions.find((s) => s.id === sessionId) || null;
}

function getMessagesBySessionId(sessionId) {
  const data = readData();
  return data.messages
    .filter((m) => m.session_id === sessionId)
    .sort((a, b) => a.id - b.id);
}

function addMessage(sessionId, role, content) {
  const data = readData();
  const nextId = data.messages.length > 0 ? data.messages[data.messages.length - 1].id + 1 : 1;
  const msg = {
    id: nextId,
    session_id: sessionId,
    role,
    content,
    created_at: nowIso(),
  };
  data.messages.push(msg);

  const session = data.sessions.find((s) => s.id === sessionId);
  if (session) {
    session.updated_at = nowIso();
  }

  writeData(data);
  return msg;
}

function updateSessionTitleIfNew(sessionId, title) {
  const data = readData();
  const session = data.sessions.find((s) => s.id === sessionId);
  if (!session) return;

  if (!session.title || session.title === "新对话") {
    session.title = title;
  }
  session.updated_at = nowIso();
  writeData(data);
}

function deleteSession(sessionId) {
  const data = readData();
  const existing = data.sessions.some((s) => s.id === sessionId);
  if (!existing) return false;

  data.sessions = data.sessions.filter((s) => s.id !== sessionId);
  data.messages = data.messages.filter((m) => m.session_id !== sessionId);
  writeData(data);
  return true;
}

module.exports = {
  createSession,
  listSessions,
  getSessionById,
  getMessagesBySessionId,
  addMessage,
  updateSessionTitleIfNew,
  deleteSession,
};
