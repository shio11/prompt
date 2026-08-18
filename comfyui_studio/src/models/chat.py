"""チャット関連のドメインモデル。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from models.enums import ChatRole


@dataclass(frozen=True)
class ChatMessage:
    """1件のチャットメッセージを表す不変の値オブジェクト。"""

    role: ChatRole
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("content は空にできません")


class ChatSession:
    """1つの相談セッションにおけるメッセージ履歴を管理するエンティティ。"""

    def __init__(self, session_id: Optional[str] = None) -> None:
        self.__id: str = session_id or str(uuid4())
        self.__messages: List[ChatMessage] = []

    @property
    def id(self) -> str:
        return self.__id

    @property
    def messages(self) -> List[ChatMessage]:
        return list(self.__messages)

    def add_message(self, message: ChatMessage) -> None:
        if not isinstance(message, ChatMessage):
            raise TypeError("message は ChatMessage である必要があります")
        self.__messages.append(message)

    def __repr__(self) -> str:
        return f"ChatSession(id={self.__id!r}, messages={len(self.__messages)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ChatSession):
            return NotImplemented
        return self.__id == other.id
