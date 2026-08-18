"""ComfyUIワークフローの実行とジョブ状態更新の共通処理。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from models.generation import GenerationJob
from repositories.job_repository import JobRepository
from services.comfyui_client import ComfyUIClient


class JobRunner:
    """ワークフロー投入からファイル取得・ジョブ永続化までの共通フローを担当する。"""

    def __init__(
        self,
        comfyui_client: ComfyUIClient,
        job_repository: JobRepository,
        output_dir: str,
        poll_interval_sec: float = 1.0,
        timeout_sec: float = 600.0,
    ) -> None:
        self._comfyui_client = comfyui_client
        self._job_repository = job_repository
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._poll_interval_sec = poll_interval_sec
        self._timeout_sec = timeout_sec

    def upload_input_file(self, local_path: str) -> str:
        return self._comfyui_client.upload_input_file(local_path)

    def run(self, job: GenerationJob, workflow: Dict[str, Any]) -> GenerationJob:
        self._job_repository.save(job)
        job.mark_running()
        self._job_repository.save(job)
        try:
            prompt_id = self._comfyui_client.queue_prompt(workflow)
            history_entry = self._comfyui_client.wait_for_completion(
                prompt_id,
                poll_interval_sec=self._poll_interval_sec,
                timeout_sec=self._timeout_sec,
            )
            output_paths = self._download_outputs(job.id, history_entry)
            job.mark_completed(output_paths)
        except Exception as exc:  # noqa: BLE001 - ジョブ失敗として記録するため捕捉する
            job.mark_failed(str(exc))
        self._job_repository.save(job)
        return job

    def _download_outputs(self, job_id: str, history_entry: Dict[str, Any]) -> List[str]:
        job_dir = self._output_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        saved_paths: List[str] = []
        for filename, subfolder, folder_type in self._comfyui_client.extract_output_files(history_entry):
            content = self._comfyui_client.download_file(filename, subfolder, folder_type)
            destination = job_dir / filename
            destination.write_bytes(content)
            saved_paths.append(str(destination))
        return saved_paths
