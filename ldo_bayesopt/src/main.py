"""LDO電源回路の外付け部品定数をロバスト多目的ベイズ最適化するエントリーポイント。"""
from __future__ import annotations

from typing import List, Tuple

from models import (
    AmplifierSpec,
    LdoDesignParameters,
    LdoSearchSpace,
    OperatingPoint,
    ParameterRange,
    RobustEvaluationResult,
    ToleranceSpec,
)
from services import (
    BayesianOptimizer,
    EnvironmentalSampler,
    LdoEvaluator,
    LdoSmallSignalModel,
    LdoTransientEstimator,
    PerturbedDesignBuilder,
    PowerLossCalculator,
    RobustLdoEvaluator,
)

N_MONTE_CARLO_SAMPLES = 32


def build_nominal_operating_point() -> OperatingPoint:
    return OperatingPoint(
        input_voltage_v=13.5,
        output_voltage_v=5.0,
        reference_voltage_v=1.2,
        max_load_current_a=0.3,
        quiescent_current_a=60.0e-6,
        load_step_current_a=0.15,
    )


def build_amplifier_spec() -> AmplifierSpec:
    return AmplifierSpec(dc_gain_db=80.0, output_resistance_ohm=1.0e6)


def build_search_space() -> LdoSearchSpace:
    return LdoSearchSpace(
        output_capacitance=ParameterRange(low=1.0e-6, high=47.0e-6),
        esr=ParameterRange(low=1.0e-3, high=0.5),
        pass_device_output_resistance=ParameterRange(low=5.0, high=500.0),
        compensation_capacitance=ParameterRange(low=1.0e-12, high=100.0e-12),
        zero_resistance=ParameterRange(low=1.0e2, high=1.0e5),
        feedback_total_resistance=ParameterRange(low=1.0e4, high=1.0e6),
    )


def build_tolerance_spec() -> ToleranceSpec:
    """車載グレード（AEC-Q）を想定した部品バラツキ・温度・入力電圧レンジ。"""
    return ToleranceSpec(
        output_capacitance_tolerance=0.20,
        esr_tolerance=0.50,
        pass_device_resistance_tolerance=0.20,
        compensation_capacitance_tolerance=0.10,
        zero_resistance_tolerance=0.01,
        feedback_resistance_tolerance=0.01,
        pass_device_resistance_temp_coeff_per_c=0.004,
        quiescent_current_temp_coeff_per_c=0.005,
        input_voltage_min_v=9.0,
        input_voltage_max_v=16.0,
        temperature_min_c=-40.0,
        temperature_max_c=125.0,
    )


def print_pareto_front(results: List[Tuple[LdoDesignParameters, RobustEvaluationResult]]) -> None:
    print(f"\n実行可能なロバスト・パレート最適解: {len(results)} 件（Monte Carlo N={N_MONTE_CARLO_SAMPLES}）\n")
    print(
        f"{'worstPM':>8} {'worstTs':>10} {'worstVos':>10} {'worstPloss':>11}  "
        f"{'Cout[uF]':>9} {'ESR[mOhm]':>10} {'Ro[Ohm]':>8} {'Cc[pF]':>7} "
        f"{'Rz[kOhm]':>9} {'Rfb[kOhm]':>10}"
    )
    for params, result in sorted(results, key=lambda item: item[1].worst_settling_time_us):
        print(
            f"{result.worst_phase_margin_deg:8.1f} {result.worst_settling_time_us:10.1f} "
            f"{result.worst_overshoot_mv:10.1f} {result.worst_power_loss_mw:11.2f}  "
            f"{params.output_capacitance_f * 1e6:9.2f} {params.esr_ohm * 1e3:10.1f} "
            f"{params.pass_device_output_resistance_ohm:8.1f} "
            f"{params.compensation_capacitance_f * 1e12:7.1f} "
            f"{params.zero_resistance_ohm / 1e3:9.2f} "
            f"{params.feedback_total_resistance_ohm / 1e3:10.1f}"
        )


def main() -> None:
    nominal_operating_point = build_nominal_operating_point()
    amplifier_spec = build_amplifier_spec()
    search_space = build_search_space()
    tolerance_spec = build_tolerance_spec()

    small_signal_model = LdoSmallSignalModel(amplifier_spec)
    transient_estimator = LdoTransientEstimator()
    power_loss_calculator = PowerLossCalculator()
    evaluator = LdoEvaluator(small_signal_model, transient_estimator, power_loss_calculator)

    environmental_sampler = EnvironmentalSampler(tolerance_spec, random_seed=0)
    environmental_samples = environmental_sampler.sample(N_MONTE_CARLO_SAMPLES)
    perturbed_design_builder = PerturbedDesignBuilder(tolerance_spec)
    robust_evaluator = RobustLdoEvaluator(
        evaluator, perturbed_design_builder, nominal_operating_point, environmental_samples
    )

    optimizer = BayesianOptimizer(robust_evaluator, search_space, min_phase_margin_deg=45.0)

    study = optimizer.run(n_trials=150)
    pareto_front = optimizer.get_pareto_front(study)
    print_pareto_front(pareto_front)


if __name__ == "__main__":
    main()
