# excel_pdf_diff_viewer

Excel(.xlsx/.xlsm)またはPDFファイルを2つ読み込み、内容をテキスト行として抽出したうえで差分比較し、
左右対比のHTMLレポートとして出力するツールです。

## 機能

- Excelファイル: シートごとに各行のセル値を抽出(`=== Sheet: シート名 ===` 区切り)
- PDFファイル: ページごとにテキストを抽出(`=== Page N ===` 区切り)
- 抽出したテキスト行同士を `difflib` で比較し、以下を色分け表示
  - 変更なし: 白 / 追加: 緑 / 削除:赤 / 変更: 黄
- 比較結果を左右対比形式の単一HTMLファイルとして出力し、既定でブラウザに表示

## セットアップ

```bash
cd excel_pdf_diff_viewer/src
pip install -r requirements.txt
```

## 実行方法

```bash
python main.py <比較元ファイル> <比較先ファイル> [-o 出力先.html] [--no-open]
```

例:

```bash
python main.py before.xlsx after.xlsx -o diff_report.html
python main.py before.pdf after.pdf
```

- `-o` / `--output`: 出力するHTMLファイルのパス(デフォルト: `diff_report.html`)
- `--no-open`: 出力後にブラウザで自動的に開かない

Excel同士・PDF同士だけでなく、Excel と PDF を組み合わせて比較することも可能です。

## ファイル構成

```
excel_pdf_diff_viewer/
├── src/
│   ├── main.py          # エントリーポイント
│   ├── models.py        # 値オブジェクト(DocumentContent, DiffLine 等)
│   ├── services.py       # 抽出・差分計算・HTML生成の各サービス
│   └── requirements.txt
└── README.md
```

## クラス設計の意図

- `ContentExtractor` を抽象基底クラスとし、`ExcelContentExtractor` / `PdfContentExtractor` に
  ファイル形式ごとの抽出ロジックを分離。`ContentExtractorFactory` が拡張子から実装を選択することで、
  対応形式を追加する際も既存コードを変更せず拡張できる構成にしている
- `DocumentContent` / `DiffLine` は `@dataclass(frozen=True)` の値オブジェクトとし、
  生成後に内容が変化しないことを保証
- `DiffService` は `difflib.SequenceMatcher` の差分計算ロジックのみを担当し、
  `HtmlDiffReportRenderer` は差分結果の表示(HTML生成)のみを担当することで、
  比較ロジックと表示ロジックの責務を分離している
