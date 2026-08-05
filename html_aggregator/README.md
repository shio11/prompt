# html_aggregator

ZIPアーカイブ内に格納された、フォルダが分かれたメインHTMLと複数のサブHTMLを展開し、
本文テキストを抽出して1つのテキストファイルに集約するツールです。
Copilot Studioの質問ノードでアップロードされたZIPをPower Automate/Azure Functions経由で
本ロジックに渡し、集約結果を生成AIノードでの要約に利用することを想定しています。

## 機能

- ZIPファイルを一時ディレクトリへ安全に展開(Zip Slip対策済み)
- 展開先をフォルダ階層に関わらず再帰的に探索し、HTMLファイルを列挙
- ファイル名(`index.html` など)からメインHTMLを判定し、残りをサブHTMLとして扱う
- メインHTML内の `<a href>` の出現順にサブHTMLを並び替え
- 各HTMLから `<title>` と本文テキストを抽出し、どのファイル由来か分かる見出し付きで1ファイルに集約

## セットアップ

```bash
cd html_aggregator/src
pip install -r requirements.txt
```

## 実行方法

```bash
python main.py <input.zip> <output.txt>
```

- `<input.zip>`: メインHTMLとサブHTMLを含むZIPファイルのパス
- `<output.txt>`: 集約結果を書き出すテキストファイルのパス

## ファイル構成

```
html_aggregator/
├── README.md
└── src/
    ├── main.py            # エントリーポイント
    ├── models.py          # 値オブジェクト(HtmlPage, AggregationConfig, PageRole)
    ├── services.py        # ZIP展開・HTML探索・分類・並び替え・抽出・集約の各サービス
    └── requirements.txt
```
