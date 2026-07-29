from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Prompt:
    """採点対象となる、Excelエージェントモードへの指示プロンプト1件を表す値オブジェクト。"""

    id: str
    text: str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id は空にできません")
        if not self.text or not self.text.strip():
            raise ValueError("text は空にできません")


@dataclass(frozen=True)
class CriterionResult:
    """単一の採点基準（Criterion）による評価結果。"""

    name: str
    weight: float
    score: float
    passed: bool
    message: str

    def __post_init__(self) -> None:
        if self.weight <= 0:
            raise ValueError("weight は正の値でなければなりません")
        if not (0 <= self.score <= self.weight):
            raise ValueError("score は 0 から weight の範囲でなければなりません")


@dataclass(frozen=True)
class EvaluationResult:
    """1件のプロンプトに対する全採点基準の評価結果をまとめた値オブジェクト。"""

    prompt: Prompt
    criterion_results: Tuple[CriterionResult, ...]

    @property
    def total_score(self) -> float:
        return sum(result.score for result in self.criterion_results)

    @property
    def feedback(self) -> str:
        issues = [result.message for result in self.criterion_results if not result.passed]
        if not issues:
            return "特に問題は見つかりませんでした。良いプロンプトです。"
        return " / ".join(issues)
