# sharepoint_link_exporter

指定したSharePointフォルダ配下(サブフォルダ含む)にある全ファイルのリンク(webUrl)を取得し、Excelファイルに一覧出力するツールです。

## 事前準備

### 1. Azure ADアプリの登録

Microsoft Entra ID(旧Azure AD)でアプリを登録し、以下を設定してください。

- APIのアクセス許可: Microsoft Graph の `Sites.Read.All`(アプリケーションのアクセス許可)を追加し、管理者の同意を付与
- 「証明書とシークレット」からクライアントシークレットを発行
- 「概要」からテナントID・クライアントIDを控える

### 2. 環境変数の設定

```bash
cd sharepoint_link_exporter/src
cp .env.example .env
```

`.env` を編集し、以下を設定してください。

| 変数名 | 内容 | 例 |
|---|---|---|
| `SP_TENANT_ID` | テナントID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `SP_CLIENT_ID` | アプリのクライアントID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `SP_CLIENT_SECRET` | クライアントシークレット | `xxxxxxxxxxxxxxxxxxxxxxxx` |
| `SP_HOSTNAME` | SharePointのホスト名 | `contoso.sharepoint.com` |
| `SP_SITE_PATH` | サイトの相対パス | `/sites/YourSiteName` |
| `SP_FOLDER_PATH` | リンクを取得したいフォルダのパス(ドキュメントライブラリ起点) | `Shared Documents/対象フォルダ` |
| `SP_OUTPUT_EXCEL_PATH` | 出力先Excelファイルパス(省略可、既定は `sharepoint_links.xlsx`) | `output/links.xlsx` |

`.env` には認証情報が含まれるため、Gitにコミットしないでください(`.gitignore` 済み)。

### 3. パッケージインストール

```bash
pip install -r requirements.txt
```

## 実行方法

```bash
python main.py
```

指定フォルダ配下の全ファイル(サブフォルダ含む)のリンクをExcelファイルに出力します。

## 出力Excelの列

| 列 | 内容 |
|---|---|
| ファイル名 | ファイル名 |
| フォルダパス | ファイルが存在するフォルダのパス |
| リンクURL | ファイルへのリンク(ハイパーリンク付き) |
| サイズ(バイト) | ファイルサイズ |

## ファイル構成

```
sharepoint_link_exporter/
├── src/
│   ├── main.py            # エントリーポイント
│   ├── models.py          # 値オブジェクト(SharePointConfig, FileLinkInfo)
│   ├── services.py        # 認証・API通信・ファイル探索・Excel出力の各サービス
│   ├── requirements.txt
│   └── .env.example
└── .gitignore
```
