"""LM63625-Q1 の設計式（データシート 式1, 式7〜式10）に基づく単点評価ロジック。

DCS-Control方式は外付け補償が不要な内部補償のため、LDOのようなループ利得の
周波数掃引は不要で、すべて閉形式の代数式で評価できる。
"""
from __future__ import annotations

from models import ApplicationRequirement, BuckDesignParameters, DeviceSpec, EvaluationResult


class SwitchingFrequencyConverter:
    """RT抵抗とスイッチング周波数の関係（データシート式1）。"""

    def __init__(self, device_spec: DeviceSpec) -> None:
        self._device_spec = device_spec

    def rt_resistance_kohm(self, switching_frequency_khz: float) -> float:
        return self._device_spec.rt_formula_constant_kohm_khz / switching_frequency_khz


class BuckConverterEvaluator:
    """設計パラメータ・動作条件の組を1点評価し EvaluationResult を返す。"""

    def __init__(self, device_spec: DeviceSpec, application: ApplicationRequirement) -> None:
        self._device_spec = device_spec
        self._application = application

    @staticmethod
    def _duty_cycle(vout_v: float, vin_v: float) -> float:
        return vout_v / vin_v

    @staticmethod
    def _inductor_ripple_current_pp_a(params: BuckDesignParameters, vin_v: float, vout_v: float) -> float:
        fsw_mhz = params.switching_frequency_khz / 1000.0
        return (vin_v - vout_v) / (fsw_mhz * params.inductance_uh) * (vout_v / vin_v)

    def _ripple_current_ratio(self, ripple_current_pp_a: float) -> float:
        # データシート指示: 比率計算には実負荷ではなく常にデバイス定格電流(2.5A)を用いる
        return ripple_current_pp_a / self._device_spec.iout_max_device_a

    def _required_min_inductance_uh(self, vout_v: float, fsw_mhz: float) -> float:
        return self._device_spec.lmin_coefficient_m * vout_v / fsw_mhz

    def _required_min_output_capacitance_uf(
        self, fsw_mhz: float, vin_v: float, vout_v: float, ripple_current_ratio: float
    ) -> float:
        d = self._duty_cycle(vout_v, vin_v)
        k = ripple_current_ratio
        delta_iout = self._application.load_step_current_a
        delta_vout = self._application.target_voltage_deviation_v
        bracket = (1.0 - d) * (1.0 + k + (k**2) / 12.0) + (k**2) / 12.0 * (2.0 - d)
        return delta_iout / (fsw_mhz * delta_vout * k) * bracket

    def _required_max_esr_ohm(self, vin_v: float, vout_v: float, ripple_current_ratio: float) -> float:
        d = self._duty_cycle(vout_v, vin_v)
        k = ripple_current_ratio
        delta_iout = self._application.load_step_current_a
        delta_vout = self._application.target_voltage_deviation_v
        denominator = 2.0 * delta_iout * (1.0 + k + (k**2) / 12.0 * (1.0 + 1.0 / (1.0 - d)))
        return (2.0 + k) * delta_vout / denominator

    @staticmethod
    def _output_ripple_mv(params: BuckDesignParameters, ripple_current_pp_a: float) -> float:
        fsw_mhz = params.switching_frequency_khz / 1000.0
        cap_term = 1.0 / (8.0 * fsw_mhz * params.output_capacitance_uf)
        return ripple_current_pp_a * (params.output_esr_ohm**2 + cap_term**2) ** 0.5 * 1000.0

    def _power_loss_mw(self, vin_v: float, vout_v: float) -> float:
        """伝導損失(RDSON)＋静止電流損失のみを含む。スイッチング損失の係数はデータシートに
        明記がないため含まれておらず、実際の損失・効率はこれより悪化する点に注意。"""
        d = self._duty_cycle(vout_v, vin_v)
        load_a = self._application.max_load_current_a
        conduction_loss_w = load_a**2 * (
            d * self._device_spec.rds_on_hs_typ_ohm + (1.0 - d) * self._device_spec.rds_on_ls_typ_ohm
        )
        quiescent_loss_w = vin_v * self._device_spec.iq_typ_a
        return (conduction_loss_w + quiescent_loss_w) * 1000.0

    def _junction_temperature_c(self, power_loss_mw: float, ambient_temperature_c: float) -> float:
        return ambient_temperature_c + (power_loss_mw / 1000.0) * self._device_spec.r_theta_ja_pwp_c_per_w

    def evaluate(
        self, params: BuckDesignParameters, vin_v: float, vout_v: float, ambient_temperature_c: float
    ) -> EvaluationResult:
        fsw_mhz = params.switching_frequency_khz / 1000.0
        ripple_current_pp_a = self._inductor_ripple_current_pp_a(params, vin_v, vout_v)
        ripple_current_ratio = self._ripple_current_ratio(ripple_current_pp_a)
        power_loss_mw = self._power_loss_mw(vin_v, vout_v)

        return EvaluationResult(
            output_ripple_mv=self._output_ripple_mv(params, ripple_current_pp_a),
            power_loss_mw=power_loss_mw,
            junction_temperature_c=self._junction_temperature_c(power_loss_mw, ambient_temperature_c),
            ripple_current_ratio=ripple_current_ratio,
            peak_inductor_current_a=self._application.max_load_current_a + ripple_current_pp_a / 2.0,
            required_min_output_capacitance_uf=self._required_min_output_capacitance_uf(
                fsw_mhz, vin_v, vout_v, ripple_current_ratio
            ),
            required_max_esr_ohm=self._required_max_esr_ohm(vin_v, vout_v, ripple_current_ratio),
            required_min_inductance_uh=self._required_min_inductance_uh(vout_v, fsw_mhz),
        )
