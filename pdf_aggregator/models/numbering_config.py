from dataclasses import dataclass


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
