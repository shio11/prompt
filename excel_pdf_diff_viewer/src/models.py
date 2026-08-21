from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Tuple


class FileType(Enum):
    """読み込み対象ファイルの種別"""

    EXCEL = auto()
    PDF = auto()


@dataclass(frozen=True)
class DocumentContent:
    """1つのファイルから抽出したテキスト内容を表す値オブジェクト"""

    file_path: Path
    file_type: FileType
    lines: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.file_path, Path):
            raise TypeError("file_path は pathlib.Path である必要があります")
        if not isinstance(self.file_type, FileType):
            raise TypeError("file_type は FileType である必要があります")

    @property
    def file_name(self) -> str:
        return self.file_path.name

    @property
    def line_count(self) -> int:
        return len(self.lines)


class DiffLineType(Enum):
    """差分比較における1行の種別"""

    EQUAL = auto()
    INSERT = auto()
    DELETE = auto()
    REPLACE = auto()


@dataclass(frozen=True)
class DiffLine:
    """左右2ファイル間の1行分の比較結果を表す値オブジェクト"""

    line_type: DiffLineType
    left_line_no: Optional[int]
    left_text: Optional[str]
    right_line_no: Optional[int]
    right_text: Optional[str]

    def __post_init__(self) -> None:
        if not isinstance(self.line_type, DiffLineType):
            raise TypeError("line_type は DiffLineType である必要があります")
