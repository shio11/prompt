"""プロンプト作成を相談できる簡易エージェント。"""
from __future__ import annotations

from models.chat import ChatMessage, ChatSession
from models.enums import ChatRole
from services.llm_client import LLMClient

_SYSTEM_PROMPT = (
    "あなたは画像・動画生成AIのプロンプト作成を手伝うアシスタントです。"
    "ユーザーの要望(作りたいイメージ、雰囲気、用途など)を聞き取り、"
    "Stable Diffusion系モデル向けの具体的な英語のポジティブプロンプトと"
    "ネガティブプロンプトを、日本語の説明付きで提案してください。"
    "情報が不足している場合は、遠慮なく確認の質問をしてください。"
)


class PromptAgentService:
    """LLMClientを利用してプロンプト相談チャットを提供するサービス。"""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    def start_session(self) -> ChatSession:
        session = ChatSession()
        session.add_message(ChatMessage(role=ChatRole.SYSTEM, content=_SYSTEM_PROMPT))
        return session

    def ask(self, session: ChatSession, user_message: str) -> ChatMessage:
        session.add_message(ChatMessage(role=ChatRole.USER, content=user_message))
        reply_text = self._llm_client.complete_chat(session.messages)
        reply = ChatMessage(role=ChatRole.ASSISTANT, content=reply_text)
        session.add_message(reply)
        return reply
