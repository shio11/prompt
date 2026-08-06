from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from models import (
    ActionStep,
    ActionType,
    AgentConfig,
    ConversationTurn,
    KnowledgeSource,
    ModelType,
    Speaker,
    Topic,
)


class TopicMatcher:
    """ユーザー発話に一致するトピックを探索する責務を持つクラス"""

    def __init__(self, topics: List[Topic]) -> None:
        self._topics: Tuple[Topic, ...] = tuple(topics)

    @property
    def topics(self) -> Tuple[Topic, ...]:
        return self._topics

    def find_match(self, user_input: str) -> Optional[Topic]:
        for topic in self._topics:
            if topic.matches(user_input):
                return topic
        return None


class ActionExecutor:
    """トピックのアクション列を順に実行し、応答メッセージを組み立てる責務を持つクラス"""

    def execute(self, actions: Tuple[ActionStep, ...], variables: Dict[str, str]) -> str:
        message_lines: List[str] = []
        for action in actions:
            message_lines.append(self._execute_one(action, variables))
        return "\n".join(message_lines)

    def _execute_one(self, action: ActionStep, variables: Dict[str, str]) -> str:
        if action.action_type is ActionType.SEND_MESSAGE:
            return action.payload
        if action.action_type is ActionType.CALL_API:
            return f"[API呼び出しをシミュレート: {action.payload}] 完了しました"
        if action.action_type is ActionType.SET_VARIABLE:
            key, _, value = action.payload.partition("=")
            variables[key.strip()] = value.strip()
            return f"(変数 {key.strip()} を設定しました)"
        if action.action_type is ActionType.END_CONVERSATION:
            return f"{action.payload}\n(会話を終了します)"
        raise ValueError(f"未対応のActionTypeです: {action.action_type}")


class GenerativeResponder:
    """一致するトピックが無い場合の生成AI応答を模擬する責務を持つクラス"""

    def __init__(self, agent_config: AgentConfig) -> None:
        self._agent_config = agent_config

    def respond(self, user_input: str) -> str:
        sources = self._agent_config.knowledge_sources
        if sources:
            source_names = ", ".join(source.name for source in sources)
            return (
                f"（{self._agent_config.name}より）ご質問「{user_input}」については、"
                f"ナレッジソース[{source_names}]を参照して回答を生成します。"
            )
        return (
            f"（{self._agent_config.name}より）ご質問「{user_input}」に一致するトピックが"
            "見つからなかったため、指示に基づいた汎用回答を生成します。"
        )


class ConversationSimulator:
    """
    AgentConfigとトピック群を用いて、ユーザーとの会話をシミュレートする責務を持つクラス。
    トピック照合・アクション実行・生成応答の各処理は他クラスへ委譲する（コンポジション）。
    """

    def __init__(
        self,
        agent_config: AgentConfig,
        topic_matcher: TopicMatcher,
        action_executor: ActionExecutor,
        responder: GenerativeResponder,
    ) -> None:
        self._agent_config = agent_config
        self._topic_matcher = topic_matcher
        self._action_executor = action_executor
        self._responder = responder
        self._history: List[ConversationTurn] = []
        self._variables: Dict[str, str] = {}

    @property
    def agent_config(self) -> AgentConfig:
        return self._agent_config

    @property
    def history(self) -> Tuple[ConversationTurn, ...]:
        return tuple(self._history)

    @property
    def variables(self) -> Dict[str, str]:
        return dict(self._variables)

    def send(self, user_input: str) -> str:
        self._history.append(ConversationTurn(Speaker.USER, user_input))
        matched_topic = self._topic_matcher.find_match(user_input)
        if matched_topic is not None:
            reply = self._action_executor.execute(matched_topic.actions, self._variables)
        else:
            reply = self._responder.respond(user_input)
        self._history.append(ConversationTurn(Speaker.AGENT, reply))
        return reply


class AgentBuilder:
    """AgentConfigとトピック群をまとめて組み立てる責務を持つビルダークラス"""

    def __init__(self, name: str, description: str, instructions: str) -> None:
        self._agent_config = AgentConfig(name=name, description=description, instructions=instructions)
        self._topics: List[Topic] = []

    def with_model(self, model_type: ModelType) -> "AgentBuilder":
        self._agent_config.model_type = model_type
        return self

    def with_temperature(self, temperature: float) -> "AgentBuilder":
        self._agent_config.temperature = temperature
        return self

    def with_knowledge_source(self, name: str, uri: str) -> "AgentBuilder":
        self._agent_config.knowledge_sources = list(self._agent_config.knowledge_sources) + [
            KnowledgeSource(name=name, uri=uri)
        ]
        return self

    def add_topic(self, topic: Topic) -> "AgentBuilder":
        self._topics.append(topic)
        return self

    def build(self) -> Tuple[AgentConfig, List[Topic]]:
        return self._agent_config, list(self._topics)
