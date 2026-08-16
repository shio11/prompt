from models import ActionStep, ActionType, ModelType, Topic, TriggerPhrase
from services import (
    ActionExecutor,
    AgentBuilder,
    AgentSetupWizard,
    ConversationSimulator,
    GenerativeResponder,
    TopicMatcher,
)


def build_sample_agent():
    builder = (
        AgentBuilder(
            name="ITヘルプデスクエージェント",
            description="社内向けIT問い合わせに対応するエージェント",
            instructions="丁寧な日本語で、社内ITポリシーに沿って回答してください。",
        )
        .with_model(ModelType.GPT_4O)
        .with_temperature(0.2)
        .with_knowledge_source(name="社内ITポータル", uri="https://it-portal.example.com")
    )

    builder.add_topic(
        Topic(
            name="挨拶",
            trigger_phrases=[TriggerPhrase("こんにちは"), TriggerPhrase("hello")],
            actions=[ActionStep(ActionType.SEND_MESSAGE, "こんにちは。ITヘルプデスクです。ご用件をどうぞ。")],
        )
    )
    builder.add_topic(
        Topic(
            name="パスワードリセット",
            trigger_phrases=[TriggerPhrase("パスワード"), TriggerPhrase("password")],
            actions=[
                ActionStep(ActionType.SET_VARIABLE, "topic=password_reset"),
                ActionStep(ActionType.CALL_API, "PasswordResetAPI"),
                ActionStep(ActionType.SEND_MESSAGE, "パスワードリセット用のリンクをメールで送信しました。"),
            ],
        )
    )
    builder.add_topic(
        Topic(
            name="会話終了",
            trigger_phrases=[TriggerPhrase("ありがとう"), TriggerPhrase("終了")],
            actions=[ActionStep(ActionType.END_CONVERSATION, "ご利用ありがとうございました。")],
        )
    )

    return builder.build()


def choose_agent():
    print("=== Copilot Studio Agent Simulator ===")
    print("1. サンプルエージェントを使用")
    print("2. 対話形式で新規作成")
    choice = input("番号を選択してください（未入力で1）: ").strip()
    if choice == "2":
        return AgentSetupWizard().run()
    return build_sample_agent()


def main() -> None:
    agent_config, topics = choose_agent()

    topic_matcher = TopicMatcher(topics)
    action_executor = ActionExecutor()
    responder = GenerativeResponder(agent_config)
    simulator = ConversationSimulator(agent_config, topic_matcher, action_executor, responder)

    print(f"=== {agent_config.name} シミュレーター ===")
    print(agent_config)
    print("メッセージを入力してください（終了するには exit と入力）")

    while True:
        try:
            user_input = input("あなた: ")
        except EOFError:
            break
        if user_input.strip().lower() == "exit":
            break
        if not user_input.strip():
            continue

        reply = simulator.send(user_input)
        print(f"エージェント: {reply}")


if __name__ == "__main__":
    main()
