"""LDO電源回路の評価ロジックと多目的ベイズ最適化を担うモジュール。"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np
import optuna

from models import (
    AmplifierSpec,
    EvaluationResult,
    LdoDesignParameters,
    LdoSearchSpace,
    OperatingPoint,
    ParameterRange,
)


class LdoSmallSignalModel:
    """誤差増幅器・パス素子・出力容量からなる2極2零点の小信号ループモデル。"""

    def __init__(self, amplifier_spec: AmplifierSpec, operating_point: OperatingPoint) -> None:
        self._amplifier_spec = amplifier_spec
        self._operating_point = operating_point

    def _dominant_pole_hz(self, params: LdoDesignParameters) -> float:
        r_ea = self._amplifier_spec.output_resistance_ohm
        return 1.0 / (2.0 * np.pi * r_ea * params.compensation_capacitance_f)

    def _output_pole_hz(self, params: LdoDesignParameters) -> float:
        r_load = self._operating_point.load_resistance_ohm
        r_out = (params.pass_device_output_resistance_ohm * r_load) / (
            params.pass_device_output_resistance_ohm + r_load
        )
        return 1.0 / (2.0 * np.pi * r_out * params.output_capacitance_f)

    def _esr_zero_hz(self, params: LdoDesignParameters) -> float:
        return 1.0 / (2.0 * np.pi * params.esr_ohm * params.output_capacitance_f)

    def _compensation_zero_hz(self, params: LdoDesignParameters) -> float:
        return 1.0 / (2.0 * np.pi * params.zero_resistance_ohm * params.compensation_capacitance_f)

    def loop_gain(self, params: LdoDesignParameters, freq_hz: np.ndarray) -> np.ndarray:
        """周波数配列に対するループ利得 L(jf) を返す。"""
        f_p1 = self._dominant_pole_hz(params)
        f_p2 = self._output_pole_hz(params)
        f_z1 = self._esr_zero_hz(params)
        f_z2 = self._compensation_zero_hz(params)

        s = 1j * freq_hz
        dc_gain = self._amplifier_spec.dc_gain_linear * self._operating_point.feedback_ratio
        pole1 = 1.0 / (1.0 + s / f_p1)
        pole2 = 1.0 / (1.0 + s / f_p2)
        zero1 = 1.0 + s / f_z1
        zero2 = 1.0 + s / f_z2
        return dc_gain * pole1 * pole2 * zero1 * zero2

    def find_crossover_frequency_hz(
        self,
        params: LdoDesignParameters,
        f_min_hz: float = 1.0,
        f_max_hz: float = 1.0e8,
        n_points: int = 4000,
    ) -> float:
        """|L(jf)| = 1 となる周波数（ユニティゲイン周波数）を対数グリッド探索で求める。"""
        freq_hz = np.logspace(np.log10(f_min_hz), np.log10(f_max_hz), n_points)
        magnitude_db = 20.0 * np.log10(np.abs(self.loop_gain(params, freq_hz)))
        sign_changes = np.where(np.diff(np.sign(magnitude_db)) < 0)[0]
        if len(sign_changes) == 0:
            return float(freq_hz[-1]) if magnitude_db[-1] > 0 else float(freq_hz[0])
        index = sign_changes[0]
        return float(freq_hz[index])

    def compute_phase_margin_deg(self, params: LdoDesignParameters) -> float:
        crossover_hz = self.find_crossover_frequency_hz(params)
        loop_value = self.loop_gain(params, np.array([crossover_hz]))[0]
        phase_deg = float(np.degrees(np.angle(loop_value)))
        return 180.0 + phase_deg


class LdoTransientEstimator:
    """位相余裕とクロスオーバー周波数から2次系近似で負荷過渡応答を推定する。"""

    _MIN_DAMPING_RATIO = 0.05
    _MAX_DAMPING_RATIO = 1.0

    def estimate(
        self,
        phase_margin_deg: float,
        crossover_freq_hz: float,
        load_step_current_a: float,
        esr_ohm: float,
    ) -> Tuple[float, float]:
        """(settling_time_us, overshoot_mv) を返す。"""
        damping_ratio = float(
            np.clip(phase_margin_deg / 100.0, self._MIN_DAMPING_RATIO, self._MAX_DAMPING_RATIO)
        )
        natural_freq_rad_s = 2.0 * np.pi * crossover_freq_hz

        if damping_ratio >= 1.0:
            overshoot_ratio = 0.0
        else:
            overshoot_ratio = float(
                np.exp(-np.pi * damping_ratio / np.sqrt(1.0 - damping_ratio**2))
            )

        settling_time_s = 4.0 / (damping_ratio * natural_freq_rad_s)
        instantaneous_step_v = load_step_current_a * esr_ohm
        overshoot_v = instantaneous_step_v * (1.0 + overshoot_ratio)

        return settling_time_s * 1.0e6, overshoot_v * 1.0e3


class PowerLossCalculator:
    """ドロップアウト損失・帰還分圧損失・消費電流損失を合算する。"""

    def calculate(self, params: LdoDesignParameters, operating_point: OperatingPoint) -> float:
        dropout_loss_w = (
            operating_point.input_voltage_v - operating_point.output_voltage_v
        ) * operating_point.max_load_current_a
        quiescent_loss_w = operating_point.input_voltage_v * operating_point.quiescent_current_a
        divider_loss_w = (
            operating_point.output_voltage_v**2 / params.feedback_total_resistance_ohm
        )
        return (dropout_loss_w + quiescent_loss_w + divider_loss_w) * 1.0e3


class LdoEvaluator:
    """設計パラメータ1点を評価し EvaluationResult を返す。"""

    def __init__(
        self,
        small_signal_model: LdoSmallSignalModel,
        transient_estimator: LdoTransientEstimator,
        power_loss_calculator: PowerLossCalculator,
        operating_point: OperatingPoint,
    ) -> None:
        self._small_signal_model = small_signal_model
        self._transient_estimator = transient_estimator
        self._power_loss_calculator = power_loss_calculator
        self._operating_point = operating_point

    def evaluate(self, params: LdoDesignParameters) -> EvaluationResult:
        phase_margin_deg = self._small_signal_model.compute_phase_margin_deg(params)
        crossover_hz = self._small_signal_model.find_crossover_frequency_hz(params)
        settling_time_us, overshoot_mv = self._transient_estimator.estimate(
            phase_margin_deg,
            crossover_hz,
            self._operating_point.load_step_current_a,
            params.esr_ohm,
        )
        power_loss_mw = self._power_loss_calculator.calculate(params, self._operating_point)
        return EvaluationResult(
            phase_margin_deg=phase_margin_deg,
            settling_time_us=settling_time_us,
            overshoot_mv=overshoot_mv,
            power_loss_mw=power_loss_mw,
        )


class BayesianOptimizer:
    """Optuna(TPE)によるLDO外付け部品定数の多目的ベイズ最適化を実行する。"""

    def __init__(
        self,
        evaluator: LdoEvaluator,
        search_space: LdoSearchSpace,
        min_phase_margin_deg: float = 45.0,
        random_seed: int = 0,
    ) -> None:
        self._evaluator = evaluator
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
        result = self._evaluator.evaluate(params)
        trial.set_user_attr("constraint", (self._min_phase_margin_deg - result.phase_margin_deg,))
        return result.settling_time_us, result.overshoot_mv, result.power_loss_mw

    def run(self, n_trials: int) -> optuna.Study:
        sampler = optuna.samplers.TPESampler(
            seed=self._random_seed, constraints_func=self._constraints, multivariate=True
        )
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        study = optuna.create_study(directions=["minimize", "minimize", "minimize"], sampler=sampler)
        study.optimize(self._objective, n_trials=n_trials)
        return study

    def get_pareto_front(self, study: optuna.Study) -> List[Tuple[LdoDesignParameters, EvaluationResult]]:
        results: List[Tuple[LdoDesignParameters, EvaluationResult]] = []
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
            results.append((params, self._evaluator.evaluate(params)))
        return results
