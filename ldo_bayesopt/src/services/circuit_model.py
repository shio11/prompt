"""LDO電源回路の小信号ループモデル・過渡応答推定・電力損失計算・単点評価。"""
from __future__ import annotations

from typing import Tuple

import numpy as np

from models import AmplifierSpec, EvaluationResult, LdoDesignParameters, OperatingPoint


class LdoSmallSignalModel:
    """誤差増幅器・パス素子・出力容量からなる2極2零点の小信号ループモデル。"""

    def __init__(self, amplifier_spec: AmplifierSpec) -> None:
        self._amplifier_spec = amplifier_spec

    def _dominant_pole_hz(self, params: LdoDesignParameters) -> float:
        r_ea = self._amplifier_spec.output_resistance_ohm
        return 1.0 / (2.0 * np.pi * r_ea * params.compensation_capacitance_f)

    def _output_pole_hz(self, params: LdoDesignParameters, operating_point: OperatingPoint) -> float:
        r_load = operating_point.load_resistance_ohm
        r_out = (params.pass_device_output_resistance_ohm * r_load) / (
            params.pass_device_output_resistance_ohm + r_load
        )
        return 1.0 / (2.0 * np.pi * r_out * params.output_capacitance_f)

    def _esr_zero_hz(self, params: LdoDesignParameters) -> float:
        return 1.0 / (2.0 * np.pi * params.esr_ohm * params.output_capacitance_f)

    def _compensation_zero_hz(self, params: LdoDesignParameters) -> float:
        return 1.0 / (2.0 * np.pi * params.zero_resistance_ohm * params.compensation_capacitance_f)

    def loop_gain(
        self, params: LdoDesignParameters, operating_point: OperatingPoint, freq_hz: np.ndarray
    ) -> np.ndarray:
        """周波数配列に対するループ利得 L(jf) を返す。"""
        f_p1 = self._dominant_pole_hz(params)
        f_p2 = self._output_pole_hz(params, operating_point)
        f_z1 = self._esr_zero_hz(params)
        f_z2 = self._compensation_zero_hz(params)

        s = 1j * freq_hz
        dc_gain = self._amplifier_spec.dc_gain_linear * operating_point.feedback_ratio
        pole1 = 1.0 / (1.0 + s / f_p1)
        pole2 = 1.0 / (1.0 + s / f_p2)
        zero1 = 1.0 + s / f_z1
        zero2 = 1.0 + s / f_z2
        return dc_gain * pole1 * pole2 * zero1 * zero2

    def find_crossover_frequency_hz(
        self,
        params: LdoDesignParameters,
        operating_point: OperatingPoint,
        f_min_hz: float = 1.0,
        f_max_hz: float = 1.0e8,
        n_points: int = 4000,
    ) -> float:
        """|L(jf)| = 1 となる周波数（ユニティゲイン周波数）を対数グリッド探索で求める。"""
        freq_hz = np.logspace(np.log10(f_min_hz), np.log10(f_max_hz), n_points)
        magnitude_db = 20.0 * np.log10(np.abs(self.loop_gain(params, operating_point, freq_hz)))
        sign_changes = np.where(np.diff(np.sign(magnitude_db)) < 0)[0]
        if len(sign_changes) == 0:
            return float(freq_hz[-1]) if magnitude_db[-1] > 0 else float(freq_hz[0])
        index = sign_changes[0]
        return float(freq_hz[index])

    def compute_phase_margin_deg(self, params: LdoDesignParameters, operating_point: OperatingPoint) -> float:
        crossover_hz = self.find_crossover_frequency_hz(params, operating_point)
        loop_value = self.loop_gain(params, operating_point, np.array([crossover_hz]))[0]
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
    """設計パラメータ・動作条件の組を1点評価し EvaluationResult を返す。"""

    def __init__(
        self,
        small_signal_model: LdoSmallSignalModel,
        transient_estimator: LdoTransientEstimator,
        power_loss_calculator: PowerLossCalculator,
    ) -> None:
        self._small_signal_model = small_signal_model
        self._transient_estimator = transient_estimator
        self._power_loss_calculator = power_loss_calculator

    def evaluate(self, params: LdoDesignParameters, operating_point: OperatingPoint) -> EvaluationResult:
        phase_margin_deg = self._small_signal_model.compute_phase_margin_deg(params, operating_point)
        crossover_hz = self._small_signal_model.find_crossover_frequency_hz(params, operating_point)
        settling_time_us, overshoot_mv = self._transient_estimator.estimate(
            phase_margin_deg,
            crossover_hz,
            operating_point.load_step_current_a,
            params.esr_ohm,
        )
        power_loss_mw = self._power_loss_calculator.calculate(params, operating_point)
        return EvaluationResult(
            phase_margin_deg=phase_margin_deg,
            settling_time_us=settling_time_us,
            overshoot_mv=overshoot_mv,
            power_loss_mw=power_loss_mw,
        )
