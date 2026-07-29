# excel_prompt_scorer

Excelのエージェントモード（Copilot in Excel 等）に指示するプロンプトを一括採点し、スコアとフィードバックをCSV/Excelに出力するツールです。

ルールベースで以下6つの観点を採点します（合計100点）。

| 採点基準 | 配点 | 内容 |
| --- | --- | --- |
| 対象範囲の明示 | 20点 | シート名・セル範囲・テーブル名などが指定されているか |
| 操作内容の具体性 | 20点 | 「追加する」「集計する」等、実行してほしい操作が具体的か |
| 出力形式の明示 | 15点 | 結果の受け取り方（表・グラフ等）が指定されているか |
| 曖昧な表現の排除 | 20点 | 「適当に」「いい感じに」等の曖昧語が含まれていないか |
| 条件・制約の明示 | 15点 | 条件分岐や除外ルールが必要な場合に明示されているか |
| 情報量 | 10点 | プロンプトの文字数から具体性が十分か |

## セットアップ

```bash
cd excel_prompt_scorer
pip install -r requirements.txt
```

## 実行方法

採点対象のプロンプトを1行1件、CSVまたはExcelファイルにまとめます（既定では `prompt` という列名を参照します）。

```bash
python main.py --input sample_prompts.csv --output result.csv
```

### オプション

- `--input`: 採点対象プロンプトが入ったCSV/Excelファイルのパス（必須）
- `--output`: 採点結果を出力するCSV/Excelファイルのパス（必須。拡張子で形式を判定）
- `--text-column`: プロンプト本文が入っている列名（既定値: `prompt`）
- `--id-column`: プロンプトのID列名（未指定の場合は行番号を使用）

出力ファイルには、`id` / `prompt` / `total_score` / `feedback` に加えて、各採点基準ごとのスコア列が追加されます。

## ファイル構成

```
excel_prompt_scorer/
├── main.py            # エントリーポイント
├── models.py          # 値オブジェクト(Prompt, CriterionResult, EvaluationResult)
├── services.py         # 採点基準(ScoringCriterion群)・PromptScorer・入出力サービス
├── requirements.txt
└── sample_prompts.csv  # 動作確認用サンプル
```

## 設計意図

- 採点基準は `ScoringCriterion` を基底とした単一責任のクラス群にし、`PromptScorer` はそれらを合成（コンポジション）して利用する。基準の追加・変更はクラスの追加・入れ替えのみで完結する。
- `Prompt` / `CriterionResult` / `EvaluationResult` はすべて `@dataclass(frozen=True)` の値オブジェクトとし、生成時に `__post_init__` でバリデーションを行うことで不正な状態を作らせない。
- ファイルI/O（`PromptRepository` / `ScoreReportWriter`）と採点ロジック（`PromptScorer` / `ScoringCriterion`）を分離し、CSV/Excelどちらの形式にも同じ採点ロジックを適用できるようにしている。
