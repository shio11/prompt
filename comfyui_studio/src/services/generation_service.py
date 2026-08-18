"""テキスト→画像・画像→動画の生成ジョブを統括するサービス。"""
from __future__ import annotations

import random
from typing import List, Optional

from models.enums import JobKind, MediaType
from models.generation import GenerationJob, GenerationParameters, VideoParameters
from repositories.job_repository import JobRepository
from services.job_runner import JobRunner
from services.workflow_builder import WorkflowBuilder

_MAX_SEED = 2**32 - 1


class GenerationService:
    """WorkflowBuilderとJobRunnerを組み合わせ、新規生成処理を制御する。"""

    def __init__(
        self,
        workflow_builder: WorkflowBuilder,
        job_runner: JobRunner,
        job_repository: JobRepository,
    ) -> None:
        self._workflow_builder = workflow_builder
        self._job_runner = job_runner
        self._job_repository = job_repository

    def generate_image(self, params: GenerationParameters) -> GenerationJob:
        job = GenerationJob(kind=JobKind.TEXT_TO_IMAGE, media_type=MediaType.IMAGE)
        seed = self._resolve_seed(params.seed)
        workflow = self._workflow_builder.build_text_to_image(params, seed)
        return self._job_runner.run(job, workflow)

    def generate_video(self, params: VideoParameters) -> GenerationJob:
        job = GenerationJob(kind=JobKind.IMAGE_TO_VIDEO, media_type=MediaType.VIDEO)
        seed = self._resolve_seed(params.seed)
        image_filename = self._job_runner.upload_input_file(params.source_image_path)
        workflow = self._workflow_builder.build_image_to_video(params, image_filename, seed)
        return self._job_runner.run(job, workflow)

    def get_job(self, job_id: str) -> Optional[GenerationJob]:
        return self._job_repository.find_by_id(job_id)

    def list_recent_jobs(self, limit: int = 20) -> List[GenerationJob]:
        return self._job_repository.list_recent(limit)

    @staticmethod
    def _resolve_seed(seed: int) -> int:
        return seed if seed >= 0 else random.randint(0, _MAX_SEED)
