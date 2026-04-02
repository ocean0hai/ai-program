import { useCallback, useEffect, useRef, useState } from "react";
import {
  createSession,
  deleteSession,
  getMeta,
  getMessages,
  listSessions,
  sendChat,
  type Meta,
  type Message,
  type Session,
} from "./api";
import "./App.css";
import MarkdownViewer from "./components/MarkdownViewer";
const STORAGE_KEY = "chat_session_id";
const SESSION_NOT_FOUND_TEXT = "会话不存在";

export default function App() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeId, setActiveId] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY));
  const [messages, setMessages] = useState<Message[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  // 当前选中的模型；null 表示使用服务端默认模型
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const refreshSessions = useCallback(async () => {
    const list = await listSessions();
    setSessions(list);
    return list;
  }, []);

  // 判断是否为"会话不存在"错误
  const isSessionNotFoundError = (e: unknown) => {
    return String(e).includes(SESSION_NOT_FOUND_TEXT);
  };

  // 初始加载会话列表
  useEffect(() => {
    refreshSessions().catch((e) => setErr(String(e)));
  }, [refreshSessions]);

  // 加载后端元信息（含可选模型列表），并将默认模型设为初始选中值
  useEffect(() => {
    getMeta()
      .then((m) => {
        setMeta(m);
        // 若尚未选择模型，默认使用服务端配置的模型
        setSelectedModel((prev) => prev ?? m.model);
      })
      .catch(() => setMeta(null));
  }, []);

  // 切换或加载会话时拉取消息列表
  useEffect(() => {
    if (!activeId) {
      setMessages([]);
      return;
    }
    localStorage.setItem(STORAGE_KEY, activeId);
    getMessages(activeId)
      .then(setMessages)
      .catch(async (e) => {
        if (isSessionNotFoundError(e)) {
          // 会话已被删除，清理本地状态
          setActiveId(null);
          localStorage.removeItem(STORAGE_KEY);
          setMessages([]);
          await refreshSessions();
          return;
        }
        setErr(String(e));
      });
  }, [activeId, refreshSessions]);

  const onNewChat = async () => {
    setErr(null);
    setLoading(true);
    try {
      const s = await createSession();
      await refreshSessions();
      setActiveId(s.id);
      setMessages([]);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  };

  const onSelect = (id: string) => {
    setErr(null);
    setActiveId(id);
  };

  const onDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("删除此会话？")) return;
    setErr(null);
    try {
      await deleteSession(id);
      if (activeId === id) {
        setActiveId(null);
        localStorage.removeItem(STORAGE_KEY);
        setMessages([]);
      }
      await refreshSessions();
    } catch (e) {
      setErr(String(e));
    }
  };

  const onSend = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setErr(null);
    setLoading(true);
    setInput("");
    try {
      // 将当前选中模型一并发送给后端；null 时后端使用默认模型
      const res = await sendChat(text, activeId, selectedModel);
      setActiveId(res.session_id);
      setMessages(res.messages);
      await refreshSessions();
    } catch (e) {
      if (isSessionNotFoundError(e)) {
        setActiveId(null);
        localStorage.removeItem(STORAGE_KEY);
        setMessages([]);
        setErr("当前会话不存在，已为你清理旧会话。请重新发送消息。");
        await refreshSessions();
        return;
      }
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  };

  // Enter 发送，Shift+Enter 换行
  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-head">
          <h1>对话记忆</h1>
          <button type="button" className="btn primary" onClick={onNewChat} disabled={loading}>
            新对话
          </button>
        </div>
        <ul className="session-list">
          {sessions.map((s) => (
            <li
              key={s.id}
              className={s.id === activeId ? "active" : ""}
              onClick={() => onSelect(s.id)}
            >
              <span className="title">{s.title || "未命名"}</span>
              <button
                type="button"
                className="btn-icon"
                title="删除"
                onClick={(e) => onDelete(s.id, e)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      </aside>
      <main className="chat">
        {/* 模型信息栏：显示当前选中模型，并提供下拉切换 */}
        {meta && (
          <div className="banner meta">
            <span className="meta-label">模型：</span>
            <select
              className="model-select"
              value={selectedModel ?? meta.model}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={loading}
            >
              {meta.models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
        )}
        {err && <div className="banner error">{err}</div>}
        <div className="messages">
          {messages.length === 0 && (
            <p className="hint">
              {activeId
                ? "暂无消息，输入下方开始对话。"
                : "选择左侧会话或点击「新对话」。"}
            </p>
          )}
          {messages.map((m) => (
            <div key={m.id} className={`bubble ${m.role}`}>
              <div className="role">{m.role === "user" ? "你" : "助手"}</div>
              {/* <div className="text">{m.content}</div> */}
              <MarkdownViewer content={m.content} />
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <div className="composer">
          <textarea
            rows={3}
            placeholder="输入消息，Enter 发送，Shift+Enter 换行"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            disabled={loading}
          />
          <button type="button" className="btn primary send" onClick={onSend} disabled={loading}>
            {loading ? "…" : "发送"}
          </button>
        </div>
      </main>
    </div>
  );
}
