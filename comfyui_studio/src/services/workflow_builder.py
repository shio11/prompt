"""ComfyUIワークフローJSONテンプレートを組み立てるクラス。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from models.enums import InterpolationModel, UpscaleModel
from models.generation import GenerationParameters, VideoParameters


class WorkflowTemplateNotFoundError(FileNotFoundError):
    """ワークフローテンプレートファイルが見つからない場合に送出する例外。"""


class WorkflowBuilder:
    """テンプレートファイルにパラメータを差し込み、ComfyUI用ワークフロー辞書を生成する。"""

    def __init__(self, workflows_dir: str) -> None:
        self._workflows_dir = Path(workflows_dir)

    def build_text_to_image(self, params: GenerationParameters, seed: int) -> Dict[str, Any]:
        template_text = self._load_template("txt2img.json")
        values = {
            "POSITIVE_PROMPT": self._escape(params.positive_prompt),
            "NEGATIVE_PROMPT": self._escape(params.negative_prompt),
            "WIDTH": params.width,
            "HEIGHT": params.height,
            "STEPS": params.steps,
            "CFG_SCALE": params.cfg_scale,
            "SEED": seed,
            "SAMPLER_NAME": self._escape(params.sampler_name),
            "CHECKPOINT_NAME": self._escape(params.checkpoint_name),
        }
        return self._render(template_text, values)

    def build_image_to_video(
        self, params: VideoParameters, image_filename: str, seed: int
    ) -> Dict[str, Any]:
        template_text = self._load_template("img2video.json")
        values = {
            "IMAGE_FILENAME": self._escape(image_filename),
            "WIDTH": params.width,
            "HEIGHT": params.height,
            "FRAME_COUNT": params.frame_count,
            "FPS": params.fps,
            "MOTION_BUCKET_ID": params.motion_bucket_id,
            "AUGMENTATION_LEVEL": params.augmentation_level,
            "STEPS": params.steps,
            "CFG_SCALE": params.cfg_scale,
            "SEED": seed,
            "CHECKPOINT_NAME": self._escape(params.checkpoint_name),
        }
        return self._render(template_text, values)

    def build_upscale(self, image_filename: str, model: UpscaleModel) -> Dict[str, Any]:
        template_text = self._load_template("upscale.json")
        values = {
            "IMAGE_FILENAME": self._escape(image_filename),
            "UPSCALE_MODEL_NAME": self._escape(model.value),
        }
        return self._render(template_text, values)

    def build_frame_interpolation(
        self, video_filename: str, model: InterpolationModel, multiplier: int
    ) -> Dict[str, Any]:
        template_text = self._load_template("frame_interpolation.json")
        values = {
            "VIDEO_FILENAME": self._escape(video_filename),
            "CKPT_NAME": self._escape(model.value),
            "MULTIPLIER": multiplier,
        }
        return self._render(template_text, values)

    def _load_template(self, filename: str) -> str:
        path = self._workflows_dir / filename
        if not path.exists():
            raise WorkflowTemplateNotFoundError(f"テンプレートが見つかりません: {path}")
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _render(template_text: str, values: Dict[str, Any]) -> Dict[str, Any]:
        rendered = template_text
        for key, value in values.items():
            rendered = rendered.replace(f"__{key}__", str(value))
        return json.loads(rendered)

    @staticmethod
    def _escape(text: str) -> str:
        """テンプレート中の引用符で囲まれた箇所に安全に差し込めるようJSON文字列としてエスケープする。"""
        return json.dumps(text)[1:-1]
