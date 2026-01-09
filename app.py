# -*- coding: utf-8 -*-
"""储能EMS教学仿真平台 - 主入口文件

对应设计文档：开发规划文档 3.2节
整合所有功能模块，提供统一的Web界面
"""

import gradio as gr
from typing import Dict, Any, Optional

from config import APP_NAME, APP_VERSION
from config.default_params import (
    create_default_bess_params,
    create_default_economic_params,
    create_default_control_params,
)

# 导入模块
from modules.basic_params import (
    create_basic_params_tab,
    setup_basic_params_events,
    get_bess_params,
    set_bess_params,
)
from modules.economic_params import (
    create_economic_params_tab,
    setup_economic_params_events,
    get_economic_params,
    set_economic_params,
)
from modules.control_params import (
    create_control_params_tab,
    setup_control_params_events,
    get_control_params,
    set_control_params,
)
from modules.simulation import (
    create_simulation_tab,
    setup_simulation_events,
    run_simulation,
    get_load_profile,
    calculate_annual_projection,
    plot_simulation_results,
)

from modules.learning_center import (
    create_learning_center_tab,
    setup_learning_center_events,
)

from modules.ems_architecture import (
    create_ems_architecture_tab,
    setup_ems_architecture_events,
)

from modules.fault_diagnosis import (
    create_fault_diagnosis_tab,
    setup_fault_diagnosis_events,
)

from models.bess import BESSParams, BatteryType
from models.economic import (
    EconomicParams, ElectricityPriceParams,
    CostParams, FinancialParams
)
from models.control import (
    ControlParams, DispatchMode, ChargeStrategy, DischargeStrategy,
    PowerControlMode, ChargeDischargeStrategy, ProtectionParams, ResponseParams
)
from models.simulation import SimulationConfig, LoadProfileType


# =============================================================================
# 应用状态管理
# =============================================================================
class AppState:
    """应用状态管理类

    管理模块间共享的参数状态
    """

    def __init__(self):
        self._bess_params: Optional[BESSParams] = None
        self._economic_params: Optional[EconomicParams] = None
        self._control_params: Optional[ControlParams] = None

    @property
    def bess_params(self) -> BESSParams:
        if self._bess_params is None:
            self._bess_params = create_default_bess_params()
        return self._bess_params

    @bess_params.setter
    def bess_params(self, value: BESSParams):
        self._bess_params = value

    @property
    def economic_params(self) -> EconomicParams:
        if self._economic_params is None:
            self._economic_params = create_default_economic_params()
        return self._economic_params

    @economic_params.setter
    def economic_params(self, value: EconomicParams):
        self._economic_params = value

    @property
    def control_params(self) -> ControlParams:
        if self._control_params is None:
            self._control_params = create_default_control_params()
        return self._control_params

    @control_params.setter
    def control_params(self, value: ControlParams):
        self._control_params = value


# 全局应用状态
app_state = AppState()


# =============================================================================
# 参数收集函数
# =============================================================================
def collect_bess_params_from_ui(
    name, battery_type, capacity, power_rated,
    power_charge_max, power_discharge_max,
    efficiency_charge, efficiency_discharge, self_discharge_rate,
    soc_min, soc_max, soc_init,
    cycle_life, calendar_life, degradation_rate
) -> BESSParams:
    """从UI组件收集BESS参数"""

    # 解析电池类型
    bt = BatteryType.LFP
    for t in BatteryType:
        if t.name == battery_type or t.value == battery_type:
            bt = t
            break

    return BESSParams(
        name=name or "BESS_01",
        battery_type=bt,
        enabled=True,
        capacity=float(capacity or 100),
        power_rated=float(power_rated or 50),
        power_charge_max=float(power_charge_max) if power_charge_max else None,
        power_discharge_max=float(power_discharge_max) if power_discharge_max else None,
        efficiency_charge=float(efficiency_charge or 95),
        efficiency_discharge=float(efficiency_discharge or 95),
        self_discharge_rate=float(self_discharge_rate or 0.1),
        soc_min=float(soc_min or 10),
        soc_max=float(soc_max or 90),
        soc_init=float(soc_init or 50),
        cycle_life=int(cycle_life or 6000),
        calendar_life=int(calendar_life or 15),
        degradation_rate=float(degradation_rate or 2.0),
    )


