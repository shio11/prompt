"""画像・動画生成、アップスケール、フレーム補間のAPIルート。"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Request

from api.schemas import (
    FrameInterpolationRequest,
    GenerateImageRequest,
    GenerateVideoRequest,
    JobResponse,
    UpscaleRequest,
)
from models.enums import InterpolationModel, UpscaleModel
from models.generation import GenerationJob, GenerationParameters, VideoParameters

router = APIRouter(prefix="/api", tags=["generation"])


def _to_job_response(job: GenerationJob) -> JobResponse:
    return JobResponse(
        id=job.id,
        kind=job.kind.value,
        media_type=job.media_type.value,
        status=job.status.value,
        output_paths=job.output_paths,
        error_message=job.error_message,
    )


@router.post("/generate/image", response_model=JobResponse)
def generate_image(payload: GenerateImageRequest, request: Request) -> JobResponse:
    service = request.app.state.generation_service
    try:
        params = GenerationParameters(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    job = service.generate_image(params)
    return _to_job_response(job)


@router.post("/generate/video", response_model=JobResponse)
def generate_video(payload: GenerateVideoRequest, request: Request) -> JobResponse:
    service = request.app.state.generation_service
    try:
        params = VideoParameters(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    job = service.generate_video(params)
    return _to_job_response(job)


@router.post("/upscale", response_model=JobResponse)
def upscale_image(payload: UpscaleRequest, request: Request) -> JobResponse:
    service = request.app.state.post_process_service
    try:
        model = UpscaleModel(payload.model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"未対応のモデルです: {payload.model}") from exc
    job = service.upscale_image(payload.image_path, model)
    return _to_job_response(job)


@router.post("/interpolate", response_model=JobResponse)
def interpolate_frames(payload: FrameInterpolationRequest, request: Request) -> JobResponse:
    service = request.app.state.post_process_service
    try:
        model = InterpolationModel(payload.model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"未対応のモデルです: {payload.model}") from exc
    job = service.interpolate_frames(payload.video_path, model, payload.multiplier)
    return _to_job_response(job)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, request: Request) -> JobResponse:
    service = request.app.state.generation_service
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="ジョブが見つかりません")
    return _to_job_response(job)


@router.get("/jobs", response_model=List[JobResponse])
def list_jobs(request: Request, limit: int = 20) -> List[JobResponse]:
    service = request.app.state.generation_service
    jobs = service.list_recent_jobs(limit)
    return [_to_job_response(job) for job in jobs]
