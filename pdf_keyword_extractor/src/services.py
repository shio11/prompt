import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
from typing import List, Optional, Pattern

import pdfplumber
from openpyxl import Workbook

from models import ExtractionResult, KeywordMatch, PageText


class PdfTextExtractionService:
    """PDFファイルからページ単位でテキストを抽出する責務を持つ"""

    def extract_pages(self, pdf_path: Path) -> List[PageText]:
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"PDFファイルを指定してください: {pdf_path}")
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDFファイルが見つかりません: {pdf_path}")

        pages: List[PageText] = []
        with pdfplumber.open(pdf_path) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append(PageText(page_number=index, text=text))
        return pages


class KeywordSearchService:
    """テキスト群からキーワードに関連する前後文脈を検索する責務を持つ"""

    def __init__(self, context_chars: int = 50) -> None:
        self.context_chars = context_chars

    @property
    def context_chars(self) -> int:
        return self._context_chars

    @context_chars.setter
    def context_chars(self, value: int) -> None:
        if value < 0:
            raise ValueError("context_chars は0以上である必要があります")
        self._context_chars = value

    def search(
        self, pages: List[PageText], keyword: str, source_path: Path
    ) -> ExtractionResult:
        if not keyword:
            raise ValueError("keyword は空にできません")

        result = ExtractionResult(source_path=source_path, keyword=keyword)
        pattern: Pattern[str] = re.compile(re.escape(keyword), re.IGNORECASE)

        for page in pages:
            for found in pattern.finditer(page.text):
                start = max(0, found.start() - self._context_chars)
                end = min(len(page.text), found.end() + self._context_chars)
                context = page.text[start:end].replace("\n", " ").strip()
                result.add_match(
                    KeywordMatch(
                        keyword=keyword,
                        page_number=page.page_number,
                        context=context,
                    )
                )
        return result


class ExcelExportService:
    """キーワード抽出結果をExcelファイルへ出力する責務を持つ"""

    _HEADER = ["キーワード", "ページ番号", "抽出内容", "PDFファイル"]

    def export(self, result: ExtractionResult, output_path: Path) -> None:
        if output_path.suffix.lower() != ".xlsx":
            raise ValueError(f".xlsx ファイルを指定してください: {output_path}")

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "KeywordMatches"
        sheet.append(self._HEADER)
        for match in result.matches:
            sheet.append(
                [match.keyword, match.page_number, match.context, str(result.source_path)]
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(output_path)


class FileDialogService:
    """PDF選択・キーワード入力・出力先選択のポップアップ操作をまとめて担当する"""

    _DEFAULT_OUTPUT_FILE_NAME = "keyword_extraction.xlsx"

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.withdraw()

    @property
    def root(self) -> tk.Tk:
        return self._root

    def select_pdf_file(self) -> Optional[Path]:
        selected = filedialog.askopenfilename(
            parent=self._root,
            title="抽出対象のPDFファイルを選択してください",
            filetypes=[("PDF files", "*.pdf")],
        )
        return Path(selected) if selected else None

    def input_keyword(self) -> Optional[str]:
        keyword = simpledialog.askstring(
            "キーワード入力",
            "検索したいキーワードを入力してください",
            parent=self._root,
        )
        return keyword.strip() if keyword and keyword.strip() else None

    def select_output_folder(self) -> Optional[Path]:
        selected = filedialog.askdirectory(
            parent=self._root,
            title="出力先フォルダを選択してください",
        )
        return Path(selected) if selected else None

    def input_output_file_name(self) -> Optional[str]:
        file_name = simpledialog.askstring(
            "出力ファイル名",
            "出力するExcelファイル名を入力してください",
            initialvalue=self._DEFAULT_OUTPUT_FILE_NAME,
            parent=self._root,
        )
        if file_name is None:
            return None

        file_name = file_name.strip()
        if not file_name:
            return None
        if not file_name.lower().endswith(".xlsx"):
            file_name += ".xlsx"
        return file_name

    def show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message, parent=self._root)

    def show_warning(self, title: str, message: str) -> None:
        messagebox.showwarning(title, message, parent=self._root)

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message, parent=self._root)

    def close(self) -> None:
        self._root.destroy()
