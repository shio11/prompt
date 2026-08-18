"""プロンプト相談チャットのAPIルート。"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request

from api.schemas import ChatRequest, ChatResponse
from models.chat import ChatSession

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    agent_service = request.app.state.agent_service
    sessions: Dict[str, ChatSession] = request.app.state.chat_sessions

    if payload.session_id and payload.session_id in sessions:
        session = sessions[payload.session_id]
    else:
        session = agent_service.start_session()
        sessions[session.id] = session

    try:
        reply = agent_service.ask(session, payload.message)
    except Exception as exc:  # noqa: BLE001 - LLM通信エラーをHTTPエラーへ変換するため捕捉する
        raise HTTPException(status_code=502, detail=f"エージェントとの通信に失敗しました: {exc}") from exc

    return ChatResponse(session_id=session.id, reply=reply.content)


@router.get("/chat/{session_id}/history")
def get_chat_history(session_id: str, request: Request) -> List[Dict[str, Any]]:
    sessions: Dict[str, ChatSession] = request.app.state.chat_sessions
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    return [
        {"role": m.role.value, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in session.messages
        if m.role.value != "system"
    ]
