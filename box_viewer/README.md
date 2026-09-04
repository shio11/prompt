# Box資料ビューア（読み取り専用）

Box内のフォルダ・ファイルをツリー表示し、右クリックメニューから資料を選択して
読み取り専用プレビューで開くGUIツールです。ダウンロードや編集は行わず、
Boxの埋め込みプレビュー（Box Embed）をブラウザで表示するだけなので、
Box上の資料を書き換えてしまう心配がありません。

## 事前準備

1. 依存パッケージのインストール

   ```bash
   cd box_viewer/src
   pip install -r requirements.txt
   ```

2. Box Developer Tokenの取得

   [Box Developer Console](https://app.box.com/developers/console) でアプリを作成し、
   Developer Tokenを発行してください（有効期限は発行後60分程度です）。

3. 環境変数の設定

   ```bash
   export BOX_DEVELOPER_TOKEN="発行したDeveloper Token"
   export BOX_ROOT_FOLDER_ID="0"  # 起点にしたいフォルダID（省略時はルートフォルダ）
   ```

## 実行方法

```bash
cd box_viewer/src
python3 main.py
```

## 使い方

- 一覧内のフォルダ／ファイルを**右クリック**するとコンテキストメニューが開きます。
  - フォルダの場合: 「開く」でそのフォルダに移動します。
  - ファイルの場合: 「開く（読み取り専用）」でBoxの読み取り専用プレビューをブラウザで開きます。
- ダブルクリックでも同様の動作（フォルダ移動／読み取り専用プレビュー表示）を行えます。
- 画面上部の「← 戻る」ボタンで1つ上のフォルダに戻れます。

## 構成

- `src/models.py`: Box認証情報・フォルダ/ファイルアイテムを表す値オブジェクト
- `src/services.py`: Box APIへの読み取り専用アクセス（`BoxRepository`）、
  プレビューを開く処理（`ReadOnlyFileOpener`）、右クリック操作を含むGUI（`BoxExplorerWindow`）
- `src/main.py`: エントリーポイント（依存オブジェクトの組み立てとGUI起動）

## 設計上のポイント

- `BoxRepository` はフォルダ一覧取得とプレビューURL取得のみを提供し、
  アップロード・更新・削除などの書き込み系APIは呼び出さない設計にすることで、
  「読み取り専用」であることをクラスの責務レベルで保証しています。
- プレビューはローカルにファイルをダウンロードせず、Boxの埋め込みプレビュー
  （`get_embed_url()` で取得するBox Embed URL）をブラウザで開く方式のため、
  ローカルへの誤った複製や編集後の再アップロードが発生しません。
