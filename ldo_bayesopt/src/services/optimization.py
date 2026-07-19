"""Optuna(TPE)によるロバスト多目的ベイズ最適化。"""
from __future__ import annotations

from typing import List, Tuple

import optuna

from models import LdoDesignParameters, LdoSearchSpace, ParameterRange, RobustEvaluationResult
from services.robustness import RobustLdoEvaluator


class BayesianOptimizer:
    """Optuna(TPE)によるLDO外付け部品定数のロバスト多目的ベイズ最適化を実行する。

    各試行の目的関数値・安定性制約は RobustLdoEvaluator が返すワーストケース値
    （温度・入力電圧・部品バラツキのモンテカルロ集合上の最悪値）を用いる。
    """

    def __init__(
        self,
        robust_evaluator: RobustLdoEvaluator,
        search_space: LdoSearchSpace,
        min_phase_margin_deg: float = 45.0,
        random_seed: int = 0,
    ) -> None:
        self._robust_evaluator = robust_evaluator
        self._search_space = search_space
        self._min_phase_margin_deg = min_phase_margin_deg
        self._random_seed = random_seed

    def _suggest_parameters(self, trial: optuna.Trial) -> LdoDesignParameters:
        def suggest(name: str, param_range: ParameterRange) -> float:
            return trial.suggest_float(
                name, param_range.low, param_range.high, log=param_range.log_scale
            )

        return LdoDesignParameters(
            output_capacitance_f=suggest("output_capacitance_f", self._search_space.output_capacitance),
            esr_ohm=suggest("esr_ohm", self._search_space.esr),
            pass_device_output_resistance_ohm=suggest(
                "pass_device_output_resistance_ohm",
                self._search_space.pass_device_output_resistance,
            ),
            compensation_capacitance_f=suggest(
                "compensation_capacitance_f", self._search_space.compensation_capacitance
            ),
            zero_resistance_ohm=suggest("zero_resistance_ohm", self._search_space.zero_resistance),
            feedback_total_resistance_ohm=suggest(
                "feedback_total_resistance_ohm", self._search_space.feedback_total_resistance
            ),
        )

    @staticmethod
    def _constraints(trial: optuna.trial.FrozenTrial) -> Tuple[float, ...]:
        return trial.user_attrs["constraint"]

    def _objective(self, trial: optuna.Trial) -> Tuple[float, float, float]:
        params = self._suggest_parameters(trial)
        result = self._robust_evaluator.evaluate(params)
        trial.set_user_attr("constraint", (self._min_phase_margin_deg - result.worst_phase_margin_deg,))
        return result.worst_settling_time_us, result.worst_overshoot_mv, result.worst_power_loss_mw

    def run(self, n_trials: int) -> optuna.Study:
        sampler = optuna.samplers.TPESampler(
            seed=self._random_seed, constraints_func=self._constraints, multivariate=True
        )
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        study = optuna.create_study(directions=["minimize", "minimize", "minimize"], sampler=sampler)
        study.optimize(self._objective, n_trials=n_trials)
        return study

    def get_pareto_front(
        self, study: optuna.Study
    ) -> List[Tuple[LdoDesignParameters, RobustEvaluationResult]]:
        results: List[Tuple[LdoDesignParameters, RobustEvaluationResult]] = []
        for trial in study.best_trials:
            if not all(c <= 0.0 for c in trial.user_attrs["constraint"]):
                continue
            params = LdoDesignParameters(
                output_capacitance_f=trial.params["output_capacitance_f"],
                esr_ohm=trial.params["esr_ohm"],
                pass_device_output_resistance_ohm=trial.params["pass_device_output_resistance_ohm"],
                compensation_capacitance_f=trial.params["compensation_capacitance_f"],
                zero_resistance_ohm=trial.params["zero_resistance_ohm"],
                feedback_total_resistance_ohm=trial.params["feedback_total_resistance_ohm"],
            )
            results.append((params, self._robust_evaluator.evaluate(params)))
        return results
