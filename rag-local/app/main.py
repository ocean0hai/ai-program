from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.llm import chat
from app.loaders import LoadedDoc, load_file
from app.prompts import SYSTEM_PROMPT, build_prompt
from app.rag import ingest_docs, retrieve
from app.schemas import ContextChunk, IngestResponse, QueryRequest, QueryResponse
from app.settings import settings

os.makedirs("data", exist_ok=True)

app = FastAPI(title="rag-local", version="0.1.0")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/ingest", response_model=IngestResponse)
async def api_ingest(
    collection: str = "default",
    files: list[UploadFile] = File(...),
):
    if not files:
        raise HTTPException(400, "请上传文件")

    tmp_dir = Path("./data/uploads")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    docs: list[LoadedDoc] = []
    for f in files:
        name = (f.filename or "upload").replace("\\", "_").replace("/", "_")
        p = tmp_dir / name
        content = await f.read()
        p.write_bytes(content)
        docs.append(load_file(p))

    result = ingest_docs(docs=docs, collection=collection)
    return IngestResponse(collection=collection, added_chunks=result.added_chunks)


@app.post("/api/query", response_model=QueryResponse)
async def api_query(body: QueryRequest):
    q = body.query.strip()
    if not q:
        raise HTTPException(400, "query 不能为空")

    top_k = body.top_k or settings.top_k_default
    hits = retrieve(query_text=q, collection=body.collection, top_k=top_k)

    contexts = [h.text for h in hits]
    prompt = build_prompt(q, contexts)
    answer = await chat(system=SYSTEM_PROMPT, user=prompt, llm_model=body.llm_model)

    return QueryResponse(
        answer=answer,
        contexts=[ContextChunk(text=h.text, source=h.source, score=h.score) for h in hits],
    )

