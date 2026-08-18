"""生成ジョブに関するドメインモデル。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from models.enums import JobKind, JobStatus, MediaType


@dataclass(frozen=True)
class GenerationParameters:
    """テキスト→画像生成のパラメータ値オブジェクト。不変。"""

    positive_prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    steps: int = 20
    cfg_scale: float = 8.0
    seed: int = -1
    sampler_name: str = "euler"
    checkpoint_name: str = "v1-5-pruned-emaonly.ckpt"

    def __post_init__(self) -> None:
        if not self.positive_prompt.strip():
            raise ValueError("positive_prompt は空にできません")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width/height は正の整数である必要があります")
        if self.width % 8 != 0 or self.height % 8 != 0:
            raise ValueError("width/height は8の倍数である必要があります")
        if self.steps <= 0:
            raise ValueError("steps は正の整数である必要があります")
        if self.cfg_scale <= 0:
            raise ValueError("cfg_scale は正の数である必要があります")


@dataclass(frozen=True)
class VideoParameters:
    """画像→動画生成(Stable Video Diffusion)のパラメータ値オブジェクト。不変。"""

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

    def __post_init__(self) -> None:
        if not self.source_image_path.strip():
            raise ValueError("source_image_path は空にできません")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width/height は正の整数である必要があります")
        if self.width % 8 != 0 or self.height % 8 != 0:
            raise ValueError("width/height は8の倍数である必要があります")
        if self.frame_count <= 0:
            raise ValueError("frame_count は正の整数である必要があります")
        if self.fps <= 0:
            raise ValueError("fps は正の整数である必要があります")
        if self.steps <= 0:
            raise ValueError("steps は正の整数である必要があります")


class GenerationJob:
    """生成ジョブのライフサイクルを管理するエンティティ。"""

    def __init__(
        self,
        kind: JobKind,
        media_type: MediaType,
        id: Optional[str] = None,  # noqa: A002 - リポジトリ復元用の識別子名として明確なため許容
        status: JobStatus = JobStatus.PENDING,
        created_at: Optional[datetime] = None,
        output_paths: Optional[List[str]] = None,
        error_message: Optional[str] = None,
    ) -> None:
        self.__id: str = id or str(uuid4())
        self.__kind: JobKind = kind
        self.__media_type: MediaType = media_type
        self.__status: JobStatus = status
        self.__created_at: datetime = created_at or datetime.utcnow()
        self.__output_paths: List[str] = list(output_paths) if output_paths else []
        self.__error_message: Optional[str] = error_message

    @property
    def id(self) -> str:
        return self.__id

    @property
    def kind(self) -> JobKind:
        return self.__kind

    @property
    def media_type(self) -> MediaType:
        return self.__media_type

    @property
    def created_at(self) -> datetime:
        return self.__created_at

    @property
    def status(self) -> JobStatus:
        return self.__status

    @status.setter
    def status(self, value: JobStatus) -> None:
        if not isinstance(value, JobStatus):
            raise TypeError("status は JobStatus である必要があります")
        self.__status = value

    @property
    def output_paths(self) -> List[str]:
        return list(self.__output_paths)

    @output_paths.setter
    def output_paths(self, value: List[str]) -> None:
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise TypeError("output_paths は文字列のリストである必要があります")
        self.__output_paths = list(value)

    @property
    def error_message(self) -> Optional[str]:
        return self.__error_message

    @error_message.setter
    def error_message(self, value: Optional[str]) -> None:
        self.__error_message = value

    def mark_running(self) -> None:
        self.status = JobStatus.RUNNING

    def mark_completed(self, output_paths: List[str]) -> None:
        self.output_paths = output_paths
        self.status = JobStatus.COMPLETED

    def mark_failed(self, error_message: str) -> None:
        self.error_message = error_message
        self.status = JobStatus.FAILED

    def __repr__(self) -> str:
        return (
            f"GenerationJob(id={self.__id!r}, kind={self.__kind!r}, "
            f"status={self.__status!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GenerationJob):
            return NotImplemented
        return self.__id == other.id
