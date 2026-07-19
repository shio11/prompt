"""Optuna(TPE)によるLM63625-Q1周辺部品定数のロバスト多目的ベイズ最適化。"""
from __future__ import annotations

from typing import List, Tuple

import optuna

from models import BuckDesignParameters, BuckSearchSpace, ParameterRange, RobustEvaluationResult
from services.robustness import RobustBuckEvaluator


class BayesianOptimizer:
    """4目的（リプル・電力損失・Cout・L）× 7制約（データシート要求充足）のロバストBO。"""

    def __init__(
        self,
        robust_evaluator: RobustBuckEvaluator,
        search_space: BuckSearchSpace,
        random_seed: int = 0,
    ) -> None:
        self._robust_evaluator = robust_evaluator
        self._search_space = search_space
        self._random_seed = random_seed

    def _suggest_parameters(self, trial: optuna.Trial) -> BuckDesignParameters:
        def suggest(name: str, param_range: ParameterRange) -> float:
            return trial.suggest_float(name, param_range.low, param_range.high, log=param_range.log_scale)

        return BuckDesignParameters(
            switching_frequency_khz=suggest(
                "switching_frequency_khz", self._search_space.switching_frequency_khz
            ),
            inductance_uh=suggest("inductance_uh", self._search_space.inductance_uh),
            output_capacitance_uf=suggest("output_capacitance_uf", self._search_space.output_capacitance_uf),
            output_esr_ohm=suggest("output_esr_ohm", self._search_space.output_esr_ohm),
            input_capacitance_uf=suggest("input_capacitance_uf", self._search_space.input_capacitance_uf),
        )

    @staticmethod
    def _constraints(trial: optuna.trial.FrozenTrial) -> Tuple[float, ...]:
        return trial.user_attrs["constraint"]

    def _objective(self, trial: optuna.Trial) -> Tuple[float, float, float, float]:
        params = self._suggest_parameters(trial)
        result = self._robust_evaluator.evaluate(params)
        trial.set_user_attr(
            "constraint",
            (
                -result.output_capacitance_margin_uf,
                -result.esr_margin_ohm,
                -result.inductance_margin_uh,
                -result.input_capacitance_margin_uf,
                -result.nominal_ripple_ratio_lower_margin,
                -result.nominal_ripple_ratio_upper_margin,
                -result.peak_current_margin_a,
                -result.junction_temperature_margin_c,
            ),
        )
        return (
            result.worst_output_ripple_mv,
            result.worst_power_loss_mw,
            params.output_capacitance_uf,
            params.inductance_uh,
        )

    def run(self, n_trials: int) -> optuna.Study:
        sampler = optuna.samplers.TPESampler(
            seed=self._random_seed, constraints_func=self._constraints, multivariate=True
        )
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        study = optuna.create_study(directions=["minimize"] * 4, sampler=sampler)
        study.optimize(self._objective, n_trials=n_trials)
        return study

    def get_pareto_front(
        self, study: optuna.Study
    ) -> List[Tuple[BuckDesignParameters, RobustEvaluationResult]]:
        results: List[Tuple[BuckDesignParameters, RobustEvaluationResult]] = []
        for trial in study.best_trials:
            if not all(c <= 0.0 for c in trial.user_attrs["constraint"]):
                continue
            params = BuckDesignParameters(
                switching_frequency_khz=trial.params["switching_frequency_khz"],
                inductance_uh=trial.params["inductance_uh"],
                output_capacitance_uf=trial.params["output_capacitance_uf"],
                output_esr_ohm=trial.params["output_esr_ohm"],
                input_capacitance_uf=trial.params["input_capacitance_uf"],
            )
            results.append((params, self._robust_evaluator.evaluate(params)))
        return results