def collect_economic_params_from_ui(
    price_valley, price_flat, price_peak, price_critical, price_feed_in,
    cost_per_kwh, cost_per_kw, cost_install_ratio, cost_om_ratio,
    discount_rate, project_years, residual_ratio
) -> EconomicParams:
    """从UI组件收集经济参数"""

    price_params = ElectricityPriceParams(
        price_valley=float(price_valley or 0.4),
        price_flat=float(price_flat or 0.8),
        price_peak=float(price_peak or 1.2),
        price_critical=float(price_critical) if price_critical else None,
        price_feed_in=float(price_feed_in or 0.5),
    )

    cost_params = CostParams(
        cost_per_kwh=float(cost_per_kwh or 1500),
        cost_per_kw=float(cost_per_kw or 500),
        cost_install_ratio=float(cost_install_ratio or 10),
        cost_om_ratio=float(cost_om_ratio or 2),
    )

    financial_params = FinancialParams(
        discount_rate=float(discount_rate or 8),
        project_years=int(project_years or 15),
        residual_ratio=float(residual_ratio or 5),
    )

    return EconomicParams(
        price_params=price_params,
        cost_params=cost_params,
        financial_params=financial_params,
    )


def collect_control_params_from_ui(
    dispatch_mode, charge_strategy, discharge_strategy, power_control_mode,
    protect_soc_high, protect_soc_low, power_limit_factor,
    protect_temp_high, protect_temp_low,
    response_time, ramp_rate
) -> ControlParams:
    """从UI组件收集控制参数"""

    # 解析调度模式
    dm = DispatchMode.ARBITRAGE
    for mode in DispatchMode:
        if mode.name == dispatch_mode or mode.value == dispatch_mode:
            dm = mode
            break

    # 解析充电策略
    cs = ChargeStrategy.VALLEY_CHARGE
    for s in ChargeStrategy:
        if s.name == charge_strategy or s.value == charge_strategy:
            cs = s
            break

    # 解析放电策略
    ds = DischargeStrategy.PEAK_DISCHARGE
    for s in DischargeStrategy:
        if s.name == discharge_strategy or s.value == discharge_strategy:
            ds = s
            break

    # 解析功率控制模式
    pcm = PowerControlMode.CONSTANT_POWER
    for m in PowerControlMode:
        if m.name == power_control_mode or m.value == power_control_mode:
            pcm = m
            break

    charge_discharge = ChargeDischargeStrategy(
        charge_strategy=cs,
        discharge_strategy=ds,
        power_control_mode=pcm,
    )

    protection = ProtectionParams(
        protect_soc_high=float(protect_soc_high or 95),
        protect_soc_low=float(protect_soc_low or 5),
        power_limit_factor=float(power_limit_factor or 1.0),
        protect_temp_high=float(protect_temp_high or 45),
        protect_temp_low=float(protect_temp_low or 0),
    )

    response = ResponseParams(
        response_time=float(response_time or 100),
        ramp_rate=float(ramp_rate or 10),
    )

    return ControlParams(
        dispatch_mode=dm,
        charge_discharge=charge_discharge,
        protection=protection,
        response=response,
    )


