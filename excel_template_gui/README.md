# excel_template_gui

Excelテンプレートへの入力をGUIで行うアプリ。

## 機能

- 起動時に `template.xlsx`(なければ自動生成)を読み込み、項目を入力欄として表示
- 「外部ファイルを読み込む」ボタン: 選択したExcel(.xlsx)の1行目(ヘッダー)とテンプレートの項目名を照合し、一致する値を入力欄へ反映
- 「出力する」ボタン: 入力欄の内容をテンプレート形式のExcelとして指定ファイルへ保存

## 項目

氏名 / フリガナ / 会社名 / 部署 / メールアドレス / 電話番号 / 日付 / 備考

## 実行方法

```bash
uv run excel-template-gui
```

またはファイルパス指定:

```bash
uv run excel_template_gui/main.py
```
