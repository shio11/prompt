# html_aggregator

フォルダまたはZIPアーカイブ内に格納された、階層が分かれたメインHTMLと複数のサブHTMLを読み込み、
本文テキストを抽出して1つのファイル(テキストまたはPDF)に集約するツールです。
Copilot Studioの質問ノードでアップロードされたファイルをPower Automate/Azure Functions経由で
本ロジックに渡し、集約結果を生成AIノードでの要約やナレッジソースとして利用することを想定しています。

## 機能

- 入力は**展開済みフォルダ**と**ZIPファイル**の両方に対応(ZIPは一時ディレクトリへ安全に展開。Zip Slip対策済み)
- 入力元をフォルダ階層に関わらず再帰的に探索し、HTMLファイルを列挙
- ファイル名(`index.html` など)からメインHTMLを判定し、残りをサブHTMLとして扱う
- メインHTML内の `<a href>` の出現順にサブHTMLを並び替え
- 各HTMLから `<title>` と本文テキストを抽出し、どのファイル由来か分かる見出し付きで1ファイルに集約
- 出力先の拡張子が `.pdf` の場合、各セクションへジャンプできる**しおり(ブックマーク)付きPDF**として出力
  (`.pdf` 以外を指定した場合はテキストファイルとして出力)

## セットアップ

```bash
cd html_aggregator/src
pip install -r requirements.txt
```

## 実行方法

```bash
python main.py <input_path> <output_path>
```

- `<input_path>`: メインHTMLとサブHTMLを含む、展開済みフォルダまたはZIPファイルのパス
- `<output_path>`: 集約結果の出力先パス
  - `.pdf` を指定 → しおり付きPDFとして出力
  - それ以外(`.txt` など) → プレーンテキストとして出力

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
