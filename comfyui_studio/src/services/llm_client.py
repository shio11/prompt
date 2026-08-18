"""LLM(Qwen3.8など)との通信を抽象化するインターフェースと実装。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

import requests

from models.chat import ChatMessage


class LLMClient(ABC):
    """チャット補完を行うLLMクライアントの抽象基底クラス。"""

    @abstractmethod
    def complete_chat(self, messages: List[ChatMessage]) -> str:
        """メッセージ履歴を渡し、アシスタントの返信テキストを取得する。"""


class LLMRequestError(RuntimeError):
    """LLMサーバーとの通信に失敗した場合に送出する例外。"""


class OllamaLLMClient(LLMClient):
    """Ollama経由でQwen3.8モデルと通信するクライアント。"""

    def __init__(self, base_url: str, model_name: str, timeout_sec: float = 120.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._timeout_sec = timeout_sec

    def complete_chat(self, messages: List[ChatMessage]) -> str:
        payload = {
            "model": self._model_name,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "stream": False,
        }
        response = requests.post(f"{self._base_url}/api/chat", json=payload, timeout=self._timeout_sec)
        if response.status_code != 200:
            raise LLMRequestError(
                f"Ollamaへのリクエストに失敗しました: {response.status_code} {response.text}"
            )
        data = response.json()
        content = data.get("message", {}).get("content")
        if not content:
            raise LLMRequestError(f"Ollamaから応答内容を取得できませんでした: {data}")
        return str(content)
