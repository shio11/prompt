from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ItemType(Enum):
    """Box上のアイテム種別"""

    FOLDER = "folder"
    FILE = "file"


@dataclass(frozen=True)
class BoxCredentials:
    """Box APIへの認証情報を表す値オブジェクト"""

    developer_token: str

    def __post_init__(self) -> None:
        if not self.developer_token or not self.developer_token.strip():
            raise ValueError("developer_tokenは空にできません")


@dataclass(frozen=True)
class BoxItem:
    """Box上のフォルダ・ファイル1件を表す値オブジェクト"""

    item_id: str
    name: str
    item_type: ItemType

    def __post_init__(self) -> None:
        if not self.item_id or not self.item_id.strip():
            raise ValueError("item_idは空にできません")
        if not self.name or not self.name.strip():
            raise ValueError("nameは空にできません")
        if not isinstance(self.item_type, ItemType):
            raise TypeError("item_typeはItemType型である必要があります")

    @property
    def is_folder(self) -> bool:
        return self.item_type is ItemType.FOLDER
