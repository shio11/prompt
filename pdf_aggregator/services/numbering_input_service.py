import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import Optional

from models.numbering_config import NumberingConfig


class _NumberingInputDialog(simpledialog.Dialog):
    """ページ番号設定(開始ページ・開始番号)を入力させるポップアップ"""

    def __init__(self, parent: tk.Misc, total_pages: int) -> None:
        self._total_pages = total_pages
        self._start_page_var: tk.StringVar = tk.StringVar()
        self._start_number_var: tk.StringVar = tk.StringVar(value="1")
        self.result_config: Optional[NumberingConfig] = None
        super().__init__(parent, title="ページ番号設定")

    def body(self, master: tk.Frame) -> tk.Widget:
        tk.Label(master, text=f"総ページ数: {self._total_pages}").grid(
            row=0, column=0, columnspan=2, pady=(0, 8)
        )
        tk.Label(master, text="番号を入れ始めるページ:").grid(row=1, column=0, sticky="w")
        entry_page = tk.Entry(master, textvariable=self._start_page_var)
        entry_page.grid(row=1, column=1)
        tk.Label(master, text="そのページの最初の番号:").grid(row=2, column=0, sticky="w")
        tk.Entry(master, textvariable=self._start_number_var).grid(row=2, column=1)
        return entry_page

    def validate(self) -> bool:
        try:
            start_page = int(self._start_page_var.get())
            start_number = int(self._start_number_var.get())
            config = NumberingConfig(start_page=start_page, start_number=start_number)
        except (TypeError, ValueError) as error:
            messagebox.showerror("入力エラー", str(error), parent=self)
            return False

        if config.start_page > self._total_pages:
            messagebox.showerror("入力エラー", "開始ページが総ページ数を超えています", parent=self)
            return False

        self.result_config = config
        return True


class NumberingInputService:
    """ページ番号設定入力ポップアップの呼び出し窓口"""

    def prompt(self, parent: tk.Misc, total_pages: int) -> Optional[NumberingConfig]:
        dialog = _NumberingInputDialog(parent, total_pages)
        return dialog.result_config
