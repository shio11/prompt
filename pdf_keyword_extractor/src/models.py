from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class PageText:
    """PDFの1ページ分のテキストを表す値オブジェクト"""

    page_number: int
    text: str

    def __post_init__(self) -> None:
        if self.page_number < 1:
            raise ValueError("page_number は1以上である必要があります")


@dataclass(frozen=True)
class KeywordMatch:
    """PDF内で検出されたキーワード一致箇所を表す値オブジェクト"""

    keyword: str
    page_number: int
    context: str

    def __post_init__(self) -> None:
        if not self.keyword:
            raise ValueError("keyword は空にできません")
        if self.page_number < 1:
            raise ValueError("page_number は1以上である必要があります")


class ExtractionResult:
    """1つのPDFに対するキーワード抽出結果の集合を管理するクラス"""

    def __init__(self, source_path: Path, keyword: str) -> None:
        self.source_path = source_path
        self.keyword = keyword
        self._matches: List[KeywordMatch] = []

    @property
    def source_path(self) -> Path:
        return self._source_path

    @source_path.setter
    def source_path(self, value: Path) -> None:
        if not isinstance(value, Path):
            raise TypeError("source_path は pathlib.Path である必要があります")
        self._source_path = value

    @property
    def keyword(self) -> str:
        return self._keyword

    @keyword.setter
    def keyword(self, value: str) -> None:
        if not value:
            raise ValueError("keyword は空にできません")
        self._keyword = value

    @property
    def matches(self) -> List[KeywordMatch]:
        return list(self._matches)

    def add_match(self, match: KeywordMatch) -> None:
        if match.keyword != self._keyword:
            raise ValueError("match.keyword がこの結果の keyword と一致しません")
        self._matches.append(match)

    def __repr__(self) -> str:
        return (
            f"ExtractionResult(source_path={self._source_path!r}, "
            f"keyword={self._keyword!r}, matches={len(self._matches)}件)"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExtractionResult):
            return NotImplemented
        return (
            self._source_path == other._source_path
            and self._keyword == other._keyword
            and self._matches == other._matches
        )
