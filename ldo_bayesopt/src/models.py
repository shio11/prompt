"""LDO電源回路のベイズ最適化で扱うデータ構造を定義するモジュール。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AmplifierSpec:
    """誤差増幅器（エラーアンプ）の固定特性。"""

    dc_gain_db: float
    output_resistance_ohm: float

    def __post_init__(self) -> None:
        if self.dc_gain_db <= 0:
            raise ValueError("dc_gain_db must be positive")
        if self.output_resistance_ohm <= 0:
            raise ValueError("output_resistance_ohm must be positive")

    @property
    def dc_gain_linear(self) -> float:
        return 10 ** (self.dc_gain_db / 20.0)


@dataclass(frozen=True)
class OperatingPoint:
    """LDOの動作条件（バッテリー電圧・負荷条件）。"""

    input_voltage_v: float
    output_voltage_v: float
    reference_voltage_v: float
    max_load_current_a: float
    quiescent_current_a: float
    load_step_current_a: float

    def __post_init__(self) -> None:
        if self.input_voltage_v <= self.output_voltage_v:
            raise ValueError("input_voltage_v must exceed output_voltage_v")
        if self.output_voltage_v <= self.reference_voltage_v:
            raise ValueError("output_voltage_v must exceed reference_voltage_v")
        if self.max_load_current_a <= 0:
            raise ValueError("max_load_current_a must be positive")
        if self.quiescent_current_a < 0:
            raise ValueError("quiescent_current_a must not be negative")
        if not (0 < self.load_step_current_a <= self.max_load_current_a):
            raise ValueError("load_step_current_a must be within (0, max_load_current_a]")

    @property
    def feedback_ratio(self) -> float:
        """帰還分圧比 beta = Vref / Vout。"""
        return self.reference_voltage_v / self.output_voltage_v

    @property
    def load_resistance_ohm(self) -> float:
        return self.output_voltage_v / self.max_load_current_a


@dataclass(frozen=True)
class LdoDesignParameters:
    """最適化対象となる外付け部品定数。"""

    output_capacitance_f: float
    esr_ohm: float
    pass_device_output_resistance_ohm: float
    compensation_capacitance_f: float
    zero_resistance_ohm: float
    feedback_total_resistance_ohm: float

    def __post_init__(self) -> None:
        for name in (
            "output_capacitance_f",
            "esr_ohm",
            "pass_device_output_resistance_ohm",
            "compensation_capacitance_f",
            "zero_resistance_ohm",
            "feedback_total_resistance_ohm",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")


@dataclass(frozen=True)
class ParameterRange:
    """探索パラメータの範囲定義。"""

    low: float
    high: float
    log_scale: bool = True

    def __post_init__(self) -> None:
        if self.log_scale and self.low <= 0:
            raise ValueError("low must be positive when log_scale is True")
        if self.low >= self.high:
            raise ValueError("low must be less than high")


@dataclass(frozen=True)
class LdoSearchSpace:
    """LDO設計パラメータの探索空間。"""

    output_capacitance: ParameterRange
    esr: ParameterRange
    pass_device_output_resistance: ParameterRange
    compensation_capacitance: ParameterRange
    zero_resistance: ParameterRange
    feedback_total_resistance: ParameterRange


@dataclass(frozen=True)
class EvaluationResult:
    """1設計点の評価結果（目的関数・安定性制約）。"""

    phase_margin_deg: float
    settling_time_us: float
    overshoot_mv: float
    power_loss_mw: float

    def is_stable(self, min_phase_margin_deg: float = 45.0) -> bool:
        return self.phase_margin_deg >= min_phase_margin_deg

    def __repr__(self) -> str:
        return (
            f"EvaluationResult(PM={self.phase_margin_deg:.1f}deg, "
            f"Ts={self.settling_time_us:.1f}us, "
            f"Vos={self.overshoot_mv:.1f}mV, "
            f"Ploss={self.power_loss_mw:.1f}mW)"
        )
