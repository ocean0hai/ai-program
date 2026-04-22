from __future__ import annotations

from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    collection: str
    added_chunks: int


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    collection: str = "default"
    top_k: int | None = None
    llm_model: str | None = None


class ContextChunk(BaseModel):
    text: str
    source: str | None = None
    score: float | None = None


class QueryResponse(BaseModel):
    answer: str
    contexts: list[ContextChunk]

