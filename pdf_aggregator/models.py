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


@dataclass(frozen=True)
class NumberingConfig:
    """ページ番号の付与開始位置と開始番号を表す値オブジェクト"""

    start_page: int
    start_number: int

    def __post_init__(self) -> None:
        if self.start_page < 1:
            raise ValueError("start_page は1以上である必要があります")
        if self.start_number < 1:
            raise ValueError("start_number は1以上である必要があります")
