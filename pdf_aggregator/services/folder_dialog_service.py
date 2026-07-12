import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from typing import Optional


class FolderDialogService:
    """フォルダ選択ポップアップの表示を担当する"""

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.withdraw()

    @property
    def root(self) -> tk.Tk:
        return self._root

    def select_input_folder(self) -> Optional[Path]:
        selected = filedialog.askdirectory(
            parent=self._root,
            title="集約するPDFが入っているフォルダを選択してください",
        )
        return Path(selected) if selected else None

    def select_output_folder(self) -> Optional[Path]:
        selected = filedialog.askdirectory(
            parent=self._root,
            title="出力先フォルダを選択してください",
        )
        return Path(selected) if selected else None

    def close(self) -> None:
        self._root.destroy()
