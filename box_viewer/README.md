# Box資料ビューア（読み取り専用）

Box内のフォルダ・ファイルをツリー表示し、右クリックメニューから資料を選択して
読み取り専用プレビューで開くGUIツールです。ダウンロードや編集は行わず、
Boxの埋め込みプレビュー（Box Embed）をブラウザで表示するだけなので、
Box上の資料を書き換えてしまう心配がありません。

## 事前準備

1. 依存パッケージのインストール

   `uv` を使う場合は `main.py` にインラインスクリプトメタデータ（PEP 723）で
   依存関係（`boxsdk`）を記載済みのため、`uv run main.py` を実行するだけで
   自動的に依存パッケージがインストールされます。個別にインストールする必要はありません。

   `pip` を使う場合は以下を実行してください。

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

   Windowsのコマンドプロンプトの場合は `set`、PowerShellの場合は `$env:` を使用してください。

## 実行方法

```bash
cd box_viewer/src
uv run main.py
```

`uv` がない場合は事前準備1で `pip install -r requirements.txt` を実行したうえで
`python3 main.py`（Windowsは `python main.py`）を実行してください。

### GUIが起動しない場合

`tkinter` はPython標準ライブラリの一部で、python.orgの通常のWindows/macOSインストーラでは
標準搭載されています。`ModuleNotFoundError: No module named 'tkinter'` が出る場合は、
tkinterを含まない特殊なPythonディストリビューション（一部のLinuxディストリビューションや、
最小構成のPythonビルド）を使用している可能性があるため、OS標準のPythonを使用するか、
`tkinter` を別途インストールしてください（例: Debian/Ubuntuなら `sudo apt install python3-tk`）。

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
  （`get_file_by_id(file_id, fields=["expiring_embed_link"])` で取得する
  Box Embed URL）をブラウザで開く方式のため、ローカルへの誤った複製や
  編集後の再アップロードが発生しません。

## 使用しているBox SDKについて

Box Python SDKは2025年にバージョン体系が再編され、旧来の`boxsdk`（`Client`/
`OAuth2`等のAPI）はv3以前でEOL（サポート終了）となっています。本ツールは
現行の最新メジャーバージョンである **boxsdk v10**（内部モジュール名は
`box_sdk_gen`、`BoxClient`/`BoxDeveloperTokenAuth`を使う新API）を採用しています。

- フォルダ一覧: `client.folders.get_folder_items(folder_id).entries`
- 読み取り専用プレビューURL: `client.files.get_file_by_id(file_id, fields=["expiring_embed_link"]).expiring_embed_link.url`

これらはpip経由でboxsdk v10を実際にインストールし、上記メソッドのシグネチャと
戻り値のスキーマ（`FolderMini`/`FileMini`/`FileFull`等）をこのセッション内で
直接確認したうえで実装しています。ただし実際のBoxアカウント・Developer Tokenに
対する疎通確認までは行えていないため、初回実行時にAPIエラーが出た場合は
エラーメッセージの内容を確認のうえご連絡ください。
