from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SharePointConfig:
    """SharePoint接続情報とエクスポート対象を表す設定値オブジェクト"""

    tenant_id: str
    client_id: str
    client_secret: str
    site_hostname: str
    site_relative_path: str
    folder_path: str
    output_excel_path: Path

    def __post_init__(self) -> None:
        for field_name in (
            "tenant_id",
            "client_id",
            "client_secret",
            "site_hostname",
            "site_relative_path",
            "folder_path",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} は空でない文字列である必要があります")
        if not isinstance(self.output_excel_path, Path):
            raise TypeError("output_excel_path は pathlib.Path である必要があります")


@dataclass(frozen=True)
class FileLinkInfo:
    """SharePoint上の1ファイルとそのリンク情報を表す値オブジェクト"""

    file_name: str
    folder_path: str
    web_url: str
    size_bytes: int

    def __post_init__(self) -> None:
        if not self.file_name:
            raise ValueError("file_name は空にできません")
        if not self.web_url:
            raise ValueError("web_url は空にできません")
        if self.size_bytes < 0:
            raise ValueError("size_bytes は0以上である必要があります")
