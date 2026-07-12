from pathlib import Path
from typing import List

from pypdf import PdfWriter


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
