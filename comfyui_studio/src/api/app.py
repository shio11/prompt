"""FastAPIアプリケーションのファクトリ。"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.chat_routes import router as chat_router
from api.generation_routes import router as generation_router
from services.agent_service import PromptAgentService
from services.generation_service import GenerationService
from services.post_process_service import PostProcessService

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def create_app(
    generation_service: GenerationService,
    post_process_service: PostProcessService,
    agent_service: PromptAgentService,
) -> FastAPI:
    app = FastAPI(title="ComfyUI Studio")

    app.state.generation_service = generation_service
    app.state.post_process_service = post_process_service
    app.state.agent_service = agent_service
    app.state.chat_sessions = {}

    app.include_router(generation_router)
    app.include_router(chat_router)

    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app
