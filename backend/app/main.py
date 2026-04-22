"""
FastAPI 后端入口。

职责：
- 提供会话/消息的 CRUD 接口（持久化到数据库）。
- 提供 /api/chat：将会话上下文裁剪后转发给 LLM，并把回复写回会话历史。

说明：
- 本项目面向“聊天记忆/多轮对话”场景，因此会在每次对话时加载最近 N 条消息作为上下文。
"""

import os
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, init_db
from app import models
from app.llm import complete_chat
from app.schemas import ChatRequest, ChatResponse, MessageOut, SessionOut

# SQLite 默认落盘到 ./data 目录；此处确保目录存在，避免首次启动报错。
os.makedirs("data", exist_ok=True)

app = FastAPI(title="Chat Memory API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    """应用启动时初始化数据库（建表/连接准备等）。"""
    init_db()


@app.get("/health")
def health():
    """健康检查接口（用于部署探活/本地快速验证）。"""
    return {"ok": True}


@app.get("/api/meta")
def meta():
    """返回当前后端配置的模型信息及可用模型列表。"""
    return {
        "model": settings.openai_model,
        "base_url": settings.get_model_config(settings.openai_model)["base_url"],
        "models": settings.get_model_list(),
    }


@app.get("/api/sessions", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db), limit: int = 50):
    """按更新时间倒序列出会话，limit 做最大值保护避免一次拉取过多数据。"""
    rows = db.scalars(
        select(models.Session).order_by(models.Session.updated_at.desc()).limit(min(limit, 100))
    ).all()
    return rows


@app.post("/api/sessions", response_model=SessionOut)
def create_session(db: Session = Depends(get_db)):
    """显式新建会话（前端也可通过首次发言隐式创建）。"""
    s = models.Session(title="新对话")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@app.get("/api/sessions/{session_id}/messages", response_model=list[MessageOut])
def get_messages(session_id: str, db: Session = Depends(get_db)):
    """获取某个会话的消息列表（按 id 升序，便于前端按时间展示）。"""
    s = db.get(models.Session, session_id)
    if not s:
        raise HTTPException(404, "会话不存在")
    q = (
        select(models.Message)
        .where(models.Message.session_id == session_id)
        .order_by(models.Message.id.asc())
    )
    return db.scalars(q).all()


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """删除会话（通常会级联删除消息，取决于 ORM 关系配置）。"""
    s = db.get(models.Session, session_id)
    if not s:
        raise HTTPException(404, "会话不存在")
    db.delete(s)
    db.commit()
    return {"ok": True}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, db: Session = Depends(get_db)):
    """
    发送一条用户消息并返回模型回复。

    流程：
    - 若 session_id 为空：创建新会话（标题取首条消息的截断）。
    - 写入 user 消息。
    - 读取最近 history_limit 条消息作为上下文，调用 LLM。
    - 写入 assistant 消息，更新会话 updated_at。
    """
    text = body.message.strip()
    if not text:
        raise HTTPException(400, "消息不能为空")

    if body.session_id:
        sess = db.get(models.Session, body.session_id)
        if not sess:
            raise HTTPException(404, "会话不存在")
    else:
        # 首条消息隐式创建会话：标题用于会话列表展示，不追求完整语义。
        sess = models.Session(title=text[:40] + ("…" if len(text) > 40 else ""))
        db.add(sess)
        # flush 让 sess.id 在 commit 前可用（后续写 Message 需要外键 session_id）。
        db.flush()

    user_msg = models.Message(session_id=sess.id, role="user", content=text)
    db.add(user_msg)
    # 同理：让 user_msg.id 提前落到数据库（便于之后按 id 排序/截取）。
    db.flush()

    recent = db.scalars(
        select(models.Message)
        .where(models.Message.session_id == sess.id)
        .order_by(models.Message.id.desc())
        .limit(settings.history_limit)
    ).all()
    # recent 当前是“从新到旧”，为了符合 chat/completions 的对话顺序需要反转回“从旧到新”。
    recent = list(reversed(recent))

    llm_messages = [{"role": m.role, "content": m.content} for m in recent if m.role in ("user", "assistant", "system")]
    # 将前端选择的模型（若有）传入 LLM 调用，覆盖服务端默认值
    reply_text = await complete_chat(llm_messages, model=body.model)

    asst = models.Message(session_id=sess.id, role="assistant", content=reply_text)
    db.add(asst)
    # updated_at 用于会话列表排序；使用 UTC 便于跨时区一致性。
    sess.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(sess)

    all_msgs = db.scalars(
        select(models.Message)
        .where(models.Message.session_id == sess.id)
        .order_by(models.Message.id.asc())
    ).all()

    return ChatResponse(
        session_id=sess.id,
        reply=reply_text,
        messages=[MessageOut.model_validate(m) for m in all_msgs],
    )
