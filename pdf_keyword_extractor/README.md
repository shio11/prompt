# pdf_keyword_extractor

指定したPDFファイルから任意のキーワードに関連する内容を検索し、前後の文脈とページ番号を付けてExcelファイルに出力するツールです。
Copilot in Excelで行っている「外部PDFからキーワード関連の内容を抽出する」操作を、ローカルのPythonのみ（外部AI APIなし）で再現します。

## 機能

- ポップアップで対象PDFファイルを選択
- ポップアップで検索キーワードを入力
- PDF内の全ページからキーワードに一致する箇所を検索し、前後の文脈を抽出
- ポップアップで出力先フォルダ・ファイル名を指定し、結果をExcel(.xlsx)に出力
  - 出力列: キーワード / ページ番号 / 抽出内容 / PDFファイル / Copilot意味理解結果(空欄)

## セットアップ

```bash
cd pdf_keyword_extractor/src
pip install -r requirements.txt
```

## 実行方法

```bash
python main.py
```

1. 検索対象のPDFファイルを選択
2. 検索したいキーワードを入力
3. 出力先フォルダを選択
4. 出力するExcelファイル名を入力

キーワードに一致する箇所が見つからない場合は、その旨がポップアップで表示され、Excel出力は行われません。

## ハイブリッド運用フロー(意味理解ベースの抽出)

本ツールはキーワードの機械的な一致検索のみを行い、意味理解ベースの抽出はAPI申請なしで使えるCopilot in Excelに任せる、以下の2段階フローを想定しています。

1. **Python(機械処理)**: 本ツールを実行し、キーワード一致箇所と空欄の「Copilot意味理解結果」列を持つExcelを出力する
2. **手動(Copilot)**: 出力されたExcelを開き、各行についてCopilot in Excelに元PDFを参照させながら「Copilot意味理解結果」列へ関連内容の要約・補足を入力してもらう

手動入力が完了した時点でそのExcelファイルがそのまま最終成果物となり、Python側での再読み込み・後処理は行いません。

## ファイル構成

```
pdf_keyword_extractor/
├── README.md
└── src/
    ├── main.py            # エントリーポイント
    ├── models.py          # 値オブジェクト(PageText, KeywordMatch, ExtractionResult)
    ├── services.py         # PDF抽出・キーワード検索・Excel出力・ダイアログ操作の各サービス
    └── requirements.txt
```

## 制限事項・今後の拡張

- Python側で行うのはキーワードの完全一致（大文字小文字は区別しない）による単純検索のみです。意味理解ベースの抽出は上記フローの通りCopilotへの手動操作に委ねています。
- 完全自動化したい場合は、「Copilot意味理解結果」列への入力処理をAzure OpenAI Service等のLLM API呼び出しに置き換えることで対応できます（別途Azure申請要）。
