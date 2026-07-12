from typing import List

from pypdf import PdfReader, PdfWriter

from models.pdf_file_info import PdfFileInfo


class PdfMergerService:
    """ソート済みのPDFファイル群を1つのPdfWriterに結合する"""

    def merge(self, sorted_files: List[PdfFileInfo]) -> PdfWriter:
        writer = PdfWriter()
        for info in sorted_files:
            reader = PdfReader(str(info.path))
            for page in reader.pages:
                writer.add_page(page)
        return writer
