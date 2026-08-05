import argparse
from pathlib import Path

from models import AggregationConfig, PageRole
from services import (
    DocumentAggregationService,
    HtmlFileRepository,
    HtmlTextExtractionService,
    MainPageClassifierService,
    SubPageOrderingService,
    ZipArchiveRepository,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ZIP内のメインHTMLとサブHTML群を1つのテキストファイルに集約する"
    )
    parser.add_argument("zip_path", type=Path, help="入力ZIPファイルのパス")
    parser.add_argument("output_path", type=Path, help="集約結果を書き出すテキストファイルのパス")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = AggregationConfig()

    zip_repository = ZipArchiveRepository()
    html_repository = HtmlFileRepository()
    main_page_classifier = MainPageClassifierService(config)
    sub_page_ordering_service = SubPageOrderingService()
    text_extraction_service = HtmlTextExtractionService(config)
    document_aggregation_service = DocumentAggregationService(config)

    root_dir = zip_repository.extract(args.zip_path)
    try:
        html_paths = html_repository.find_html_files(root_dir)
        main_path, sub_paths = main_page_classifier.classify(html_paths)
        ordered_sub_paths = sub_page_ordering_service.order(main_path, sub_paths, config.encoding)

        pages = [text_extraction_service.extract(main_path, root_dir, PageRole.MAIN)]
        pages.extend(
            text_extraction_service.extract(path, root_dir, PageRole.SUB)
            for path in ordered_sub_paths
        )

        document = document_aggregation_service.build(pages)
        args.output_path.write_text(document, encoding=config.encoding)
    finally:
        zip_repository.cleanup(root_dir)

    print(f"集約結果を出力しました: {args.output_path}")


if __name__ == "__main__":
    main()
