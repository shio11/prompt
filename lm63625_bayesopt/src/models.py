"""LM63625-Q1 (DQPWPRQ1, HTSSOP16, 2.5Aデバイス) 周辺回路のベイズ最適化で扱うデータ構造。

DeviceSpec の各値は TI データシート (LM63615-Q1, LM63625-Q1, JAJSI34J) の
電気的特性表・設計手順（セクション6, 7.3, 8.2.2）から転記した実測仕様値。
DesignAssumptions はデータシートに明記がなく、本ツールが設計マージンとして
仮定した値（要検証）であることを区別して保持する。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceSpec:
    """LM63625-Q1 (2.5Aデバイス, PWP/HTSSOP16パッケージ) のデータシート記載仕様値。"""

    vin_min_v: float = 3.5
    vin_max_v: float = 36.0
    vout_min_v: float = 1.0
    vout_max_v: float = 20.0
    iout_max_device_a: float = 2.5
    vfb_5v_min_v: float = 4.925
    vfb_5v_typ_v: float = 5.0
    vfb_5v_max_v: float = 5.075
    iq_typ_a: float = 23.0e-6
    iq_max_a: float = 40.0e-6
    isc_hs_min_a: float = 3.18
    isc_hs_typ_a: float = 3.75
    rds_on_hs_typ_ohm: float = 0.093
    rds_on_ls_typ_ohm: float = 0.061
    r_theta_ja_pwp_c_per_w: float = 43.1
    tj_max_c: float = 150.0
    ta_grade1_min_c: float = -40.0
    ta_grade1_max_c: float = 125.0
    fsw_min_khz: float = 250.0
    fsw_max_khz: float = 2200.0
    rt_formula_constant_kohm_khz: float = 15770.0
    ripple_current_ratio_min: float = 0.20
    ripple_current_ratio_max: float = 0.40
    lmin_coefficient_m: float = 0.42
    cin_min_uf: float = 4.7

    def __post_init__(self) -> None:
        if not (0 < self.vin_min_v < self.vin_max_v):
            raise ValueError("vin_min_v must be positive and less than vin_max_v")
        if not (0 < self.vout_min_v < self.vout_max_v):
            raise ValueError("vout_min_v must be positive and less than vout_max_v")
        if self.iout_max_device_a <= 0:
            raise ValueError("iout_max_device_a must be positive")
        if not (0 < self.vfb_5v_min_v < self.vfb_5v_typ_v < self.vfb_5v_max_v):
            raise ValueError("vfb_5v_min_v < vfb_5v_typ_v < vfb_5v_max_v must hold")
        if not (0 < self.fsw_min_khz < self.fsw_max_khz):
            raise ValueError("fsw_min_khz must be positive and less than fsw_max_khz")
        if not (0 < self.ripple_current_ratio_min < self.ripple_current_ratio_max):
            raise ValueError("ripple_current_ratio_min must be positive and less than ripple_current_ratio_max")
        if self.ta_grade1_min_c >= self.ta_grade1_max_c:
            raise ValueError("ta_grade1_min_c must be less than ta_grade1_max_c")


@dataclass(frozen=True)
class DesignAssumptions:
    """データシートに明記されていない、本ツール側の設計マージン仮定値（要検証）。

    output_capacitor_tolerance / output_capacitor_bias_derating のみ、データシート
    セクション8.2.2.4の設計例（許容誤差20%、バイアスディレーティング10%）に基づく実測値。
    それ以外は一般的なセラミックコンデンサ・パワーインダクタ・精密抵抗の典型値を仮定している。
    """

    output_capacitor_tolerance: float = 0.20
    output_capacitor_bias_derating: float = 0.10
    input_capacitor_tolerance: float = 0.20
    input_capacitor_bias_derating: float = 0.10
    output_esr_tolerance: float = 0.30
    inductor_tolerance: float = 0.20
    rt_resistor_tolerance: float = 0.01
    current_limit_design_margin: float = 0.90
    junction_temperature_margin_c: float = 10.0

    def __post_init__(self) -> None:
        for name in (
            "output_capacitor_tolerance",
            "output_capacitor_bias_derating",
            "input_capacitor_tolerance",
            "input_capacitor_bias_derating",
            "output_esr_tolerance",
            "inductor_tolerance",
            "rt_resistor_tolerance",
        ):
            value = getattr(self, name)
            if not (0.0 <= value < 1.0):
                raise ValueError(f"{name} must be within [0, 1)")
        if not (0.0 < self.current_limit_design_margin <= 1.0):
            raise ValueError("current_limit_design_margin must be within (0, 1]")
        if self.junction_temperature_margin_c < 0:
            raise ValueError("junction_temperature_margin_c must not be negative")


@dataclass(frozen=True)
class ApplicationRequirement:
    """アプリケーション側の設計目標（データシートではなくユーザー要求）。"""

    input_voltage_nominal_v: float
    input_voltage_min_v: float
    input_voltage_max_v: float
    output_voltage_v: float
    max_load_current_a: float
    load_step_current_a: float
    target_voltage_deviation_v: float

    def __post_init__(self) -> None:
        if not (0 < self.input_voltage_min_v < self.input_voltage_max_v):
            raise ValueError("input_voltage_min_v must be positive and less than input_voltage_max_v")
        if not (self.input_voltage_min_v <= self.input_voltage_nominal_v <= self.input_voltage_max_v):
            raise ValueError("input_voltage_nominal_v must be within [input_voltage_min_v, input_voltage_max_v]")
        if self.output_voltage_v <= 0:
            raise ValueError("output_voltage_v must be positive")
        if self.max_load_current_a <= 0:
            raise ValueError("max_load_current_a must be positive")
        if not (0 < self.load_step_current_a <= self.max_load_current_a):
            raise ValueError("load_step_current_a must be within (0, max_load_current_a]")
        if self.target_voltage_deviation_v <= 0:
            raise ValueError("target_voltage_deviation_v must be positive")


@dataclass(frozen=True)
class BuckDesignParameters:
    """最適化対象となる外付け部品定数（L, Cout, ESR, Cin, RT⇔スイッチング周波数）。"""

    switching_frequency_khz: float
    inductance_uh: float
    output_capacitance_uf: float
    output_esr_ohm: float
    input_capacitance_uf: float

    def __post_init__(self) -> None:
        for name in (
            "switching_frequency_khz",
            "inductance_uh",
            "output_capacitance_uf",
            "output_esr_ohm",
            "input_capacitance_uf",
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
class BuckSearchSpace:
    """外付け部品の探索空間。"""

    switching_frequency_khz: ParameterRange
    inductance_uh: ParameterRange
    output_capacitance_uf: ParameterRange
    output_esr_ohm: ParameterRange
    input_capacitance_uf: ParameterRange


@dataclass(frozen=True)
class EnvironmentalSample:
    """モンテカルロサンプリングされた1つの動作条件・部品バラツキの組み合わせ。"""

    input_voltage_v: float
    ambient_temperature_c: float
    output_voltage_v: float
    output_capacitance_multiplier: float
    output_esr_multiplier: float
    input_capacitance_multiplier: float
    inductance_multiplier: float
    switching_frequency_multiplier: float


@dataclass(frozen=True)
class EvaluationResult:
    """1設計点・1動作条件での評価結果。"""

    output_ripple_mv: float
    power_loss_mw: float
    junction_temperature_c: float
    ripple_current_ratio: float
    peak_inductor_current_a: float
    required_min_output_capacitance_uf: float
    required_max_esr_ohm: float
    required_min_inductance_uh: float


@dataclass(frozen=True)
class RobustEvaluationResult:
    """温度・入力電圧・出力電圧・部品バラツキのモンテカルロ集合に対する評価結果。

    margin系フィールドは「(実力値) - (要求値)」であり、正の値であれば全サンプルで
    要求を満たすことを意味する（worst caseとして全サンプル中の最小値を保持）。

    ripple_ratio_*_margin のみ例外で、モンテカルロのworst caseではなく公称動作点
    （Vin=公称値、Vout=typ、TA=25℃、部品バラツキなし）で評価する。リップル電流比
    20〜40%はデータシートの「インダクタ選定時の目安」であり、バッテリー電圧全域や
    部品バラツキを含めた worst case で強制すると、VinがVoutに近づく低電圧側で
    物理的に達成不可能な制約になってしまうため。
    """

    worst_output_ripple_mv: float
    worst_power_loss_mw: float
    output_capacitance_margin_uf: float
    esr_margin_ohm: float
    inductance_margin_uh: float
    input_capacitance_margin_uf: float
    nominal_ripple_ratio_lower_margin: float
    nominal_ripple_ratio_upper_margin: float
    peak_current_margin_a: float
    junction_temperature_margin_c: float
    n_samples: int

    def is_feasible(self) -> bool:
        return min(
            self.output_capacitance_margin_uf,
            self.esr_margin_ohm,
            self.inductance_margin_uh,
            self.input_capacitance_margin_uf,
            self.nominal_ripple_ratio_lower_margin,
            self.nominal_ripple_ratio_upper_margin,
            self.peak_current_margin_a,
            self.junction_temperature_margin_c,
        ) >= 0.0

    def __repr__(self) -> str:
        return (
            f"RobustEvaluationResult(worst_Vr={self.worst_output_ripple_mv:.1f}mV, "
            f"worst_Ploss={self.worst_power_loss_mw:.1f}mW, "
            f"feasible={self.is_feasible()}, N={self.n_samples})"
        )
