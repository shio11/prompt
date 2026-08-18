"""アップスケールとフレーム補間(後処理)を担当するサービス。"""
from __future__ import annotations

from models.enums import InterpolationModel, JobKind, MediaType, UpscaleModel
from models.generation import GenerationJob
from services.job_runner import JobRunner
from services.workflow_builder import WorkflowBuilder


class PostProcessService:
    """既存の画像・動画に対するアップスケール／フレーム補間処理を統括する。"""

    def __init__(self, workflow_builder: WorkflowBuilder, job_runner: JobRunner) -> None:
        self._workflow_builder = workflow_builder
        self._job_runner = job_runner

    def upscale_image(self, image_path: str, model: UpscaleModel) -> GenerationJob:
        job = GenerationJob(kind=JobKind.UPSCALE, media_type=MediaType.IMAGE)
        image_filename = self._job_runner.upload_input_file(image_path)
        workflow = self._workflow_builder.build_upscale(image_filename, model)
        return self._job_runner.run(job, workflow)

    def interpolate_frames(
        self, video_path: str, model: InterpolationModel, multiplier: int = 2
    ) -> GenerationJob:
        job = GenerationJob(kind=JobKind.FRAME_INTERPOLATION, media_type=MediaType.VIDEO)
        video_filename = self._job_runner.upload_input_file(video_path)
        workflow = self._workflow_builder.build_frame_interpolation(video_filename, model, multiplier)
        return self._job_runner.run(job, workflow)
