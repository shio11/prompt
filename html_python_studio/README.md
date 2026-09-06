# HTML & Python Studio

環境構築なしで、他人のPCのMicrosoft Edge(または他のモダンブラウザ)から
開くだけでHTMLの作成・編集と**その場でのPython実行**ができるツールです。

Pythonの実行には[Pyodide](https://pyodide.org/)(WebAssembly版Pythonランタイム)
をCDNから読み込んで使用します。実行はすべてブラウザ内(クライアントサイド)で
完結するため、開く側のPCにPythonのインストールやサーバーの起動は一切不要です。
初回起動時のみ、ランタイム取得のためインターネット接続が必要です。

## 生成方法

```bash
cd html_python_studio/src
python3 main.py --output ../dist/html_python_studio.html --title "HTML & Python Studio"
```

`--output` を省略すると、実行したディレクトリに `html_python_studio.html`
という単一のHTMLファイルが生成されます。このファイル1つを配布すれば、
相手はEdgeで開くだけで利用できます。

## 生成されたツールの機能

- **HTMLソース編集 + プレビュー**: 左上のテキストエリアにHTMLを書き、
  「プレビュー更新」で右側にライブ表示。「開く」「保存」でローカルの
  `.html` ファイルの読み込み・書き出しが可能。
- **Pythonコンソール**: 左下のテキストエリアにPythonコードを書き、
  「実行」(または Ctrl+Enter)でブラウザ内で実行。標準出力・例外の
  トレースバックを下部に表示。
- **HTMLとPythonの連携**: Pythonコードから `render_html(html)` を呼ぶと
  プレビュー欄とHTMLソースを直接書き換えられ、`get_html()` で現在の
  HTMLソースを取得できます。

## 構成

小規模プロジェクト向け構成(`models.py` / `services.py` / `main.py`)を採用しています。

```
html_python_studio/
├── README.md
├── .gitignore
└── src/
    ├── models.py    # AppConfig / PyodideRuntime / StudioMetadata (値オブジェクト)
    ├── services.py  # StudioHtmlBuilder / StudioClientScript / StudioStyleSheet / StudioFileWriter
    └── main.py      # エントリーポイント(CLI引数解析 → 生成 → 書き出し)
```
