import json
from pathlib import Path

# 从项目根目录的 config.json 读取配置
_config_path = Path(__file__).parent.parent.parent / "config.json"
_cfg: dict = json.loads(_config_path.read_text(encoding="utf-8"))

# 解析模型列表
_models: list[dict] = _cfg.get("models", [])
_default_model_obj: dict = next((m for m in _models if m.get("default")), _models[0] if _models else {})


class Settings:
    models: list[dict] = _models
    openai_model: str = _default_model_obj.get("name", "gpt-4o-mini")
    cors_origins: list[str] = _cfg.get("cors_origins", ["http://localhost:5173", "http://127.0.0.1:5173"])
    database_url: str = _cfg.get("database_url", "sqlite:///./data/chat_memory.db")
    history_limit: int = _cfg.get("history_limit", 30)

    def get_model_list(self) -> list[str]:
        """返回所有模型名称列表，默认模型置于首位。"""
        names = [m["name"] for m in self.models if m.get("name")]
        if not names:
            names = [self.openai_model]
        return names

    def get_model_config(self, name: str) -> dict:
        """按模型名查找 api_key 和 base_url，找不到时回退到默认模型。"""
        found = next((m for m in self.models if m.get("name") == name), _default_model_obj)
        return {
            "api_key": found.get("api_key", ""),
            "base_url": found.get("base_url", "https://api.openai.com/v1"),
        }


settings = Settings()
