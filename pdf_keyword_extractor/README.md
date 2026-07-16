# pdf_keyword_extractor

指定したPDFファイルから任意のキーワードに関連する内容を検索し、前後の文脈とページ番号を付けてExcelファイルに出力するツールです。
Copilot in Excelで行っている「外部PDFからキーワード関連の内容を抽出する」操作を、ローカルのPythonのみ（外部AI APIなし）で再現します。

## 機能

- ポップアップで対象PDFファイルを選択
- ポップアップで検索キーワードを入力
- PDF内の全ページからキーワードに一致する箇所を検索し、前後の文脈を抽出
- ポップアップで出力先フォルダ・ファイル名を指定し、結果をExcel(.xlsx)に出力
  - 出力列: キーワード / ページ番号 / 抽出内容 / PDFファイル

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

- 現時点ではキーワードの完全一致（大文字小文字は区別しない）による単純検索のみで、Copilotのような文脈理解に基づく関連情報の抽出は行いません。
- 意味理解ベースの抽出まで再現したい場合は、Azure OpenAI Service等のLLM APIとの連携が必要です（別途申請要）。
