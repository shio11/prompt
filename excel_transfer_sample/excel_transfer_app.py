# -*- coding: utf-8 -*-
"""Excel転記アプリ（GUI: tkinter）

外部ライブラリ:
- tkinter（標準ライブラリ）
- openpyxl

概要:
    template.xlsx の「設定」シートから対象資料の一覧を読み込み、
    チェックボックスでON/OFFされた資料について source_data.xlsx から
    明細を読み込んで一覧表示する。「Excelに出力」ボタンで、表示中の
    明細を template.xlsx の「明細」シートに書き戻す。
"""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import NamedTuple, Union

from openpyxl import load_workbook

TEMPLATE_FILENAME = "template.xlsx"
SETTINGS_SHEET = "設定"
DETAIL_SHEET = "明細"

# Excelセルに入りうる値の型（anyは使わない）
CellValue = Union[str, int, float, None]


class SourceConfig(NamedTuple):
    key: str
    display_name: str
    checked: bool
    source_file: str
    source_sheet: str


class DetailRow(NamedTuple):
    display_name: str
    date: CellValue
    category: CellValue
    amount: CellValue


# ---------------------------------------------------------------------------
# Excel入出力
# ---------------------------------------------------------------------------


def load_source_configs(template_path: Path) -> list[SourceConfig]:
    """「設定」シートから対象資料の一覧を読み込む。"""
    if not template_path.exists():
        raise FileNotFoundError(f"テンプレートファイルが見つかりません: {template_path}")

    workbook = load_workbook(template_path, data_only=False)
    try:
        if SETTINGS_SHEET not in workbook.sheetnames:
            raise ValueError(f"シート「{SETTINGS_SHEET}」が見つかりません。")
        sheet = workbook[SETTINGS_SHEET]

        configs: list[SourceConfig] = []
        row = 4
        while sheet.cell(row=row, column=1).value:
            configs.append(
                SourceConfig(
                    key=str(sheet.cell(row=row, column=1).value),
                    display_name=str(sheet.cell(row=row, column=2).value),
                    checked=bool(sheet.cell(row=row, column=3).value),
                    source_file=str(sheet.cell(row=row, column=4).value),
                    source_sheet=str(sheet.cell(row=row, column=5).value),
                )
            )
            row += 1
        return configs
    finally:
        workbook.close()


def load_detail_rows(source_path: Path, sheet_name: str, display_name: str) -> list[DetailRow]:
    """入力元ファイルの指定シートから明細行を読み込む。"""
    if not source_path.exists():
        raise FileNotFoundError(f"入力元ファイルが見つかりません: {source_path}")

    workbook = load_workbook(source_path, data_only=True)
    try:
        if sheet_name not in workbook.sheetnames:
            raise ValueError(f"シート「{sheet_name}」が {source_path.name} に見つかりません。")
        sheet = workbook[sheet_name]

        rows: list[DetailRow] = []
        row = 4
        while sheet.cell(row=row, column=1).value is not None:
            rows.append(
                DetailRow(
                    display_name=display_name,
                    date=sheet.cell(row=row, column=1).value,
                    category=sheet.cell(row=row, column=2).value,
                    amount=sheet.cell(row=row, column=3).value,
                )
            )
            row += 1
        return rows
    finally:
        workbook.close()


def write_details_to_template(template_path: Path, details: list[DetailRow]) -> None:
    """「明細」シートのデータ行（4行目以降）を全て置き換える。

    「サマリー」シートの数式・「設定」シートの内容には触れない。
    """
    if not template_path.exists():
        raise FileNotFoundError(f"テンプレートファイルが見つかりません: {template_path}")

    workbook = load_workbook(template_path, data_only=False)
    try:
        if DETAIL_SHEET not in workbook.sheetnames:
            raise ValueError(f"シート「{DETAIL_SHEET}」が見つかりません。")
        sheet = workbook[DETAIL_SHEET]

        if sheet.max_row >= 4:
            sheet.delete_rows(4, sheet.max_row - 3)

        for offset, detail in enumerate(details):
            row = 4 + offset
            sheet.cell(row=row, column=1, value=detail.display_name)
            sheet.cell(row=row, column=2, value=detail.date)
            sheet.cell(row=row, column=3, value=detail.category)
            sheet.cell(row=row, column=4, value=detail.amount)

        workbook.save(template_path)
    finally:
        workbook.close()


