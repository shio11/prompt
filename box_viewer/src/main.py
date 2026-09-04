import os

from models import BoxCredentials
from services import BoxAuthenticator, BoxExplorerWindow, BoxRepository, ReadOnlyFileOpener


def main() -> None:
    developer_token = os.environ.get("BOX_DEVELOPER_TOKEN", "")
    root_folder_id = os.environ.get("BOX_ROOT_FOLDER_ID", "0")

    credentials = BoxCredentials(developer_token=developer_token)
    authenticator = BoxAuthenticator(credentials)
    repository = BoxRepository(authenticator.client)
    opener = ReadOnlyFileOpener()

    window = BoxExplorerWindow(repository=repository, opener=opener, root_folder_id=root_folder_id)
    window.run()


if __name__ == "__main__":
    main()
