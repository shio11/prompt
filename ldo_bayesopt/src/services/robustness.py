"""温度・入力電圧・部品バラツキに対するモンテカルロ・ロバスト評価。"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np

from models import (
    EnvironmentalSample,
    LdoDesignParameters,
    OperatingPoint,
    RobustEvaluationResult,
    ToleranceSpec,
)
from services.circuit_model import EvaluationResult, LdoEvaluator


class EnvironmentalSampler:
    """許容誤差定義（温度・入力電圧・部品バラツキ）からモンテカルロ環境サンプルを生成する。"""

    def __init__(self, tolerance_spec: ToleranceSpec, random_seed: int = 0) -> None:
        self._tolerance_spec = tolerance_spec
        self._rng = np.random.default_rng(random_seed)

    def sample(self, n_samples: int) -> List[EnvironmentalSample]:
        spec = self._tolerance_spec
        return [
            EnvironmentalSample(
                input_voltage_v=float(self._rng.uniform(spec.input_voltage_min_v, spec.input_voltage_max_v)),
                temperature_c=float(self._rng.uniform(spec.temperature_min_c, spec.temperature_max_c)),
                output_capacitance_multiplier=self._sample_tolerance(spec.output_capacitance_tolerance),
                esr_multiplier=self._sample_tolerance(spec.esr_tolerance),
                pass_device_resistance_multiplier=self._sample_tolerance(spec.pass_device_resistance_tolerance),
                compensation_capacitance_multiplier=self._sample_tolerance(
                    spec.compensation_capacitance_tolerance
                ),
                zero_resistance_multiplier=self._sample_tolerance(spec.zero_resistance_tolerance),
                feedback_resistance_multiplier=self._sample_tolerance(spec.feedback_resistance_tolerance),
            )
            for _ in range(n_samples)
        ]

    def _sample_tolerance(self, tolerance: float) -> float:
        return float(self._rng.uniform(1.0 - tolerance, 1.0 + tolerance))


class PerturbedDesignBuilder:
    """公称設計値・公称動作条件に環境サンプルを適用し、評価用の実効値を構築する。"""

    def __init__(self, tolerance_spec: ToleranceSpec) -> None:
        self._tolerance_spec = tolerance_spec

    def build(
        self,
        nominal_params: LdoDesignParameters,
        nominal_operating_point: OperatingPoint,
        sample: EnvironmentalSample,
    ) -> Tuple[LdoDesignParameters, OperatingPoint]:
        temp_delta_c = sample.temperature_c - 25.0
        resistance_temp_factor = 1.0 + self._tolerance_spec.pass_device_resistance_temp_coeff_per_c * temp_delta_c
        quiescent_temp_factor = 1.0 + self._tolerance_spec.quiescent_current_temp_coeff_per_c * temp_delta_c

        perturbed_params = LdoDesignParameters(
            output_capacitance_f=nominal_params.output_capacitance_f * sample.output_capacitance_multiplier,
            esr_ohm=nominal_params.esr_ohm * sample.esr_multiplier,
            pass_device_output_resistance_ohm=(
                nominal_params.pass_device_output_resistance_ohm
                * sample.pass_device_resistance_multiplier
                * resistance_temp_factor
            ),
            compensation_capacitance_f=nominal_params.compensation_capacitance_f
            * sample.compensation_capacitance_multiplier,
            zero_resistance_ohm=nominal_params.zero_resistance_ohm * sample.zero_resistance_multiplier,
            feedback_total_resistance_ohm=nominal_params.feedback_total_resistance_ohm
            * sample.feedback_resistance_multiplier,
        )
        perturbed_operating_point = OperatingPoint(
            input_voltage_v=sample.input_voltage_v,
            output_voltage_v=nominal_operating_point.output_voltage_v,
            reference_voltage_v=nominal_operating_point.reference_voltage_v,
            max_load_current_a=nominal_operating_point.max_load_current_a,
            quiescent_current_a=nominal_operating_point.quiescent_current_a * quiescent_temp_factor,
            load_step_current_a=nominal_operating_point.load_step_current_a,
        )
        return perturbed_params, perturbed_operating_point


class RobustLdoEvaluator:
    """固定されたモンテカルロ環境サンプル集合に対する評価を集約し、ワーストケース結果を返す。

    全ての候補設計に同一の環境サンプル集合（common random numbers）を用いることで、
    ベイズ最適化の目的関数評価に余計なノイズが乗るのを防ぐ。
    """

    def __init__(
        self,
        evaluator: LdoEvaluator,
        perturbed_design_builder: PerturbedDesignBuilder,
        nominal_operating_point: OperatingPoint,
        environmental_samples: List[EnvironmentalSample],
    ) -> None:
        self._evaluator = evaluator
        self._perturbed_design_builder = perturbed_design_builder
        self._nominal_operating_point = nominal_operating_point
        self._environmental_samples = environmental_samples

    def evaluate(self, nominal_params: LdoDesignParameters) -> RobustEvaluationResult:
        results: List[EvaluationResult] = []
        for sample in self._environmental_samples:
            perturbed_params, perturbed_operating_point = self._perturbed_design_builder.build(
                nominal_params, self._nominal_operating_point, sample
            )
            results.append(self._evaluator.evaluate(perturbed_params, perturbed_operating_point))

        return RobustEvaluationResult(
            worst_phase_margin_deg=min(result.phase_margin_deg for result in results),
            worst_settling_time_us=max(result.settling_time_us for result in results),
            worst_overshoot_mv=max(result.overshoot_mv for result in results),
            worst_power_loss_mw=max(result.power_loss_mw for result in results),
            n_samples=len(results),
        )
