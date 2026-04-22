from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.embeddings import embed_texts
from app.loaders import LoadedDoc
from app.settings import settings
from app.splitter import split_text_recursive
from app.vectordb import Retrieved, query as vdb_query, upsert_chunks


@dataclass(frozen=True)
class IngestResult:
    added_chunks: int


def _make_id(source: str, chunk_index: int, text: str) -> str:
    h = hashlib.sha1(f"{source}::{chunk_index}::{text}".encode("utf-8", errors="ignore")).hexdigest()
    return h


def ingest_docs(*, docs: list[LoadedDoc], collection: str) -> IngestResult:
    chunks: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for d in docs:
        parts = split_text_recursive(d.text, chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
        for i, c in enumerate(parts):
            c = c.strip()
            if not c:
                continue
            ids.append(_make_id(d.source, i, c))
            chunks.append(c)
            metadatas.append({"source": d.source, "chunk_index": i})

    vectors = embed_texts(chunks)
    n = upsert_chunks(collection=collection, ids=ids, texts=chunks, embeddings=vectors, metadatas=metadatas)
    return IngestResult(added_chunks=n)


def retrieve(*, query_text: str, collection: str, top_k: int) -> list[Retrieved]:
    qv = embed_texts([query_text])[0]
    return vdb_query(collection=collection, query_embedding=qv, top_k=top_k)

