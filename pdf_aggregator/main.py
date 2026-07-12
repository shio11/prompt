from tkinter import messagebox

from repositories.pdf_file_repository import PdfFileRepository
from services.folder_dialog_service import FolderDialogService
from services.numbering_input_service import NumberingInputService
from services.page_numbering_service import PageNumberingService
from services.pdf_file_sorter_service import PdfFileSorterService
from services.pdf_merger_service import PdfMergerService

_OUTPUT_FILE_NAME = "aggregated.pdf"


def main() -> None:
    dialog_service = FolderDialogService()
    file_repository = PdfFileRepository()
    sorter_service = PdfFileSorterService()
    merger_service = PdfMergerService()
    numbering_service = PageNumberingService()
    numbering_input_service = NumberingInputService()

    input_folder = dialog_service.select_input_folder()
    if input_folder is None:
        messagebox.showwarning("キャンセル", "入力フォルダが選択されませんでした")
        dialog_service.close()
        return

    try:
        pdf_paths = file_repository.find_pdf_files(input_folder)
        if not pdf_paths:
            messagebox.showerror("エラー", "フォルダ内にPDFファイルが見つかりません")
            dialog_service.close()
            return
        sorted_files = sorter_service.sort(pdf_paths)
        writer = merger_service.merge(sorted_files)
    except (ValueError, NotADirectoryError) as error:
        messagebox.showerror("エラー", str(error))
        dialog_service.close()
        return

    total_pages = len(writer.pages)
    numbering_config = numbering_input_service.prompt(dialog_service.root, total_pages)
    if numbering_config is None:
        messagebox.showwarning("キャンセル", "ページ番号設定が入力されませんでした")
        dialog_service.close()
        return

    numbering_service.add_page_numbers(writer, numbering_config)

    output_folder = dialog_service.select_output_folder()
    if output_folder is None:
        messagebox.showwarning("キャンセル", "出力フォルダが選択されませんでした")
        dialog_service.close()
        return

    output_path = output_folder / _OUTPUT_FILE_NAME
    file_repository.save(writer, output_path)
    messagebox.showinfo("完了", f"PDFを出力しました: {output_path}")
    dialog_service.close()


if __name__ == "__main__":
    main()
