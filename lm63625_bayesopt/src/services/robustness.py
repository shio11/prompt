"""温度・入力電圧・出力電圧・部品バラツキに対するモンテカルロ・ロバスト評価。"""
from __future__ import annotations

from typing import List

import numpy as np

from models import (
    ApplicationRequirement,
    BuckDesignParameters,
    DesignAssumptions,
    DeviceSpec,
    EnvironmentalSample,
    RobustEvaluationResult,
)
from services.circuit_model import BuckConverterEvaluator

NOMINAL_AMBIENT_TEMPERATURE_C = 25.0


class EnvironmentalSampler:
    """許容誤差定義（温度・入力電圧・出力電圧・部品バラツキ）からモンテカルロ環境サンプルを生成する。"""

    def __init__(
        self,
        device_spec: DeviceSpec,
        assumptions: DesignAssumptions,
        application: ApplicationRequirement,
        random_seed: int = 0,
    ) -> None:
        self._device_spec = device_spec
        self._assumptions = assumptions
        self._application = application
        self._rng = np.random.default_rng(random_seed)

    def sample(self, n_samples: int) -> List[EnvironmentalSample]:
        spec = self._device_spec
        asm = self._assumptions
        app = self._application
        return [
            EnvironmentalSample(
                input_voltage_v=float(self._rng.uniform(app.input_voltage_min_v, app.input_voltage_max_v)),
                ambient_temperature_c=float(self._rng.uniform(spec.ta_grade1_min_c, spec.ta_grade1_max_c)),
                output_voltage_v=float(self._rng.uniform(spec.vfb_5v_min_v, spec.vfb_5v_max_v)),
                output_capacitance_multiplier=self._derated_multiplier(
                    asm.output_capacitor_tolerance, asm.output_capacitor_bias_derating
                ),
                output_esr_multiplier=self._tolerance_multiplier(asm.output_esr_tolerance),
                input_capacitance_multiplier=self._derated_multiplier(
                    asm.input_capacitor_tolerance, asm.input_capacitor_bias_derating
                ),
                inductance_multiplier=self._tolerance_multiplier(asm.inductor_tolerance),
                switching_frequency_multiplier=self._tolerance_multiplier(asm.rt_resistor_tolerance),
            )
            for _ in range(n_samples)
        ]

    def _tolerance_multiplier(self, tolerance: float) -> float:
        return float(self._rng.uniform(1.0 - tolerance, 1.0 + tolerance))

    def _derated_multiplier(self, tolerance: float, bias_derating: float) -> float:
        # 許容誤差はランダムに変動する一方、DCバイアスディレーティングは常に適用される系統的効果
        return self._tolerance_multiplier(tolerance) * (1.0 - bias_derating)


class PerturbedDesignBuilder:
    """公称設計値に環境サンプルの乗数を適用し、評価用の実効値を構築する。"""

    def build(self, nominal_params: BuckDesignParameters, sample: EnvironmentalSample) -> BuckDesignParameters:
        return BuckDesignParameters(
            switching_frequency_khz=nominal_params.switching_frequency_khz
            * sample.switching_frequency_multiplier,
            inductance_uh=nominal_params.inductance_uh * sample.inductance_multiplier,
            output_capacitance_uf=nominal_params.output_capacitance_uf * sample.output_capacitance_multiplier,
            output_esr_ohm=nominal_params.output_esr_ohm * sample.output_esr_multiplier,
            input_capacitance_uf=nominal_params.input_capacitance_uf * sample.input_capacitance_multiplier,
        )


class RobustBuckEvaluator:
    """固定されたモンテカルロ環境サンプル集合に対する評価を集約し、ワーストケース結果を返す。

    全ての候補設計に同一の環境サンプル集合（common random numbers）を用いることで、
    ベイズ最適化の目的関数評価に余計なノイズが乗るのを防ぐ。
    """

    def __init__(
        self,
        evaluator: BuckConverterEvaluator,
        perturbed_design_builder: PerturbedDesignBuilder,
        device_spec: DeviceSpec,
        assumptions: DesignAssumptions,
        application: ApplicationRequirement,
        environmental_samples: List[EnvironmentalSample],
    ) -> None:
        self._evaluator = evaluator
        self._perturbed_design_builder = perturbed_design_builder
        self._device_spec = device_spec
        self._assumptions = assumptions
        self._application = application
        self._environmental_samples = environmental_samples

    def evaluate(self, nominal_params: BuckDesignParameters) -> RobustEvaluationResult:
        ripples: List[float] = []
        power_losses: List[float] = []
        cout_margins: List[float] = []
        esr_margins: List[float] = []
        inductance_margins: List[float] = []
        cin_margins: List[float] = []
        peak_current_margins: List[float] = []
        tj_margins: List[float] = []

        for sample in self._environmental_samples:
            perturbed_params = self._perturbed_design_builder.build(nominal_params, sample)
            result = self._evaluator.evaluate(
                perturbed_params, sample.input_voltage_v, sample.output_voltage_v, sample.ambient_temperature_c
            )
            ripples.append(result.output_ripple_mv)
            power_losses.append(result.power_loss_mw)
            cout_margins.append(perturbed_params.output_capacitance_uf - result.required_min_output_capacitance_uf)
            esr_margins.append(result.required_max_esr_ohm - perturbed_params.output_esr_ohm)
            inductance_margins.append(perturbed_params.inductance_uh - result.required_min_inductance_uh)
            cin_margins.append(perturbed_params.input_capacitance_uf - self._device_spec.cin_min_uf)
            peak_current_margins.append(
                self._assumptions.current_limit_design_margin * self._device_spec.isc_hs_min_a
                - result.peak_inductor_current_a
            )
            tj_margins.append(
                self._device_spec.tj_max_c
                - self._assumptions.junction_temperature_margin_c
                - result.junction_temperature_c
            )

        nominal_result = self._evaluator.evaluate(
            nominal_params,
            self._application.input_voltage_nominal_v,
            self._device_spec.vfb_5v_typ_v,
            NOMINAL_AMBIENT_TEMPERATURE_C,
        )

        return RobustEvaluationResult(
            worst_output_ripple_mv=max(ripples),
            worst_power_loss_mw=max(power_losses),
            output_capacitance_margin_uf=min(cout_margins),
            esr_margin_ohm=min(esr_margins),
            inductance_margin_uh=min(inductance_margins),
            input_capacitance_margin_uf=min(cin_margins),
            nominal_ripple_ratio_lower_margin=(
                nominal_result.ripple_current_ratio - self._device_spec.ripple_current_ratio_min
            ),
            nominal_ripple_ratio_upper_margin=(
                self._device_spec.ripple_current_ratio_max - nominal_result.ripple_current_ratio
            ),
            peak_current_margin_a=min(peak_current_margins),
            junction_temperature_margin_c=min(tj_margins),
            n_samples=len(self._environmental_samples),
        )