# =============================================================================
# 主应用创建
# =============================================================================
def create_app() -> gr.Blocks:
    """创建Gradio应用

    Returns:
        gr.Blocks: Gradio应用实例
    """

    with gr.Blocks(
        title=APP_NAME,
        theme=gr.themes.Soft(),
        css="""
            .main-title { text-align: center; margin-bottom: 10px; }
            .version-info { text-align: center; color: #666; font-size: 0.9em; }
        """
    ) as app:

        # 标题区域
        gr.Markdown(
            f"# {APP_NAME}",
            elem_classes=["main-title"]
        )
        gr.Markdown(
            f"版本 {APP_VERSION} | 交互式储能系统仿真与教学平台",
            elem_classes=["version-info"]
        )

        # 主标签页
        with gr.Tabs() as main_tabs:

            # ===== 基础参数标签页 =====
            basic_tab, basic_components = create_basic_params_tab()

            # ===== 经济参数标签页 =====
            economic_tab, economic_components = create_economic_params_tab()

            # ===== 控制策略标签页 =====
            control_tab, control_components = create_control_params_tab()

            # ===== 仿真计算标签页 =====
            simulation_tab, simulation_components = create_simulation_tab()

            # ===== 教学引导标签页 =====
            learning_tab, learning_components = create_learning_center_tab()

            # ===== EMS架构标签页 =====
            ems_tab, ems_components = create_ems_architecture_tab()

            # ===== 故障诊断标签页 =====
            fault_tab, fault_components = create_fault_diagnosis_tab()

        # ===== 设置事件绑定 =====

        # 基础参数事件
        setup_basic_params_events(basic_components)

        # 经济参数事件
        setup_economic_params_events(economic_components)

        # 控制策略事件
        setup_control_params_events(control_components)

        # 仿真事件 - 需要传入参数获取函数
        def get_current_bess_params():
            """获取当前BESS参数"""
            return collect_bess_params_from_ui(
                basic_components["name"].value,
                basic_components["battery_type"].value,
                basic_components["capacity"].value,
                basic_components["power_rated"].value,
                basic_components["power_charge_max"].value,
                basic_components["power_discharge_max"].value,
                basic_components["efficiency_charge"].value,
                basic_components["efficiency_discharge"].value,
                basic_components["self_discharge_rate"].value,
                basic_components["soc_min"].value,
                basic_components["soc_max"].value,
                basic_components["soc_init"].value,
                basic_components["cycle_life"].value,
                basic_components["calendar_life"].value,
                basic_components["degradation_rate"].value,
            )

        def get_current_economic_params():
            """获取当前经济参数"""
            return collect_economic_params_from_ui(
                economic_components["price_valley"].value,
                economic_components["price_flat"].value,
                economic_components["price_peak"].value,
                economic_components["price_critical"].value,
                economic_components["price_feed_in"].value,
                economic_components["cost_per_kwh"].value,
                economic_components["cost_per_kw"].value,
                economic_components["cost_install_ratio"].value,
                economic_components["cost_om_ratio"].value,
                economic_components["discount_rate"].value,
                economic_components["project_years"].value,
                economic_components["residual_ratio"].value,
            )

        def get_current_control_params():
            """获取当前控制参数"""
            return collect_control_params_from_ui(
                control_components["dispatch_mode"].value,
                control_components["charge_strategy"].value,
                control_components["discharge_strategy"].value,
                control_components["power_control_mode"].value,
                control_components["protect_soc_high"].value,
                control_components["protect_soc_low"].value,
                control_components["power_limit_factor"].value,
                control_components["protect_temp_high"].value,
                control_components["protect_temp_low"].value,
                control_components["response_time"].value,
                control_components["ramp_rate"].value,
            )

        # 自定义仿真执行函数（整合所有参数）
        def run_integrated_simulation(
            duration, timestep, load_profile, load_file, load_scale,
            # BESS参数
            bess_name, battery_type, capacity, power_rated,
            power_charge_max, power_discharge_max,
            eff_charge, eff_discharge, self_discharge,
            soc_min, soc_max, soc_init,
            cycle_life, calendar_life, degradation,
            # 经济参数
            price_valley, price_flat, price_peak, price_critical, price_feed_in,
            cost_per_kwh, cost_per_kw, cost_install_ratio, cost_om_ratio,
            discount_rate, project_years, residual_ratio,
            # 控制参数
            dispatch_mode, charge_strategy, discharge_strategy, power_control_mode,
            protect_soc_high, protect_soc_low, power_limit_factor,
            protect_temp_high, protect_temp_low,
            response_time, ramp_rate
        ):
            """执行集成仿真"""
            try:
                # 收集参数
                bess_params = collect_bess_params_from_ui(
                    bess_name, battery_type, capacity, power_rated,
                    power_charge_max, power_discharge_max,
                    eff_charge, eff_discharge, self_discharge,
                    soc_min, soc_max, soc_init,
                    cycle_life, calendar_life, degradation
                )

                economic_params = collect_economic_params_from_ui(
                    price_valley, price_flat, price_peak, price_critical, price_feed_in,
                    cost_per_kwh, cost_per_kw, cost_install_ratio, cost_om_ratio,
                    discount_rate, project_years, residual_ratio
                )

                control_params = collect_control_params_from_ui(
                    dispatch_mode, charge_strategy, discharge_strategy, power_control_mode,
                    protect_soc_high, protect_soc_low, power_limit_factor,
                    protect_temp_high, protect_temp_low,
                    response_time, ramp_rate
                )

                # 解析负荷类型
                load_type = LoadProfileType.INDUSTRIAL
                for lt in LoadProfileType:
                    if lt.name == load_profile:
                        load_type = lt
                        break

                # 创建仿真配置
                config = SimulationConfig(
                    duration_hours=int(duration),
                    timestep_minutes=int(timestep),
                    load_profile_type=load_type,
                    load_scale_factor=float(load_scale)
                )

                # 执行仿真
                result = run_simulation(
                    bess_params,
                    economic_params,
                    control_params,
                    config
                )

                # 绘制图表
                power_fig, soc_fig = plot_simulation_results(result)

                # 格式化统计表格
                from modules.simulation import format_statistics_table
                economic_data, operation_data = format_statistics_table(result)

                # 年度预测
                annual_data = calculate_annual_projection(
                    result, bess_params, economic_params
                )

                from modules.simulation import format_annual_table
                annual_table = format_annual_table(annual_data)

                return (
                    power_fig, soc_fig,
                    economic_data, operation_data,
                    annual_table,
                    f"仿真完成 - {config.timesteps}个时间步"
                )

            except Exception as e:
                import traceback
                error_msg = f"仿真失败: {str(e)}\n{traceback.format_exc()}"
                return (None, None, [], [], [], error_msg)

        # 绑定仿真按钮 - 收集所有参数
        all_inputs = [
            # 仿真配置
            simulation_components["duration"],
            simulation_components["timestep"],
            simulation_components["load_profile"],
            simulation_components["load_file"],
            simulation_components["load_scale"],
            # BESS参数
            basic_components["name"],
            basic_components["battery_type"],
            basic_components["capacity"],
            basic_components["power_rated"],
            basic_components["power_charge_max"],
            basic_components["power_discharge_max"],
            basic_components["efficiency_charge"],
            basic_components["efficiency_discharge"],
            basic_components["self_discharge_rate"],
            basic_components["soc_min"],
            basic_components["soc_max"],
            basic_components["soc_init"],
            basic_components["cycle_life"],
            basic_components["calendar_life"],
            basic_components["degradation_rate"],
            # 经济参数
            economic_components["price_valley"],
            economic_components["price_flat"],
            economic_components["price_peak"],
            economic_components["price_critical"],
            economic_components["price_feed_in"],
            economic_components["cost_per_kwh"],
            economic_components["cost_per_kw"],
            economic_components["cost_install_ratio"],
            economic_components["cost_om_ratio"],
            economic_components["discount_rate"],
            economic_components["project_years"],
            economic_components["residual_ratio"],
            # 控制参数
            control_components["dispatch_mode"],
            control_components["charge_strategy"],
            control_components["discharge_strategy"],
            control_components["power_control_mode"],
            control_components["protect_soc_high"],
            control_components["protect_soc_low"],
            control_components["power_limit_factor"],
            control_components["protect_temp_high"],
            control_components["protect_temp_low"],
            control_components["response_time"],
            control_components["ramp_rate"],
        ]

        simulation_outputs = [
            simulation_components["power_plot"],
            simulation_components["soc_plot"],
            simulation_components["economic_stats"],
            simulation_components["operation_stats"],
            simulation_components["annual_stats"],
            simulation_components["status_text"],
        ]

        simulation_components["run_btn"].click(
            fn=run_integrated_simulation,
            inputs=all_inputs,
            outputs=simulation_outputs
        )

        # 教学引导事件
        setup_learning_center_events(learning_components)

        # EMS架构事件
        setup_ems_architecture_events(ems_components)

        # 故障诊断事件
        setup_fault_diagnosis_events(fault_components)

        # 底部信息
        gr.Markdown("---")
        gr.Markdown(
            "储能EMS教学仿真平台 | "
            "用于教学目的的储能系统仿真工具 | "
            f"v{APP_VERSION}"
        )

    return app


def main():
    """主函数"""
    print(f"启动 {APP_NAME} v{APP_VERSION}")
    print("=" * 50)

    app = create_app()

    print("应用创建完成，正在启动服务器...")
    print("访问地址: http://localhost:7860")
    print("=" * 50)

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()
