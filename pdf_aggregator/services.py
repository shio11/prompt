import io
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
from typing import List, Optional, Pattern

from pypdf import PdfReader, PdfWriter
from pypdf._page import PageObject
from reportlab.pdfgen import canvas

from models import NumberingConfig, PdfFileInfo


class PdfFileRepository:
    """PDFファイルに対するファイルシステムI/Oのみを担当する"""

    def find_pdf_files(self, folder: Path) -> List[Path]:
        if not folder.is_dir():
            raise NotADirectoryError(f"{folder} はフォルダではありません")
        return [
            path for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() == ".pdf"
        ]

    def save(self, writer: PdfWriter, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)


class PdfFileSorterService:
    """ファイル名先頭の連番(例: 01_xxx.pdf)を抽出し、昇順に並び替える"""

    _LEADING_NUMBER_PATTERN: Pattern[str] = re.compile(r"^(\d+)_")

    def sort(self, files: List[Path]) -> List[PdfFileInfo]:
        infos: List[PdfFileInfo] = [self._to_pdf_file_info(path) for path in files]
        return sorted(infos, key=lambda info: info.order_number)

    def _to_pdf_file_info(self, path: Path) -> PdfFileInfo:
        match = self._LEADING_NUMBER_PATTERN.match(path.stem)
        if match is None:
            raise ValueError(
                f"ファイル名 '{path.name}' は '連番_' で始まる形式ではありません"
            )
        return PdfFileInfo(path=path, order_number=int(match.group(1)))


class PdfMergerService:
    """ソート済みのPDFファイル群を1つのPdfWriterに結合する"""

    def merge(self, sorted_files: List[PdfFileInfo]) -> PdfWriter:
        writer = PdfWriter()
        for info in sorted_files:
            reader = PdfReader(str(info.path))
            for page in reader.pages:
                writer.add_page(page)
        return writer


class PageNumberingService:
    """結合済みPDFの右上に「現在ページ/総ページ数」を付与する"""

    _MARGIN_RIGHT: float = 36.0
    _MARGIN_TOP: float = 24.0
    _FONT_NAME: str = "Helvetica"
    _FONT_SIZE: int = 10

    def add_page_numbers(self, writer: PdfWriter, config: NumberingConfig) -> None:
        total_pages = len(writer.pages)
        if config.start_page > total_pages:
            raise ValueError("start_page が総ページ数を超えています")

        for index, page in enumerate(writer.pages):
            page_number_in_document = index + 1
            if page_number_in_document < config.start_page:
                continue

            display_number = config.start_number + (page_number_in_document - config.start_page)
            overlay_page = self._create_overlay_page(
                width=float(page.mediabox.width),
                height=float(page.mediabox.height),
                text=f"{display_number}/{total_pages}",
            )
            page.merge_page(overlay_page)

    def _create_overlay_page(self, width: float, height: float, text: str) -> PageObject:
        buffer = io.BytesIO()
        pdf_canvas = canvas.Canvas(buffer, pagesize=(width, height))
        pdf_canvas.setFont(self._FONT_NAME, self._FONT_SIZE)
        x = width - self._MARGIN_RIGHT
        y = height - self._MARGIN_TOP
        pdf_canvas.drawRightString(x, y, text)
        pdf_canvas.save()
        buffer.seek(0)
        return PdfReader(buffer).pages[0]


class FolderDialogService:
    """フォルダ選択ポップアップの表示を担当する"""

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.withdraw()

    @property
    def root(self) -> tk.Tk:
        return self._root

    def select_input_folder(self) -> Optional[Path]:
        selected = filedialog.askdirectory(
            parent=self._root,
            title="集約するPDFが入っているフォルダを選択してください",
        )
        return Path(selected) if selected else None

    def select_output_folder(self) -> Optional[Path]:
        selected = filedialog.askdirectory(
            parent=self._root,
            title="出力先フォルダを選択してください",
        )
        return Path(selected) if selected else None

    def close(self) -> None:
        self._root.destroy()


class _NumberingInputDialog(simpledialog.Dialog):
    """ページ番号設定(開始ページ・開始番号)を入力させるポップアップ"""

    def __init__(self, parent: tk.Misc, total_pages: int) -> None:
        self._total_pages = total_pages
        self._start_page_var: tk.StringVar = tk.StringVar()
        self._start_number_var: tk.StringVar = tk.StringVar(value="1")
        self.result_config: Optional[NumberingConfig] = None
        super().__init__(parent, title="ページ番号設定")

    def body(self, master: tk.Frame) -> tk.Widget:
        tk.Label(master, text=f"総ページ数: {self._total_pages}").grid(
            row=0, column=0, columnspan=2, pady=(0, 8)
        )
        tk.Label(master, text="番号を入れ始めるページ:").grid(row=1, column=0, sticky="w")
        entry_page = tk.Entry(master, textvariable=self._start_page_var)
        entry_page.grid(row=1, column=1)
        tk.Label(master, text="そのページの最初の番号:").grid(row=2, column=0, sticky="w")
        tk.Entry(master, textvariable=self._start_number_var).grid(row=2, column=1)
        return entry_page

    def validate(self) -> bool:
        try:
            start_page = int(self._start_page_var.get())
            start_number = int(self._start_number_var.get())
            config = NumberingConfig(start_page=start_page, start_number=start_number)
        except (TypeError, ValueError) as error:
            messagebox.showerror("入力エラー", str(error), parent=self)
            return False

        if config.start_page > self._total_pages:
            messagebox.showerror("入力エラー", "開始ページが総ページ数を超えています", parent=self)
            return False

        self.result_config = config
        return True


class NumberingInputService:
    """ページ番号設定入力ポップアップの呼び出し窓口"""

    def prompt(self, parent: tk.Misc, total_pages: int) -> Optional[NumberingConfig]:
        dialog = _NumberingInputDialog(parent, total_pages)
        return dialog.result_config


class OutputFileNameInputService:
    """出力するPDFのファイル名を入力させるポップアップの呼び出し窓口"""

    _DEFAULT_FILE_NAME: str = "aggregated.pdf"

    def prompt(self, parent: tk.Misc) -> Optional[str]:
        file_name = simpledialog.askstring(
            "出力ファイル名",
            "出力するPDFのファイル名を入力してください",
            initialvalue=self._DEFAULT_FILE_NAME,
            parent=parent,
        )
        if file_name is None:
            return None

        file_name = file_name.strip()
        if not file_name:
            return None
        if not file_name.lower().endswith(".pdf"):
            file_name += ".pdf"
        return file_name
