"""ComfyUIサーバーとのHTTP通信のみを担当するクライアント。"""
from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


class ComfyUIRequestError(RuntimeError):
    """ComfyUIサーバーとの通信に失敗した場合に送出する例外。"""


class ComfyUIClient:
    """ComfyUIのHTTP APIのみを扱う薄いクライアント。ワークフローの中身には関与しない。"""

    def __init__(
        self, base_url: str, client_id: Optional[str] = None, timeout_sec: float = 30.0
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client_id = client_id or str(uuid.uuid4())
        self._timeout_sec = timeout_sec

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def client_id(self) -> str:
        return self._client_id

    def upload_input_file(self, local_path: str) -> str:
        """画像・動画ファイルをComfyUIのinputディレクトリへアップロードし、保存されたファイル名を返す。"""
        path = Path(local_path)
        if not path.exists():
            raise ComfyUIRequestError(f"アップロード対象のファイルが存在しません: {local_path}")
        with path.open("rb") as file_obj:
            files = {"image": (path.name, file_obj)}
            response = requests.post(
                f"{self._base_url}/upload/image", files=files, timeout=self._timeout_sec
            )
        if response.status_code != 200:
            raise ComfyUIRequestError(
                f"ファイルのアップロードに失敗しました: {response.status_code} {response.text}"
            )
        data = response.json()
        filename = data.get("name")
        if not filename:
            raise ComfyUIRequestError(f"アップロード結果からファイル名を取得できませんでした: {data}")
        return str(filename)

    def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        payload = {"prompt": workflow, "client_id": self._client_id}
        response = requests.post(f"{self._base_url}/prompt", json=payload, timeout=self._timeout_sec)
        if response.status_code != 200:
            raise ComfyUIRequestError(
                f"ComfyUIへのキュー投入に失敗しました: {response.status_code} {response.text}"
            )
        data = response.json()
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise ComfyUIRequestError(f"prompt_id を取得できませんでした: {data}")
        return str(prompt_id)

    def get_history(self, prompt_id: str) -> Dict[str, Any]:
        response = requests.get(f"{self._base_url}/history/{prompt_id}", timeout=self._timeout_sec)
        if response.status_code != 200:
            raise ComfyUIRequestError(
                f"履歴の取得に失敗しました: {response.status_code} {response.text}"
            )
        return response.json()

    def wait_for_completion(
        self, prompt_id: str, poll_interval_sec: float = 1.0, timeout_sec: float = 600.0
    ) -> Dict[str, Any]:
        elapsed = 0.0
        while elapsed < timeout_sec:
            history = self.get_history(prompt_id)
            entry = history.get(prompt_id)
            if entry is not None and entry.get("outputs"):
                return entry
            time.sleep(poll_interval_sec)
            elapsed += poll_interval_sec
        raise TimeoutError(f"ComfyUIジョブ {prompt_id} の完了待機がタイムアウトしました")

    def extract_output_files(self, history_entry: Dict[str, Any]) -> List[Tuple[str, str, str]]:
        files: List[Tuple[str, str, str]] = []
        outputs = history_entry.get("outputs", {})
        for node_output in outputs.values():
            for key in ("images", "gifs", "videos"):
                for item in node_output.get(key, []):
                    filename = item.get("filename")
                    subfolder = item.get("subfolder", "")
                    folder_type = item.get("type", "output")
                    if filename:
                        files.append((filename, subfolder, folder_type))
        return files

    def download_file(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        response = requests.get(f"{self._base_url}/view", params=params, timeout=self._timeout_sec)
        if response.status_code != 200:
            raise ComfyUIRequestError(
                f"ファイルの取得に失敗しました: {response.status_code} {response.text}"
            )
        return response.content