# ---------------------------------------------------------------------------
# 計算ロジック（純粋関数）
# ---------------------------------------------------------------------------


def filter_checked_configs(
    configs: list[SourceConfig], checked_map: dict[str, bool]
) -> list[SourceConfig]:
    """チェックONの資料設定のみを返す。"""
    return [config for config in configs if checked_map.get(config.key, False)]


def calculate_total(details: list[DetailRow]) -> float:
    """明細行から金額の合計を計算する。"""
    return sum(detail.amount for detail in details if isinstance(detail.amount, (int, float)))


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------


class ExcelTransferApp:
    def __init__(self, root: tk.Tk, template_path: Path) -> None:
        self.root = root
        self.template_path = template_path
        self.template_dir = template_path.parent
        self.configs: list[SourceConfig] = []
        self.check_vars: dict[str, tk.BooleanVar] = {}
        self.current_details: list[DetailRow] = []

        root.title("Excel転記アプリ")
        root.geometry("640x420")

        self.checkbox_frame = ttk.LabelFrame(root, text="対象資料")
        self.checkbox_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        columns = ("display_name", "date", "category", "amount")
        headings = {"display_name": "資料名", "date": "日付", "category": "費目", "amount": "金額"}
        self.tree = ttk.Treeview(root, columns=columns, show="headings", height=12)
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=140, anchor="center")
        self.tree.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        self.total_label = ttk.Label(root, text="合計金額: -", font=("Arial", 11, "bold"))
        self.total_label.grid(row=2, column=0, sticky="w", padx=10)

        self.output_button = ttk.Button(root, text="Excelに出力", command=self.on_output)
        self.output_button.grid(row=3, column=0, pady=10)

        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        self._load_initial_settings()

    def _load_initial_settings(self) -> None:
        try:
            self.configs = load_source_configs(self.template_path)
        except (FileNotFoundError, ValueError) as exc:
            messagebox.showerror("読み込みエラー", str(exc))
            return

        for i, config in enumerate(self.configs):
            var = tk.BooleanVar(value=config.checked)
            self.check_vars[config.key] = var
            checkbox = ttk.Checkbutton(
                self.checkbox_frame,
                text=config.display_name,
                variable=var,
                command=self.on_check_changed,
            )
            checkbox.grid(row=0, column=i, padx=8, pady=4)

        self.refresh_details()

    def _current_checked_map(self) -> dict[str, bool]:
        return {key: var.get() for key, var in self.check_vars.items()}

    def on_check_changed(self) -> None:
        self.refresh_details()

    def refresh_details(self) -> None:
        checked_configs = filter_checked_configs(self.configs, self._current_checked_map())

        details: list[DetailRow] = []
        try:
            for config in checked_configs:
                source_path = self.template_dir / config.source_file
                details.extend(
                    load_detail_rows(source_path, config.source_sheet, config.display_name)
                )
        except (FileNotFoundError, ValueError) as exc:
            messagebox.showerror("読み込みエラー", str(exc))
            return

        self.current_details = details
        self.tree.delete(*self.tree.get_children())
        for detail in details:
            amount_text = f"{detail.amount:,}" if isinstance(detail.amount, (int, float)) else detail.amount
            self.tree.insert(
                "", "end", values=(detail.display_name, detail.date, detail.category, amount_text)
            )

        total = calculate_total(details)
        self.total_label.config(text=f"合計金額: {total:,.0f} 円")

    def on_output(self) -> None:
        confirmed = messagebox.askyesno(
            "確認", f"{self.template_path.name} に上書き保存します。よろしいですか？"
        )
        if not confirmed:
            return

        try:
            write_details_to_template(self.template_path, self.current_details)
        except (FileNotFoundError, ValueError, PermissionError) as exc:
            messagebox.showerror("出力エラー", str(exc))
            return

        messagebox.showinfo("完了", "Excelへの出力が完了しました。")


def main() -> None:
    template_path = Path(__file__).resolve().parent / TEMPLATE_FILENAME
    root = tk.Tk()
    ExcelTransferApp(root, template_path)
    root.mainloop()


if __name__ == "__main__":
    main()
