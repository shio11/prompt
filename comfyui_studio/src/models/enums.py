"""ドメイン全体で使用する列挙型定義。"""
from enum import Enum


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobKind(str, Enum):
    TEXT_TO_IMAGE = "text_to_image"
    IMAGE_TO_VIDEO = "image_to_video"
    UPSCALE = "upscale"
    FRAME_INTERPOLATION = "frame_interpolation"


class UpscaleModel(str, Enum):
    REAL_ESRGAN_X2 = "RealESRGAN_x2plus.pth"
    REAL_ESRGAN_X4 = "RealESRGAN_x4plus.pth"
    REAL_ESRGAN_ANIME_X4 = "RealESRGAN_x4plus_anime_6B.pth"


class InterpolationModel(str, Enum):
    RIFE47 = "rife47.pth"
    RIFE49 = "rife49.pth"


class ChatRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
