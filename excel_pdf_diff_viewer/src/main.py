import argparse
import webbrowser
from pathlib import Path

from services import (
    ContentExtractorFactory,
    DiffService,
    HtmlDiffReportRenderer,
    ReportFileWriter,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Excel/PDFファイルを読み込み、差分をHTMLレポートとして出力します"
    )
    parser.add_argument("left_file", type=Path, help="比較対象1つ目のファイル(.xlsx/.xlsm/.pdf)")
    parser.add_argument("right_file", type=Path, help="比較対象2つ目のファイル(.xlsx/.xlsm/.pdf)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("diff_report.html"),
        help="出力するHTMLファイルのパス(デフォルト: diff_report.html)",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="生成後にブラウザで自動的に開かない",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    extractor_factory = ContentExtractorFactory()
    diff_service = DiffService()
    renderer = HtmlDiffReportRenderer()
    writer = ReportFileWriter()

    left_content = extractor_factory.create_for(args.left_file).extract(args.left_file)
    right_content = extractor_factory.create_for(args.right_file).extract(args.right_file)

    diff_lines = diff_service.compute(left_content, right_content)
    report_html = renderer.render(left_content, right_content, diff_lines)
    writer.write(report_html, args.output)

    print(f"差分レポートを出力しました: {args.output}")

    if not args.no_open:
        webbrowser.open(args.output.resolve().as_uri())


if __name__ == "__main__":
    main()
