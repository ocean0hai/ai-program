from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import chromadb

from app.settings import settings


@dataclass(frozen=True)
class Retrieved:
    text: str
    source: str | None
    score: float | None


def _client() -> chromadb.PersistentClient:
    # Chroma 使用本地持久化目录；目录不存在时创建。
    os.makedirs(settings.chroma_dir, exist_ok=True)
    return chromadb.PersistentClient(path=settings.chroma_dir)


def get_collection(name: str):
    c = _client()
    # 使用 cosine 空间：在 embedding 做了 normalize 后，cosine 距离/相似度更稳定。
    return c.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def upsert_chunks(
    *,
    collection: str,
    ids: list[str],
    texts: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict[str, Any]],
) -> int:
    col = get_collection(collection)
    col.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
    return len(ids)


def query(
    *,
    collection: str,
    query_embedding: list[float],
    top_k: int,
) -> list[Retrieved]:
    col = get_collection(collection)
    res = col.query(query_embeddings=[query_embedding], n_results=top_k, include=["documents", "metadatas", "distances"])

    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    out: list[Retrieved] = []
    for i in range(min(len(docs), len(metas), len(dists))):
        md = metas[i] or {}
        # 注意：Chroma 返回的 `distances` 在 cosine 空间下通常是“距离”（越小越相近），
        # 并非传统意义上“越大越好”的 score。这里原样返回，方便你前端/上层自行解释。
        out.append(
            Retrieved(
                text=str(docs[i]),
                source=md.get("source"),
                score=float(dists[i]) if dists[i] is not None else None,
            )
        )
    return out

