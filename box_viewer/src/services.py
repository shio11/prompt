from __future__ import annotations

import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk
from typing import Dict, List, Optional

from boxsdk import Client, OAuth2

from models import BoxCredentials, BoxItem, ItemType


class BoxAuthenticator:
    """Box認証情報からAPIクライアントを組み立てる責務を持つクラス"""

    def __init__(self, credentials: BoxCredentials) -> None:
        self._credentials = credentials
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _build_client(self) -> Client:
        oauth = OAuth2(
            client_id="",
            client_secret="",
            access_token=self._credentials.developer_token,
        )
        return Client(oauth)


class BoxRepository:
    """
    Box APIへの読み取り専用アクセスを担うクラス。
    フォルダ内容の一覧取得と、ファイルの読み取り専用プレビューURL取得のみを提供し、
    アップロード・更新・削除等の書き込み系操作は一切扱わない。
    """

    def __init__(self, client: Client) -> None:
        self._client = client

    def list_folder_items(self, folder_id: str) -> List[BoxItem]:
        folder = self._client.folder(folder_id=folder_id)
        items: List[BoxItem] = []
        for entry in folder.get_items():
            item_type = ItemType.FOLDER if entry.type == "folder" else ItemType.FILE
            items.append(BoxItem(item_id=entry.id, name=entry.name, item_type=item_type))
        return items

    def get_preview_url(self, file_id: str) -> str:
        return self._client.file(file_id=file_id).get_embed_url()


class ReadOnlyFileOpener:
    """Box上のファイルを読み取り専用プレビューとして既定のブラウザで開く責務を持つクラス"""

    def open_preview(self, preview_url: str) -> None:
        webbrowser.open(preview_url, new=2)


class BoxExplorerWindow:
    """
    Box内のフォルダ階層をツリー表示し、右クリックメニューから資料を選択して
    読み取り専用プレビューで開くGUIを提供するクラス。
    Box APIとのやり取りはBoxRepository/ReadOnlyFileOpenerへ委譲する（コンポジション）。
    """

    def __init__(
        self,
        repository: BoxRepository,
        opener: ReadOnlyFileOpener,
        root_folder_id: str = "0",
    ) -> None:
        self._repository = repository
        self._opener = opener
        self._folder_stack: List[str] = [root_folder_id]
        self._items_by_row: Dict[str, BoxItem] = {}

        self._root = tk.Tk()
        self._root.title("Box資料ビューア（読み取り専用）")
        self._root.geometry("640x420")

        self._back_button = ttk.Button(self._root, text="← 戻る", command=self._go_back)
        self._back_button.pack(fill=tk.X)

        self._tree = ttk.Treeview(self._root, columns=("type",), show="tree headings")
        self._tree.heading("#0", text="名前")
        self._tree.heading("type", text="種別")
        self._tree.pack(fill=tk.BOTH, expand=True)

        self._context_menu = tk.Menu(self._root, tearoff=0)

        self._tree.bind("<Button-3>", self._on_right_click)
        self._tree.bind("<Button-2>", self._on_right_click)
        self._tree.bind("<Double-1>", self._on_double_click)

    def run(self) -> None:
        self._load_current_folder()
        self._root.mainloop()

    def _current_folder_id(self) -> str:
        return self._folder_stack[-1]

    def _load_current_folder(self) -> None:
        self._tree.delete(*self._tree.get_children())
        self._items_by_row.clear()
        try:
            items = self._repository.list_folder_items(self._current_folder_id())
        except Exception as error:
            messagebox.showerror("エラー", f"フォルダの取得に失敗しました: {error}")
            return
        for item in items:
            type_label = "フォルダ" if item.is_folder else "ファイル"
            row_id = self._tree.insert("", tk.END, text=item.name, values=(type_label,))
            self._items_by_row[row_id] = item

    def _on_right_click(self, event: "tk.Event[tk.Misc]") -> None:
        row_id = self._tree.identify_row(event.y)
        if not row_id:
            return
        self._tree.selection_set(row_id)
        item = self._items_by_row.get(row_id)
        if item is None:
            return
        self._context_menu.delete(0, tk.END)
        if item.is_folder:
            self._context_menu.add_command(label="開く", command=lambda: self._enter_folder(item))
        else:
            self._context_menu.add_command(
                label="開く（読み取り専用）", command=lambda: self._open_read_only(item)
            )
        self._context_menu.tk_popup(event.x_root, event.y_root)

    def _on_double_click(self, event: "tk.Event[tk.Misc]") -> None:
        row_id = self._tree.identify_row(event.y)
        if not row_id:
            return
        item = self._items_by_row.get(row_id)
        if item is None:
            return
        if item.is_folder:
            self._enter_folder(item)
        else:
            self._open_read_only(item)

    def _enter_folder(self, item: BoxItem) -> None:
        self._folder_stack.append(item.item_id)
        self._load_current_folder()

    def _go_back(self) -> None:
        if len(self._folder_stack) > 1:
            self._folder_stack.pop()
            self._load_current_folder()

    def _open_read_only(self, item: BoxItem) -> None:
        try:
            preview_url = self._repository.get_preview_url(item.item_id)
        except Exception as error:
            messagebox.showerror("エラー", f"プレビューの取得に失敗しました: {error}")
            return
        self._opener.open_preview(preview_url)
