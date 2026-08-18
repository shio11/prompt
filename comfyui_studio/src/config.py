"""アプリケーション設定。環境変数から読み込む不変の設定値オブジェクト。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    comfyui_base_url: str = os.getenv("COMFYUI_BASE_URL", "http://127.0.0.1:8188")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    qwen_model_name: str = os.getenv("QWEN_MODEL_NAME", "qwen3:8b")
    db_path: str = os.getenv("DB_PATH", str(BASE_DIR / "data" / "jobs.db"))
    workflows_dir: str = os.getenv("WORKFLOWS_DIR", str(BASE_DIR / "workflows"))
    output_dir: str = os.getenv("OUTPUT_DIR", str(BASE_DIR / "data" / "outputs"))
    comfyui_poll_interval_sec: float = float(os.getenv("COMFYUI_POLL_INTERVAL_SEC", "1.0"))
    comfyui_timeout_sec: float = float(os.getenv("COMFYUI_TIMEOUT_SEC", "600.0"))


def get_settings() -> Settings:
    return Settings()
