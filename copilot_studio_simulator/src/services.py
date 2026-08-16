from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from models import (
    ActionStep,
    ActionType,
    AgentConfig,
    ConversationTurn,
    KnowledgeSource,
    ModelType,
    Speaker,
    Topic,
    TriggerPhrase,
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


class AgentSetupWizard:
    """
    コンソール入力を通じて対話的にエージェント設定・ナレッジソース・トピックを
    組み立てる責務を持つクラス。実際の組み立てはAgentBuilderへ委譲する（コンポジション）。
    """

    _MODEL_CHOICES: Tuple[ModelType, ...] = (
        ModelType.GPT_4O,
        ModelType.GPT_4,
        ModelType.GPT_35_TURBO,
    )
    _ACTION_CHOICES: Tuple[ActionType, ...] = (
        ActionType.SEND_MESSAGE,
        ActionType.CALL_API,
        ActionType.SET_VARIABLE,
        ActionType.END_CONVERSATION,
    )

    def __init__(
        self,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self._input = input_fn
        self._output = output_fn

    def run(self) -> Tuple[AgentConfig, List[Topic]]:
        self._output("=== エージェント設定ウィザード ===")
        builder = self._build_base_agent()
        self._register_knowledge_sources(builder)
        self._register_topics(builder)
        return builder.build()

    def _build_base_agent(self) -> AgentBuilder:
        while True:
            try:
                name = self._input("エージェント名: ").strip()
                description = self._input("説明（省略可）: ").strip()
                instructions = self._input("システム指示: ").strip()
                builder = AgentBuilder(name=name, description=description, instructions=instructions)
                builder.with_model(self._prompt_model_type())
                builder.with_temperature(self._prompt_temperature())
                return builder
            except ValueError as error:
                self._output(f"入力エラー: {error}。もう一度入力してください。")

    def _prompt_model_type(self) -> ModelType:
        self._output("使用モデルを選択してください:")
        for index, model_type in enumerate(self._MODEL_CHOICES, start=1):
            self._output(f"  {index}. {model_type.value}")
        choice = self._input("番号を入力（未入力でgpt-4o）: ").strip()
        if not choice:
            return ModelType.GPT_4O
        try:
            return self._MODEL_CHOICES[int(choice) - 1]
        except (ValueError, IndexError):
            self._output("不正な選択です。gpt-4oを使用します。")
            return ModelType.GPT_4O

    def _prompt_temperature(self) -> float:
        raw = self._input("応答温度（0.0〜1.0、未入力で0.3）: ").strip()
        if not raw:
            return 0.3
        try:
            return float(raw)
        except ValueError:
            self._output("不正な数値です。0.3を使用します。")
            return 0.3

    def _register_knowledge_sources(self, builder: AgentBuilder) -> None:
        self._output("--- ナレッジソース登録（未入力で終了） ---")
        while True:
            name = self._input("ナレッジソース名（未入力で終了）: ").strip()
            if not name:
                break
            uri = self._input("  URI: ").strip()
            try:
                builder.with_knowledge_source(name=name, uri=uri)
            except ValueError as error:
                self._output(f"入力エラー: {error}")

    def _register_topics(self, builder: AgentBuilder) -> None:
        self._output("--- トピック登録（未入力で終了） ---")
        while True:
            name = self._input("トピック名（未入力で終了）: ").strip()
            if not name:
                break
            try:
                topic = self._build_topic(name)
                builder.add_topic(topic)
            except ValueError as error:
                self._output(f"入力エラー: {error}。このトピックは登録されませんでした。")

    def _build_topic(self, name: str) -> Topic:
        phrases_raw = self._input("  トリガーフレーズ（カンマ区切りで複数指定可）: ").strip()
        trigger_phrases = [TriggerPhrase(text.strip()) for text in phrases_raw.split(",") if text.strip()]
        actions = self._register_actions()
        return Topic(name=name, trigger_phrases=trigger_phrases, actions=actions)

    def _register_actions(self) -> List[ActionStep]:
        self._output("  --- アクション登録（未入力で終了、最低1件必要） ---")
        actions: List[ActionStep] = []
        while True:
            for index, action_type in enumerate(self._ACTION_CHOICES, start=1):
                self._output(f"    {index}. {action_type.name}")
            choice = self._input("  番号（未入力で終了）: ").strip()
            if not choice:
                break
            try:
                action_type = self._ACTION_CHOICES[int(choice) - 1]
            except (ValueError, IndexError):
                self._output("  不正な選択です。")
                continue
            payload = self._input("  内容（SET_VARIABLEの場合は key=value 形式）: ").strip()
            try:
                actions.append(ActionStep(action_type=action_type, payload=payload))
            except ValueError as error:
                self._output(f"  入力エラー: {error}")
        return actions
