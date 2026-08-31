"""
combine_py_for_copilot.py

指定フォルダ以下(サブフォルダ含む)の .py ファイルをすべて再帰的に集めて、
1つのテキストファイルに結合するスクリプト。
Microsoft 365 Copilot Chat など、複数ファイルをまとめて添付しづらい場面で、
1ファイルとして添付するために使う。

使い方:
    python combine_py_for_copilot.py
        → カレントディレクトリ以下の .py を結合し、combined_for_copilot.txt を出力

    python combine_py_for_copilot.py <対象フォルダ>
        → 指定フォルダ以下の .py を結合

    python combine_py_for_copilot.py <対象フォルダ> -o <出力ファイル名>
        → 出力ファイル名を指定

    python combine_py_for_copilot.py <対象フォルダ> -e venv __pycache__ .git
        → 除外したいフォルダ名を追加指定(デフォルトの除外リストに追加される)
"""

import argparse
from pathlib import Path

# デフォルトで除外するフォルダ名(このフォルダ名を含むパスの.pyはスキップ)
DEFAULT_EXCLUDE_DIRS = {"venv", ".venv", "__pycache__", ".git", "node_modules", "env"}


def collect_py_files(root: Path, exclude_dirs: set[str]) -> list[Path]:
    """root以下を再帰検索し、除外フォルダを含まない.pyファイル一覧をソートして返す"""
    py_files = [
        p for p in root.rglob("*.py")
        if not any(part in exclude_dirs for part in p.parts)
    ]
    return sorted(py_files)


def combine_files(root: Path, output_file: Path, exclude_dirs: set[str]) -> int:
    """.pyファイルを結合してoutput_fileに書き出す。結合したファイル数を返す"""
    py_files = collect_py_files(root, exclude_dirs)

    with output_file.open("w", encoding="utf-8") as out:
        for path in py_files:
            rel_path = path.relative_to(root)
            out.write(f"\n{'=' * 20} {rel_path} {'=' * 20}\n")
            try:
                out.write(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                out.write(f"[読み込み失敗: {rel_path} は UTF-8 以外の文字コードの可能性があります]\n")

    return len(py_files)


def main():
    parser = argparse.ArgumentParser(
        description="複数の.pyファイルを再帰的に集めて1つのテキストファイルに結合する"
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="検索を開始するルートフォルダ(省略時はカレントディレクトリ)",
    )
    parser.add_argument(
        "-o", "--output",
        default="combined_for_copilot.txt",
        help="出力ファイル名(デフォルト: combined_for_copilot.txt)",
    )
    parser.add_argument(
        "-e", "--exclude",
        nargs="*",
        default=[],
        help="除外したいフォルダ名を追加指定(デフォルトの除外リストに追加される)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output_file = Path(args.output)
    exclude_dirs = DEFAULT_EXCLUDE_DIRS | set(args.exclude)

    if not root.exists():
        print(f"エラー: フォルダが見つかりません: {root}")
        return

    count = combine_files(root, output_file, exclude_dirs)

    if count == 0:
        print(f"'{root}' 以下に .py ファイルが見つかりませんでした。")
    else:
        print(f"{count} 個の .py ファイルを '{output_file}' にまとめました。")
        print(f"除外フォルダ: {sorted(exclude_dirs)}")


if __name__ == "__main__":
    main()
