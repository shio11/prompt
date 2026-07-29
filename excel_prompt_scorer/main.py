import argparse
from pathlib import Path

from services import PromptRepository, PromptScorer, ScoreReportWriter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Excelエージェントモード向けプロンプトを一括採点し、スコアとフィードバックを出力します。"
    )
    parser.add_argument("--input", required=True, help="採点対象プロンプトが入ったCSV/Excelファイルのパス")
    parser.add_argument("--output", required=True, help="採点結果を出力するCSV/Excelファイルのパス")
    parser.add_argument("--text-column", default="prompt", help="プロンプト本文が入っている列名（既定値: prompt）")
    parser.add_argument("--id-column", default=None, help="プロンプトのID列名（未指定の場合は行番号を使用）")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    repository = PromptRepository(text_column=args.text_column, id_column=args.id_column)
    scorer = PromptScorer()
    writer = ScoreReportWriter()

    prompts = repository.load(Path(args.input))
    if not prompts:
        print("採点対象のプロンプトが見つかりませんでした。")
        return

    results = [scorer.score(prompt) for prompt in prompts]
    writer.write(results, Path(args.output))
    print(f"{len(results)}件のプロンプトを採点し、{args.output} に出力しました。")


if __name__ == "__main__":
    main()
