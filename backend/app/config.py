"""
配置加载。

目前采用“单一 config.json”作为配置入口，便于在本地/演示环境快速切换模型与后端地址。
后续若需要上生产，建议改造为：环境变量 > 配置文件 的覆盖优先级，并避免把密钥提交到仓库。
"""

import json
from pathlib import Path

# 从项目根目录的 config.json 读取配置（以当前文件位置为锚点，避免工作目录变化导致找不到配置）。
_config_path = Path(__file__).parent.parent.parent / "config.json"
_cfg: dict = json.loads(_config_path.read_text(encoding="utf-8"))

# 解析模型列表：支持多模型配置，并允许标记一个 default 作为后端默认选择。
_models: list[dict] = _cfg.get("models", [])
_default_model_obj: dict = next((m for m in _models if m.get("default")), _models[0] if _models else {})


class Settings:
    """运行时配置的只读视图（从 config.json 解析得到）。"""
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
