import re
from pathlib import Path
from typing import List, Pattern

from models.pdf_file_info import PdfFileInfo


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
