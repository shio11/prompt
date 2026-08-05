import argparse
from pathlib import Path

from models import AggregationConfig, PageRole
from services import (
    DocumentAggregationService,
    HtmlFileRepository,
    HtmlTextExtractionService,
    InputSourceResolverService,
    MainPageClassifierService,
    PdfDocumentBuilderService,
    SubPageOrderingService,
    ZipArchiveRepository,
)

_PDF_SUFFIX = ".pdf"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="フォルダまたはZIP内のメインHTMLとサブHTML群を1つのファイルに集約する"
    )
    parser.add_argument("input_path", type=Path, help="展開済みフォルダ、またはZIPファイルのパス")
    parser.add_argument(
        "output_path",
        type=Path,
        help="集約結果の出力先パス(拡張子が.pdfならPDF、それ以外はテキストで出力)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = AggregationConfig()

    zip_repository = ZipArchiveRepository()
    input_source_resolver = InputSourceResolverService(zip_repository)
    html_repository = HtmlFileRepository()
    main_page_classifier = MainPageClassifierService(config)
    sub_page_ordering_service = SubPageOrderingService()
    text_extraction_service = HtmlTextExtractionService(config)
    document_aggregation_service = DocumentAggregationService(config)
    pdf_document_builder_service = PdfDocumentBuilderService()

    root_dir, should_cleanup = input_source_resolver.resolve(args.input_path)
    try:
        html_paths = html_repository.find_html_files(root_dir)
        main_path, sub_paths = main_page_classifier.classify(html_paths)
        ordered_sub_paths = sub_page_ordering_service.order(main_path, sub_paths, config.encoding)

        pages = [text_extraction_service.extract(main_path, root_dir, PageRole.MAIN)]
        pages.extend(
            text_extraction_service.extract(path, root_dir, PageRole.SUB)
            for path in ordered_sub_paths
        )

        if args.output_path.suffix.lower() == _PDF_SUFFIX:
            pdf_document_builder_service.build(pages, args.output_path)
        else:
            document = document_aggregation_service.build(pages)
            args.output_path.write_text(document, encoding=config.encoding)
    finally:
        input_source_resolver.cleanup(root_dir, should_cleanup)

    print(f"集約結果を出力しました: {args.output_path}")


if __name__ == "__main__":
    main()
