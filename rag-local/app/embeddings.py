from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.settings import settings


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    # Embedding 模型加载通常较慢，这里全进程复用一个实例。
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    # normalize_embeddings=True：便于使用 cosine 空间进行检索，并减少数值尺度差异。
    vectors = _model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]

