from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PdfFileInfo:
    """1つのPDFファイルとその集約順序番号を表す値オブジェクト"""

    path: Path
    order_number: int

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            raise TypeError("path は pathlib.Path である必要があります")
        if self.order_number < 0:
            raise ValueError("order_number は0以上である必要があります")

    @property
    def file_name(self) -> str:
        return self.path.name
