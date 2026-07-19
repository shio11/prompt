"""LDO電源回路の外付け部品定数を多目的ベイズ最適化するエントリーポイント。"""
from __future__ import annotations

from typing import List, Tuple

from models import AmplifierSpec, EvaluationResult, LdoDesignParameters, LdoSearchSpace, OperatingPoint, ParameterRange
from services import BayesianOptimizer, LdoEvaluator, LdoSmallSignalModel, LdoTransientEstimator, PowerLossCalculator


def build_operating_point() -> OperatingPoint:
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


def print_pareto_front(results: List[Tuple[LdoDesignParameters, EvaluationResult]]) -> None:
    print(f"\n実行可能なパレート最適解: {len(results)} 件\n")
    print(
        f"{'PM[deg]':>8} {'Ts[us]':>10} {'Vos[mV]':>10} {'Ploss[mW]':>10}  "
        f"{'Cout[uF]':>9} {'ESR[mOhm]':>10} {'Ro[Ohm]':>8} {'Cc[pF]':>7} "
        f"{'Rz[kOhm]':>9} {'Rfb[kOhm]':>10}"
    )
    for params, result in sorted(results, key=lambda item: item[1].settling_time_us):
        print(
            f"{result.phase_margin_deg:8.1f} {result.settling_time_us:10.1f} "
            f"{result.overshoot_mv:10.1f} {result.power_loss_mw:10.2f}  "
            f"{params.output_capacitance_f * 1e6:9.2f} {params.esr_ohm * 1e3:10.1f} "
            f"{params.pass_device_output_resistance_ohm:8.1f} "
            f"{params.compensation_capacitance_f * 1e12:7.1f} "
            f"{params.zero_resistance_ohm / 1e3:9.2f} "
            f"{params.feedback_total_resistance_ohm / 1e3:10.1f}"
        )


def main() -> None:
    operating_point = build_operating_point()
    amplifier_spec = build_amplifier_spec()
    search_space = build_search_space()

    small_signal_model = LdoSmallSignalModel(amplifier_spec, operating_point)
    transient_estimator = LdoTransientEstimator()
    power_loss_calculator = PowerLossCalculator()
    evaluator = LdoEvaluator(small_signal_model, transient_estimator, power_loss_calculator, operating_point)
    optimizer = BayesianOptimizer(evaluator, search_space, min_phase_margin_deg=45.0)

    study = optimizer.run(n_trials=150)
    pareto_front = optimizer.get_pareto_front(study)
    print_pareto_front(pareto_front)


if __name__ == "__main__":
    main()
