"""エントリーポイント。設定を組み立て、HTMLツールを生成してファイルへ出力する。"""

from __future__ import annotations

import argparse
from pathlib import Path

from models import AppConfig, PyodideRuntime, StudioMetadata
from services import StudioFileWriter, StudioHtmlBuilder

DEFAULT_PYODIDE_VERSION = "0.26.4"
DEFAULT_PYODIDE_CDN_BASE_URL = "https://cdn.jsdelivr.net/pyodide"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="環境構築なしでブラウザから開けるHTML作成・編集ツールを生成します。"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("html_python_studio.html"),
        help="生成するHTMLファイルの出力先パス(既定: html_python_studio.html)",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="HTML & Python Studio",
        help="ツール画面に表示するタイトル",
    )
    return parser.parse_args()


def build_app_config(args: argparse.Namespace) -> AppConfig:
    metadata = StudioMetadata(
        title=args.title,
        description="HTMLの作成・編集と、ブラウザ内Python実行を1画面で行えるツールです。",
    )
    pyodide = PyodideRuntime(
        version=DEFAULT_PYODIDE_VERSION,
        cdn_base_url=DEFAULT_PYODIDE_CDN_BASE_URL,
    )
    return AppConfig(metadata=metadata, pyodide=pyodide, output_path=args.output)


def main() -> None:
    args = parse_arguments()
    config = build_app_config(args)

    builder = StudioHtmlBuilder(config)
    html_document = builder.build()

    writer = StudioFileWriter(config.output_path)
    written_path = writer.write(html_document)

    print(f"生成しました: {written_path.resolve()}")
    print("このHTMLファイルを配布し、Microsoft Edgeで開くだけで利用できます。")


if __name__ == "__main__":
    main()
