from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_dir: str = "./data/chroma"

    # 兜底配置：当 config.json 未提供 llm_models 时使用
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b-instruct"

    top_k_default: int = 5
    chunk_size: int = 900
    chunk_overlap: int = 150


settings = Settings()

