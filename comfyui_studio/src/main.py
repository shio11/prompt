"""アプリケーションのエントリーポイント。依存関係の組み立てと起動のみを行う。"""
from __future__ import annotations

import uvicorn

from api.app import create_app
from config import get_settings
from repositories.job_repository import JobRepository
from services.agent_service import PromptAgentService
from services.comfyui_client import ComfyUIClient
from services.generation_service import GenerationService
from services.job_runner import JobRunner
from services.llm_client import OllamaLLMClient
from services.post_process_service import PostProcessService
from services.workflow_builder import WorkflowBuilder


def main() -> None:
    settings = get_settings()

    comfyui_client = ComfyUIClient(base_url=settings.comfyui_base_url)
    workflow_builder = WorkflowBuilder(workflows_dir=settings.workflows_dir)
    job_repository = JobRepository(db_path=settings.db_path)
    job_runner = JobRunner(
        comfyui_client=comfyui_client,
        job_repository=job_repository,
        output_dir=settings.output_dir,
        poll_interval_sec=settings.comfyui_poll_interval_sec,
        timeout_sec=settings.comfyui_timeout_sec,
    )

    generation_service = GenerationService(
        workflow_builder=workflow_builder,
        job_runner=job_runner,
        job_repository=job_repository,
    )
    post_process_service = PostProcessService(
        workflow_builder=workflow_builder,
        job_runner=job_runner,
    )

    llm_client = OllamaLLMClient(
        base_url=settings.ollama_base_url,
        model_name=settings.qwen_model_name,
    )
    agent_service = PromptAgentService(llm_client=llm_client)

    app = create_app(
        generation_service=generation_service,
        post_process_service=post_process_service,
        agent_service=agent_service,
    )

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
