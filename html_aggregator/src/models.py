from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Tuple


class PageRole(Enum):
    """HTMLページがメインかサブかを表す種別"""

    MAIN = auto()
    SUB = auto()


@dataclass(frozen=True)
class HtmlPage:
    """1つのHTMLファイルから抽出したタイトルと本文テキストを表す値オブジェクト"""

    relative_path: Path
    role: PageRole
    title: str
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.relative_path, Path):
            raise TypeError("relative_path は pathlib.Path である必要があります")
        if not self.text.strip():
            raise ValueError(f"本文が空です: {self.relative_path}")

    @property
    def role_label(self) -> str:
        return "メイン" if self.role is PageRole.MAIN else "サブ"


@dataclass(frozen=True)
class AggregationConfig:
    """集約処理全体で使う設定値を表す値オブジェクト"""

    main_file_candidates: Tuple[str, ...] = ("index.html", "main.html", "top.html")
    encoding: str = "utf-8"
    section_separator: str = "\n\n" + "-" * 40 + "\n\n"

    def __post_init__(self) -> None:
        if not self.main_file_candidates:
            raise ValueError("main_file_candidates は1件以上指定してください")
        if not self.encoding:
            raise ValueError("encoding を空にはできません")
