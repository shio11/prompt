from services import (
    ExcelExportService,
    FileDialogService,
    KeywordSearchService,
    PdfTextExtractionService,
)


def main() -> None:
    dialog_service = FileDialogService()
    extraction_service = PdfTextExtractionService()
    search_service = KeywordSearchService()
    export_service = ExcelExportService()

    pdf_path = dialog_service.select_pdf_file()
    if pdf_path is None:
        dialog_service.show_warning("キャンセル", "PDFファイルが選択されませんでした")
        dialog_service.close()
        return

    keyword = dialog_service.input_keyword()
    if keyword is None:
        dialog_service.show_warning("キャンセル", "キーワードが入力されませんでした")
        dialog_service.close()
        return

    try:
        pages = extraction_service.extract_pages(pdf_path)
        result = search_service.search(pages=pages, keyword=keyword, source_path=pdf_path)
    except (ValueError, FileNotFoundError) as error:
        dialog_service.show_error("エラー", str(error))
        dialog_service.close()
        return

    if not result.matches:
        dialog_service.show_info("結果", "指定したキーワードは見つかりませんでした")
        dialog_service.close()
        return

    output_folder = dialog_service.select_output_folder()
    if output_folder is None:
        dialog_service.show_warning("キャンセル", "出力フォルダが選択されませんでした")
        dialog_service.close()
        return

    output_file_name = dialog_service.input_output_file_name()
    if output_file_name is None:
        dialog_service.show_warning("キャンセル", "出力ファイル名が入力されませんでした")
        dialog_service.close()
        return

    output_path = output_folder / output_file_name
    try:
        export_service.export(result, output_path)
    except ValueError as error:
        dialog_service.show_error("エラー", str(error))
        dialog_service.close()
        return

    dialog_service.show_info(
        "完了", f"{len(result.matches)}件のキーワード一致を出力しました: {output_path}"
    )
    dialog_service.close()


if __name__ == "__main__":
    main()
