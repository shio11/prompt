"""
combine_py_for_copilot.py

指定フォルダ以下(サブフォルダ含む)の .py ファイルをすべて再帰的に集めて、
1つのテキストファイルに結合、または1つのzipファイルにまとめるスクリプト。
Microsoft 365 Copilot Chat など、複数ファイルをまとめて添付しづらい場面で、
1ファイルとして添付するために使う。

使い方:
    python combine_py_for_copilot.py
        → カレントディレクトリ以下の .py を結合し、combined_for_copilot.txt を出力(デフォルト)

    python combine_py_for_copilot.py <対象フォルダ>
        → 指定フォルダ以下の .py を結合

    python combine_py_for_copilot.py --format zip
        → 1つのテキストではなく、フォルダ階層を保ったままzipにまとめて出力

    python combine_py_for_copilot.py --format md
        → コードブロック付きMarkdown(.md)として結合出力

    python combine_py_for_copilot.py --format both
        → txt結合とzip化の両方を出力

    python combine_py_for_copilot.py <対象フォルダ> -o <出力ファイル名(拡張子なし)>
        → 出力ファイル名を指定(拡張子は --format に応じて自動付与)

    python combine_py_for_copilot.py <対象フォルダ> -e venv __pycache__ .git
        → 除外したいフォルダ名を追加指定(デフォルトの除外リストに追加される)
"""

import argparse
import zipfile
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


def combine_to_text(py_files: list[Path], root: Path, output_file: Path) -> None:
    """.pyファイルを1つのテキストファイルに結合する(フォルダ階層は見出しとして記載)"""
    with output_file.open("w", encoding="utf-8") as out:
        for path in py_files:
            rel_path = path.relative_to(root)
            out.write(f"\n{'=' * 20} {rel_path} {'=' * 20}\n")
            try:
                out.write(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                out.write(f"[読み込み失敗: {rel_path} は UTF-8 以外の文字コードの可能性があります]\n")


def combine_to_markdown(py_files: list[Path], root: Path, output_file: Path) -> None:
    """.pyファイルをコードブロック付きMarkdownとして1ファイルに結合する"""
    with output_file.open("w", encoding="utf-8") as out:
        out.write(f"# 結合ファイル一覧（{len(py_files)}件）\n\n")
        for path in py_files:
            rel_path = path.relative_to(root)
            out.write(f"## `{rel_path}`\n\n")
            out.write("```python\n")
            try:
                content = path.read_text(encoding="utf-8")
                # コードブロックの終端(```)がコード中に含まれる場合に備えてエスケープ
                content = content.replace("```", "` ` `")
                out.write(content)
                if not content.endswith("\n"):
                    out.write("\n")
            except UnicodeDecodeError:
                out.write(f"[読み込み失敗: {rel_path} は UTF-8 以外の文字コードの可能性があります]\n")
            out.write("```\n\n")


def combine_to_zip(py_files: list[Path], root: Path, output_file: Path) -> None:
    """.pyファイルをフォルダ階層を保ったまま1つのzipにまとめる"""
    with zipfile.ZipFile(output_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in py_files:
            rel_path = path.relative_to(root)
            # arcname にフォルダ階層込みの相対パスを指定 → zip内でも階層が保たれる
            zf.write(path, arcname=str(rel_path))


def main():
    parser = argparse.ArgumentParser(
        description="複数の.pyファイルを再帰的に集めて、テキスト結合またはzip化する"
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="検索を開始するルートフォルダ(省略時はカレントディレクトリ)",
    )
    parser.add_argument(
        "-o", "--output",
        default="combined_for_copilot",
        help="出力ファイル名(拡張子なし。デフォルト: combined_for_copilot)",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["txt", "md", "zip", "both"],
        default="txt",
        help="出力形式: txt(結合テキスト) / md(Markdown結合) / zip(zip化) / both(txt+zip)。デフォルト: txt",
    )
    parser.add_argument(
        "-e", "--exclude",
        nargs="*",
        default=[],
        help="除外したいフォルダ名を追加指定(デフォルトの除外リストに追加される)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    exclude_dirs = DEFAULT_EXCLUDE_DIRS | set(args.exclude)

    if not root.exists():
        print(f"エラー: フォルダが見つかりません: {root}")
        return

    py_files = collect_py_files(root, exclude_dirs)

    if not py_files:
        print(f"'{root}' 以下に .py ファイルが見つかりませんでした。")
        return

    output_stem = Path(args.output)

    if args.format in ("txt", "both"):
        txt_path = output_stem.with_suffix(".txt")
        combine_to_text(py_files, root, txt_path)
        print(f"📄 {len(py_files)} 個の .py ファイルを '{txt_path}' に結合しました。")

    if args.format == "md":
        md_path = output_stem.with_suffix(".md")
        combine_to_markdown(py_files, root, md_path)
        print(f"📝 {len(py_files)} 個の .py ファイルを '{md_path}' に結合しました。")

    if args.format in ("zip", "both"):
        zip_path = output_stem.with_suffix(".zip")
        combine_to_zip(py_files, root, zip_path)
        print(f"🗜️  {len(py_files)} 個の .py ファイルを '{zip_path}' にまとめました(フォルダ階層を保持)。")

    print(f"除外フォルダ: {sorted(exclude_dirs)}")


if __name__ == "__main__":
    main()
