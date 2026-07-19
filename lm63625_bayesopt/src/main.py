"""LM63625DQPWPRQ1 (2.5Aデバイス, HTSSOP16) 周辺回路をロバスト多目的ベイズ最適化するエントリーポイント。

VOUT=5V はデータシート推奨のVSEL=VCC（内蔵5V分圧器）を用いる前提とし、
外付けフィードバック分圧器は使用しない（帰還抵抗の最適化対象は存在しない）。
"""
from __future__ import annotations

from typing import List, Tuple

from models import (
    ApplicationRequirement,
    BuckDesignParameters,
    BuckSearchSpace,
    DesignAssumptions,
    DeviceSpec,
    ParameterRange,
    RobustEvaluationResult,
)
from services import (
    BayesianOptimizer,
    BuckConverterEvaluator,
    EnvironmentalSampler,
    PerturbedDesignBuilder,
    RobustBuckEvaluator,
    SwitchingFrequencyConverter,
)

N_MONTE_CARLO_SAMPLES = 32
N_TRIALS = 400


def build_application_requirement() -> ApplicationRequirement:
    return ApplicationRequirement(
        input_voltage_nominal_v=13.5,
        input_voltage_min_v=9.0,
        input_voltage_max_v=16.0,
        output_voltage_v=5.0,
        max_load_current_a=1.5,
        load_step_current_a=1.0,
        target_voltage_deviation_v=0.15,
    )


def build_search_space() -> BuckSearchSpace:
    return BuckSearchSpace(
        switching_frequency_khz=ParameterRange(low=250.0, high=2200.0),
        inductance_uh=ParameterRange(low=1.0, high=33.0),
        output_capacitance_uf=ParameterRange(low=10.0, high=300.0),
        output_esr_ohm=ParameterRange(low=1.0e-3, high=5.0e-2),
        input_capacitance_uf=ParameterRange(low=4.7, high=47.0),
    )


def print_pareto_front(
    results: List[Tuple[BuckDesignParameters, RobustEvaluationResult]],
    frequency_converter: SwitchingFrequencyConverter,
    max_rows: int = 15,
) -> None:
    print(f"\n実行可能なロバスト・パレート最適解: {len(results)} 件（Monte Carlo N={N_MONTE_CARLO_SAMPLES}）")
    print(f"上位 {min(max_rows, len(results))} 件をworst_Vrでソートして表示\n")
    print(
        f"{'worstVr':>8} {'worstPloss':>11}  "
        f"{'fSW[kHz]':>9} {'RT[kOhm]':>9} {'L[uH]':>7} {'Cout[uF]':>9} "
        f"{'ESR[mOhm]':>10} {'Cin[uF]':>8}"
    )
    for params, result in sorted(results, key=lambda item: item[1].worst_output_ripple_mv)[:max_rows]:
        rt_kohm = frequency_converter.rt_resistance_kohm(params.switching_frequency_khz)
        print(
            f"{result.worst_output_ripple_mv:8.1f} {result.worst_power_loss_mw:11.2f}  "
            f"{params.switching_frequency_khz:9.1f} {rt_kohm:9.2f} {params.inductance_uh:7.2f} "
            f"{params.output_capacitance_uf:9.1f} {params.output_esr_ohm * 1e3:10.2f} "
            f"{params.input_capacitance_uf:8.2f}"
        )


def main() -> None:
    device_spec = DeviceSpec()
    assumptions = DesignAssumptions()
    application = build_application_requirement()
    search_space = build_search_space()

    evaluator = BuckConverterEvaluator(device_spec, application)
    frequency_converter = SwitchingFrequencyConverter(device_spec)

    environmental_sampler = EnvironmentalSampler(device_spec, assumptions, application, random_seed=0)
    environmental_samples = environmental_sampler.sample(N_MONTE_CARLO_SAMPLES)
    perturbed_design_builder = PerturbedDesignBuilder()
    robust_evaluator = RobustBuckEvaluator(
        evaluator, perturbed_design_builder, device_spec, assumptions, application, environmental_samples
    )

    optimizer = BayesianOptimizer(robust_evaluator, search_space)
    study = optimizer.run(n_trials=N_TRIALS)
    pareto_front = optimizer.get_pareto_front(study)
    print_pareto_front(pareto_front, frequency_converter)

    print(
        "\n固定（データシート推奨・最適化対象外）: VSEL=VCC (VOUT=5V 内蔵分圧器使用), "
        "CBOOT=220nF, CVCC=1uF, 入力HFバイパス=220nF"
    )


if __name__ == "__main__":
    main()
