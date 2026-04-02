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

os.makedirs("data", exist_ok=True)

app = FastAPI(title="Chat Memory API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/meta")
def meta():
    return {"model": settings.openai_model, "base_url": settings.openai_base_url}


@app.get("/api/sessions", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db), limit: int = 50):
    rows = db.scalars(
        select(models.Session).order_by(models.Session.updated_at.desc()).limit(min(limit, 100))
    ).all()
    return rows


@app.post("/api/sessions", response_model=SessionOut)
def create_session(db: Session = Depends(get_db)):
    s = models.Session(title="新对话")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@app.get("/api/sessions/{session_id}/messages", response_model=list[MessageOut])
def get_messages(session_id: str, db: Session = Depends(get_db)):
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
    s = db.get(models.Session, session_id)
    if not s:
        raise HTTPException(404, "会话不存在")
    db.delete(s)
    db.commit()
    return {"ok": True}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, db: Session = Depends(get_db)):
    text = body.message.strip()
    if not text:
        raise HTTPException(400, "消息不能为空")

    if body.session_id:
        sess = db.get(models.Session, body.session_id)
        if not sess:
            raise HTTPException(404, "会话不存在")
    else:
        sess = models.Session(title=text[:40] + ("…" if len(text) > 40 else ""))
        db.add(sess)
        db.flush()

    user_msg = models.Message(session_id=sess.id, role="user", content=text)
    db.add(user_msg)
    db.flush()

    recent = db.scalars(
        select(models.Message)
        .where(models.Message.session_id == sess.id)
        .order_by(models.Message.id.desc())
        .limit(settings.history_limit)
    ).all()
    recent = list(reversed(recent))

    llm_messages = [{"role": m.role, "content": m.content} for m in recent if m.role in ("user", "assistant", "system")]
    reply_text = await complete_chat(llm_messages)

    asst = models.Message(session_id=sess.id, role="assistant", content=reply_text)
    db.add(asst)
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
