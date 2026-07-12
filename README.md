# prompt

サンプル

## pdf_aggregator

指定フォルダ内のPDFファイルをファイル名先頭の連番順に結合し、右上に自動でページ番号を付与して出力するツールです。

### 機能

- ポップアップで入力フォルダを選択し、フォルダ内のPDFファイルを集約
  - ファイル名(`01_xxx.pdf` のような `連番_` 形式)の先頭番号順に並び替えて結合
- 結合後PDFの総ページ数を取得し、右上に「現在ページ/総ページ数」を自動付与
  - 付与を開始するページと、そのページの最初の番号はポップアップ入力で指定
- ポップアップで出力フォルダを選択し、結合済みPDFを `aggregated.pdf` として出力

### セットアップ

```bash
cd pdf_aggregator
pip install -r requirements.txt
```

### 実行方法

```bash
python main.py
```

1. 集約したいPDFが入っているフォルダを選択
2. ページ番号を入れ始めるページと、その最初の番号を入力
3. 出力先フォルダを選択

### ファイル構成

```
pdf_aggregator/
├── main.py            # エントリーポイント
├── models.py          # 値オブジェクト(PdfFileInfo, NumberingConfig)
├── services.py        # フォルダ選択・ソート・結合・番号付与の各サービス
└── requirements.txt
```
