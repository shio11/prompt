"""アプリケーション全体で共有する値オブジェクト・DTOを定義するモジュール。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PyodideRuntime:
    """ブラウザ内で読み込むPyodide(WebAssembly版Python)ランタイムの情報。

    バージョンとCDNのベースURLからスクリプトURLを組み立てる際、
    ミスタイプでCDN URLが壊れた状態のオブジェクトが生まれないよう
    生成時にバリデーションを行う。
    """

    version: str
    cdn_base_url: str

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("version は空にできません。")
        if not self.cdn_base_url.startswith("https://"):
            raise ValueError("cdn_base_url は https:// で始まる必要があります。")

    @property
    def script_url(self) -> str:
        """pyodide.js 本体のURL。"""
        base = self.cdn_base_url.rstrip("/")
        return f"{base}/v{self.version}/full/pyodide.js"


@dataclass(frozen=True)
class StudioMetadata:
    """生成するHTMLツールの表示上のメタ情報(タイトル・説明文)。"""

    title: str
    description: str

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title は空にできません。")


@dataclass(frozen=True)
class AppConfig:
    """ツール生成に必要な設定一式をまとめたイミュータブルな設定オブジェクト。"""

    metadata: StudioMetadata
    pyodide: PyodideRuntime
    output_path: Path

    def __post_init__(self) -> None:
        if self.output_path.suffix.lower() != ".html":
            raise ValueError("output_path は .html 拡張子で終わる必要があります。")
