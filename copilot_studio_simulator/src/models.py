from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional, Tuple


class ModelType(Enum):
    """エージェントが応答生成に使用するモデルの種類"""

    GPT_4O = "gpt-4o"
    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-35-turbo"


class ActionType(Enum):
    """トピック内で実行されるアクションの種類"""

    SEND_MESSAGE = auto()
    CALL_API = auto()
    SET_VARIABLE = auto()
    END_CONVERSATION = auto()


class Speaker(Enum):
    """会話ターンの発話者"""

    USER = "user"
    AGENT = "agent"


@dataclass(frozen=True)
class TriggerPhrase:
    """トピックを起動するトリガーフレーズを表す値オブジェクト"""

    text: str

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise ValueError("トリガーフレーズは空にできません")

    def matches(self, user_input: str) -> bool:
        return self.text.strip().lower() in user_input.strip().lower()


@dataclass(frozen=True)
class KnowledgeSource:
    """エージェントが参照するナレッジソースを表す値オブジェクト"""

    name: str
    uri: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("ナレッジソース名は空にできません")
        if not self.uri.strip():
            raise ValueError("ナレッジソースのuriは空にできません")


@dataclass(frozen=True)
class ActionStep:
    """トピック内で実行される1件のアクションを表す値オブジェクト"""

    action_type: ActionType
    payload: str

    def __post_init__(self) -> None:
        if not self.payload.strip():
            raise ValueError("アクションのpayloadは空にできません")


@dataclass(frozen=True)
class ConversationTurn:
    """会話履歴の1ターン分の記録を表す値オブジェクト"""

    speaker: Speaker
    message: str
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        label = "ユーザー" if self.speaker is Speaker.USER else "エージェント"
        return f"[{self.timestamp:%H:%M:%S}] {label}: {self.message}"


class Topic:
    """
    Copilot Studioの「トピック」を模擬するクラス。
    トリガーフレーズの集合と、一致時に実行するアクション列を保持する。
    """

    def __init__(
        self,
        name: str,
        trigger_phrases: List[TriggerPhrase],
        actions: List[ActionStep],
    ) -> None:
        self._name: str = ""
        self._trigger_phrases: Tuple[TriggerPhrase, ...] = ()
        self._actions: Tuple[ActionStep, ...] = ()
        self.name = name
        self.trigger_phrases = trigger_phrases
        self.actions = actions

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("トピック名は空にできません")
        self._name = value

    @property
    def trigger_phrases(self) -> Tuple[TriggerPhrase, ...]:
        return self._trigger_phrases

    @trigger_phrases.setter
    def trigger_phrases(self, value: List[TriggerPhrase]) -> None:
        if not value:
            raise ValueError("トリガーフレーズは1件以上必要です")
        self._trigger_phrases = tuple(value)

    @property
    def actions(self) -> Tuple[ActionStep, ...]:
        return self._actions

    @actions.setter
    def actions(self, value: List[ActionStep]) -> None:
        if not value:
            raise ValueError("アクションは1件以上必要です")
        self._actions = tuple(value)

    def matches(self, user_input: str) -> bool:
        return any(phrase.matches(user_input) for phrase in self._trigger_phrases)

    def __repr__(self) -> str:
        return (
            f"Topic(name={self._name!r}, "
            f"triggers={len(self._trigger_phrases)}, actions={len(self._actions)})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Topic):
            return NotImplemented
        return self._name == other._name


class AgentConfig:
    """
    Copilot Studioの「エージェント」設定を模擬するクラス。
    名前・説明・システム指示・使用モデル・応答温度・ナレッジソースを
    カプセル化し、setter経由でのみ変更を許可してバリデーションを行う。
    """

    def __init__(
        self,
        name: str,
        description: str,
        instructions: str,
        model_type: ModelType = ModelType.GPT_4O,
        temperature: float = 0.3,
        knowledge_sources: Optional[List[KnowledgeSource]] = None,
    ) -> None:
        self._name: str = ""
        self._description: str = ""
        self._instructions: str = ""
        self._model_type: ModelType = ModelType.GPT_4O
        self._temperature: float = 0.0
        self._knowledge_sources: Tuple[KnowledgeSource, ...] = ()

        self.name = name
        self.description = description
        self.instructions = instructions
        self.model_type = model_type
        self.temperature = temperature
        self.knowledge_sources = knowledge_sources or []

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("エージェント名は空にできません")
        self._name = value

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("descriptionはstr型である必要があります")
        self._description = value

    @property
    def instructions(self) -> str:
        return self._instructions

    @instructions.setter
    def instructions(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("instructions（システム指示）は空にできません")
        self._instructions = value

    @property
    def model_type(self) -> ModelType:
        return self._model_type

    @model_type.setter
    def model_type(self, value: ModelType) -> None:
        if not isinstance(value, ModelType):
            raise TypeError("model_typeはModelType型である必要があります")
        self._model_type = value

    @property
    def temperature(self) -> float:
        return self._temperature

    @temperature.setter
    def temperature(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("temperatureはfloat型である必要があります")
        if not 0.0 <= value <= 1.0:
            raise ValueError("temperatureは0.0〜1.0の範囲で指定してください")
        self._temperature = float(value)

    @property
    def knowledge_sources(self) -> Tuple[KnowledgeSource, ...]:
        return self._knowledge_sources

    @knowledge_sources.setter
    def knowledge_sources(self, value: List[KnowledgeSource]) -> None:
        self._knowledge_sources = tuple(value)

    def __repr__(self) -> str:
        return (
            f"AgentConfig(name={self._name!r}, model={self._model_type.value}, "
            f"temperature={self._temperature}, "
            f"knowledge_sources={len(self._knowledge_sources)})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AgentConfig):
            return NotImplemented
        return self._name == other._name and self._model_type == other._model_type
