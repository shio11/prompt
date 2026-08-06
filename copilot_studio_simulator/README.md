# Copilot Studio Agent Simulator

Microsoft Copilot Studioの「エージェント」設定（名前・指示・使用モデル・ナレッジソース・トピック）を
簡易に模擬し、コンソール上で会話をシミュレートするツールです。

## 実行方法

```bash
cd src
python3 main.py
```

`exit` と入力すると終了します。

## 構成

- `src/models.py`: エージェント設定・トピック・アクション等のデータ構造
- `src/services.py`: トピック照合、アクション実行、生成応答、会話シミュレーションのロジック
- `src/main.py`: エントリーポイント（サンプルエージェントの組み立てと対話ループの起動）

## カスタマイズ

`main.py` の `build_sample_agent()` を編集し、`AgentBuilder` でエージェント名・指示・
モデル・ナレッジソース・トピック（トリガーフレーズとアクション）を変更することで、
任意のエージェント設定を模擬できます。
