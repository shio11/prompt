import os
from pathlib import Path

from dotenv import load_dotenv

from models import SharePointConfig
from services import (
    FileLinkExcelExporter,
    GraphApiClient,
    GraphAuthService,
    SharePointFolderFileRepository,
    SharePointSiteResolver,
)


def _build_config() -> SharePointConfig:
    load_dotenv()
    try:
        return SharePointConfig(
            tenant_id=os.environ["SP_TENANT_ID"],
            client_id=os.environ["SP_CLIENT_ID"],
            client_secret=os.environ["SP_CLIENT_SECRET"],
            site_hostname=os.environ["SP_HOSTNAME"],
            site_relative_path=os.environ["SP_SITE_PATH"],
            folder_path=os.environ["SP_FOLDER_PATH"],
            output_excel_path=Path(os.environ.get("SP_OUTPUT_EXCEL_PATH", "sharepoint_links.xlsx")),
        )
    except KeyError as error:
        raise RuntimeError(f"環境変数 {error} が設定されていません") from error


def main() -> None:
    config = _build_config()

    auth_service = GraphAuthService(config)
    api_client = GraphApiClient(auth_service)
    site_resolver = SharePointSiteResolver(api_client)
    file_repository = SharePointFolderFileRepository(api_client)
    exporter = FileLinkExcelExporter()

    drive_id = site_resolver.resolve_drive_id(config.site_hostname, config.site_relative_path)
    file_links = file_repository.find_all_files(drive_id, config.folder_path)

    if not file_links:
        print("指定フォルダ内にファイルが見つかりませんでした")
        return

    exporter.export(file_links, config.output_excel_path)
    print(f"{len(file_links)}件のリンクを出力しました: {config.output_excel_path}")


if __name__ == "__main__":
    main()
