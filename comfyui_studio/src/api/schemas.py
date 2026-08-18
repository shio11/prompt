"""FastAPIのリクエスト/レスポンス用スキーマ。"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class GenerateImageRequest(BaseModel):
    positive_prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    steps: int = 20
    cfg_scale: float = 8.0
    seed: int = -1
    sampler_name: str = "euler"
    checkpoint_name: str = "v1-5-pruned-emaonly.ckpt"


class GenerateVideoRequest(BaseModel):
    source_image_path: str
    width: int = 1024
    height: int = 576
    frame_count: int = 14
    fps: int = 6
    motion_bucket_id: int = 127
    augmentation_level: float = 0.0
    steps: int = 20
    cfg_scale: float = 2.5
    seed: int = -1
    checkpoint_name: str = "svd_xt.safetensors"


class UpscaleRequest(BaseModel):
    image_path: str
    model: str = "RealESRGAN_x4plus.pth"


class FrameInterpolationRequest(BaseModel):
    video_path: str
    model: str = "rife47.pth"
    multiplier: int = 2


class JobResponse(BaseModel):
    id: str
    kind: str
    media_type: str
    status: str
    output_paths: List[str]
    error_message: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    session_id: str
    reply: str
