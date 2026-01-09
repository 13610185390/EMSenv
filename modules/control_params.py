# -*- coding: utf-8 -*-
"""控制策略模块

对应技术设计文档：03_控制策略模块技术设计.md
负责调度模式、充放电策略、保护参数的配置
"""

from typing import Dict, Any, Optional, Tuple, List
from datetime import time

import gradio as gr

from models.control import (
    ControlParams, DispatchMode, ChargeStrategy, DischargeStrategy,
    PowerControlMode, ChargeDischargeStrategy, ProtectionParams,
    ResponseParams, SchedulePoint, DispatchSchedule,
    CONTROL_TEACHING_META
)
from models.bess import BESSParams
from models.economic import ElectricityPriceParams
from config.default_params import (
    get_default_control_params, create_default_control_params
)
from utils.validators import validate_control_params as _validate_control_params


# =============================================================================
# 模块状态
# =============================================================================
_current_params: Optional[ControlParams] = None


# =============================================================================
# 参数管理函数
# =============================================================================
def get_control_params() -> ControlParams:
    """获取当前控制参数配置

    Returns:
        ControlParams: 控制参数数据类实例
    """
    global _current_params
    if _current_params is None:
        _current_params = create_default_control_params()
    return _current_params


def set_control_params(params: ControlParams) -> Tuple[bool, List[str]]:
    """设置控制参数

    Args:
        params: 控制参数数据类实例

    Returns:
        Tuple[bool, List[str]]: (是否成功, 错误信息列表)
    """
    global _current_params

    ok, errors = validate_control_params(params)
    if not ok:
        return False, errors

    _current_params = params
    return True, []


def validate_control_params(params: ControlParams) -> Tuple[bool, List[str]]:
    """校验控制参数

    Args:
        params: 待校验的参数

    Returns:
        Tuple[bool, List[str]]: (是否通过, 错误信息列表)
    """
    params_dict = {
        "protect_soc_high": params.protection.protect_soc_high,
        "protect_soc_low": params.protection.protect_soc_low,
        "power_limit_factor": params.protection.power_limit_factor,
        "protect_temp_high": params.protection.protect_temp_high,
        "protect_temp_low": params.protection.protect_temp_low,
        "response_time": params.response.response_time,
        "ramp_rate": params.response.ramp_rate,
    }
    return _validate_control_params(params_dict)


def reset_to_default() -> ControlParams:
    """重置为默认参数

    Returns:
        ControlParams: 默认参数实例
    """
    global _current_params
    _current_params = create_default_control_params()
    return _current_params


# =============================================================================
# 调度计划生成
# =============================================================================
def generate_dispatch_schedule(
    control_params: ControlParams,
    bess_params: BESSParams,
    price_params: ElectricityPriceParams,
    load_curve: List[float],
    timestep_minutes: int = 15,
    duration_hours: int = 24
) -> DispatchSchedule:
    """生成调度计划

    Args:
        control_params: 控制参数
        bess_params: BESS参数
        price_params: 电价参数
        load_curve: 负荷曲线
        timestep_minutes: 时间步长
        duration_hours: 仿真时长

    Returns:
        DispatchSchedule: 调度计划
    """
    dispatch_mode = control_params.dispatch_mode

    if dispatch_mode == DispatchMode.ARBITRAGE:
        return _generate_arbitrage_schedule(
            bess_params, price_params, timestep_minutes, duration_hours
        )
    elif dispatch_mode == DispatchMode.LOAD_FOLLOW:
        return _generate_load_follow_schedule(
            bess_params, load_curve, timestep_minutes, duration_hours
        )
    else:
        # 默认返回空调度
        return DispatchSchedule(
            timestep_minutes=timestep_minutes,
            schedule=[
                SchedulePoint(i, 0.0, "待机", bess_params.soc_init)
                for i in range(duration_hours * 60 // timestep_minutes)
            ]
        )


def _generate_arbitrage_schedule(
    bess_params: BESSParams,
    price_params: ElectricityPriceParams,
    timestep_minutes: int,
    duration_hours: int
) -> DispatchSchedule:
    """生成峰谷套利调度计划

    策略：谷时充电，峰时放电

    Args:
        bess_params: BESS参数
        price_params: 电价参数
        timestep_minutes: 时间步长
        duration_hours: 仿真时长

    Returns:
        DispatchSchedule: 调度计划
    """
    from models.economic import PricePeriodType

    timesteps = duration_hours * 60 // timestep_minutes
    schedule = []

    # 获取电价曲线
    price_curve = price_params.get_price_curve(timestep_minutes)

    # 模拟SOC变化
    current_soc = bess_params.soc_init
    timestep_hours = timestep_minutes / 60
    total_charge = 0.0
    total_discharge = 0.0

    for i in range(timesteps):
        # 计算当前时间
        hour = (i * timestep_minutes) // 60
        minute = (i * timestep_minutes) % 60
        current_time = time(hour % 24, minute)

        # 获取当前时段类型
        period_type = price_params.get_period_type_at(current_time)

        power = 0.0
        action = "待机"

        if period_type == PricePeriodType.VALLEY:
            # 谷时充电
            if current_soc < bess_params.soc_max:
                power = -bess_params.power_charge_max  # 负值表示充电
                action = "谷时充电"
                # 计算SOC变化
                energy = abs(power) * timestep_hours * bess_params.efficiency_charge / 100
                soc_change = energy / bess_params.capacity * 100
                current_soc = min(bess_params.soc_max, current_soc + soc_change)
                total_charge += energy

        elif period_type == PricePeriodType.PEAK or period_type == PricePeriodType.CRITICAL:
            # 峰时放电
            if current_soc > bess_params.soc_min:
                power = bess_params.power_discharge_max  # 正值表示放电
                action = "峰时放电"
                # 计算SOC变化
                energy = power * timestep_hours
                soc_change = energy / bess_params.capacity * 100
                current_soc = max(bess_params.soc_min, current_soc - soc_change)
                total_discharge += energy * bess_params.efficiency_discharge / 100

        else:
            action = "平时待机"

        schedule.append(SchedulePoint(
            timestamp=i,
            power=power,
            action=action,
            soc_expected=current_soc
        ))

    return DispatchSchedule(
        schedule=schedule,
        timestep_minutes=timestep_minutes,
        total_charge_kwh=total_charge,
        total_discharge_kwh=total_discharge
    )


def _generate_load_follow_schedule(
    bess_params: BESSParams,
    load_curve: List[float],
    timestep_minutes: int,
    duration_hours: int
) -> DispatchSchedule:
    """生成负荷跟踪调度计划

    策略：削峰填谷，平滑负荷曲线

    Args:
        bess_params: BESS参数
        load_curve: 负荷曲线
        timestep_minutes: 时间步长
        duration_hours: 仿真时长

    Returns:
        DispatchSchedule: 调度计划
    """
    timesteps = duration_hours * 60 // timestep_minutes
    schedule = []

    if not load_curve:
        return DispatchSchedule(timestep_minutes=timestep_minutes)

    # 计算负荷平均值作为目标
    avg_load = sum(load_curve[:timesteps]) / min(len(load_curve), timesteps)

    current_soc = bess_params.soc_init
    timestep_hours = timestep_minutes / 60
    total_charge = 0.0
    total_discharge = 0.0

    for i in range(timesteps):
        load = load_curve[i] if i < len(load_curve) else avg_load
        deviation = load - avg_load

        power = 0.0
        action = "待机"

        if deviation > 10 and current_soc > bess_params.soc_min:
            # 负荷高于平均，放电削峰
            power = min(deviation, bess_params.power_discharge_max)
            action = "削峰放电"
            energy = power * timestep_hours
            soc_change = energy / bess_params.capacity * 100
            current_soc = max(bess_params.soc_min, current_soc - soc_change)
            total_discharge += energy * bess_params.efficiency_discharge / 100

        elif deviation < -10 and current_soc < bess_params.soc_max:
            # 负荷低于平均，充电填谷
            power = -min(abs(deviation), bess_params.power_charge_max)
            action = "填谷充电"
            energy = abs(power) * timestep_hours * bess_params.efficiency_charge / 100
            soc_change = energy / bess_params.capacity * 100
            current_soc = min(bess_params.soc_max, current_soc + soc_change)
            total_charge += energy

        schedule.append(SchedulePoint(
            timestamp=i,
            power=power,
            action=action,
            soc_expected=current_soc
        ))

    return DispatchSchedule(
        schedule=schedule,
        timestep_minutes=timestep_minutes,
        total_charge_kwh=total_charge,
        total_discharge_kwh=total_discharge
    )


# =============================================================================
# Gradio UI组件
# =============================================================================
def create_control_params_tab():
    """创建控制策略标签页

    Returns:
        Tuple[gr.Tab, Dict]: (标签页, 组件字典)
    """
    with gr.Tab("控制策略") as tab:

        gr.Markdown("### 控制策略配置")
        gr.Markdown("配置储能系统的调度模式、充放电策略和保护参数。")

        with gr.Row():
            # 左侧：策略配置
            with gr.Column(scale=1):

                # 调度模式
                with gr.Group():
                    gr.Markdown("#### 调度模式")

                    dispatch_mode = gr.Radio(
                        label="选择调度模式",
                        choices=[
                            ("峰谷套利 - 谷充峰放", "ARBITRAGE"),
                            ("负荷跟踪 - 削峰填谷", "LOAD_FOLLOW"),
                            ("新能源消纳 (待实现)", "RE_SMOOTHING"),
                            ("需量管理 (待实现)", "DEMAND_MANAGEMENT"),
                        ],
                        value="ARBITRAGE",
                        info="选择储能系统的主要运行模式"
                    )

                    # 模式说明
                    mode_description = gr.Markdown(
                        value=CONTROL_TEACHING_META["dispatch_modes"]["ARBITRAGE"]["description"]
                    )

                # 充放电策略
                with gr.Group():
                    gr.Markdown("#### 充放电策略")
                    with gr.Row():
                        charge_strategy = gr.Dropdown(
                            label="充电策略",
                            choices=[
                                ("谷时充电", "VALLEY_CHARGE"),
                                ("低于目标SOC充电", "SOC_TRIGGER_LOW"),
                                ("低电价充电", "PRICE_TRIGGER_LOW"),
                            ],
                            value="VALLEY_CHARGE",
                            info="选择何时开始充电"
                        )
                        discharge_strategy = gr.Dropdown(
                            label="放电策略",
                            choices=[
                                ("峰时放电", "PEAK_DISCHARGE"),
                                ("高于目标SOC放电", "SOC_TRIGGER_HIGH"),
                                ("高电价放电", "PRICE_TRIGGER_HIGH"),
                            ],
                            value="PEAK_DISCHARGE",
                            info="选择何时开始放电"
                        )

                    power_control_mode = gr.Radio(
                        label="功率控制模式",
                        choices=[
                            ("定功率", "CONSTANT_POWER"),
                            ("变功率", "VARIABLE_POWER"),
                            ("优化控制", "OPTIMIZED"),
                        ],
                        value="CONSTANT_POWER",
                        info="功率输出控制方式"
                    )

            # 右侧：保护与响应参数
            with gr.Column(scale=1):

                # 保护参数
                with gr.Group():
                    gr.Markdown("#### 保护参数")

                    with gr.Row():
                        protect_soc_high = gr.Slider(
                            label="过充保护阈值 (%)",
                            minimum=80,
                            maximum=100,
                            value=95.0,
                            step=1,
                            info=CONTROL_TEACHING_META["protection_params"]["protect_soc_high"]["help_text"]
                        )
                        protect_soc_low = gr.Slider(
                            label="过放保护阈值 (%)",
                            minimum=0,
                            maximum=20,
                            value=5.0,
                            step=1,
                            info=CONTROL_TEACHING_META["protection_params"]["protect_soc_low"]["help_text"]
                        )

                    power_limit_factor = gr.Slider(
                        label="功率限制系数",
                        minimum=0.5,
                        maximum=1.0,
                        value=1.0,
                        step=0.05,
                        info=CONTROL_TEACHING_META["protection_params"]["power_limit_factor"]["help_text"]
                    )

                    with gr.Row():
                        protect_temp_high = gr.Slider(
                            label="高温保护阈值 (℃)",
                            minimum=35,
                            maximum=60,
                            value=45.0,
                            step=1,
                            info="电池温度超过此值触发保护"
                        )
                        protect_temp_low = gr.Slider(
                            label="低温保护阈值 (℃)",
                            minimum=-20,
                            maximum=15,
                            value=0.0,
                            step=1,
                            info="电池温度低于此值触发保护"
                        )

                # 响应参数
                with gr.Group():
                    gr.Markdown("#### 响应参数")

                    with gr.Row():
                        response_time = gr.Number(
                            label="响应时间 (ms)",
                            value=100.0,
                            minimum=10,
                            maximum=1000,
                            step=10,
                            info=CONTROL_TEACHING_META["response_params"]["response_time"]["help_text"]
                        )
                        ramp_rate = gr.Number(
                            label="爬坡速率 (kW/s)",
                            value=10.0,
                            minimum=1,
                            maximum=100,
                            step=1,
                            info=CONTROL_TEACHING_META["response_params"]["ramp_rate"]["help_text"]
                        )

        # 操作按钮
        with gr.Row():
            reset_btn = gr.Button("重置为默认值")
            validate_btn = gr.Button("校验参数", variant="primary")

        validation_output = gr.Textbox(
            label="校验结果",
            value="",
            interactive=False,
            lines=2
        )

    # 返回组件字典
    components = {
        "dispatch_mode": dispatch_mode,
        "mode_description": mode_description,
        "charge_strategy": charge_strategy,
        "discharge_strategy": discharge_strategy,
        "power_control_mode": power_control_mode,
        "protect_soc_high": protect_soc_high,
        "protect_soc_low": protect_soc_low,
        "power_limit_factor": power_limit_factor,
        "protect_temp_high": protect_temp_high,
        "protect_temp_low": protect_temp_low,
        "response_time": response_time,
        "ramp_rate": ramp_rate,
        "reset_btn": reset_btn,
        "validate_btn": validate_btn,
        "validation_output": validation_output,
    }

    return tab, components


def setup_control_params_events(components: Dict[str, Any]):
    """设置控制参数事件绑定

    Args:
        components: 组件字典
    """

    def update_mode_description(mode):
        """更新模式说明"""
        descriptions = {
            "ARBITRAGE": CONTROL_TEACHING_META["dispatch_modes"]["ARBITRAGE"]["description"],
            "LOAD_FOLLOW": CONTROL_TEACHING_META["dispatch_modes"]["LOAD_FOLLOW"]["description"],
            "RE_SMOOTHING": CONTROL_TEACHING_META["dispatch_modes"]["RE_SMOOTHING"]["description"],
            "DEMAND_MANAGEMENT": CONTROL_TEACHING_META["dispatch_modes"]["DEMAND_MANAGEMENT"]["description"],
        }
        return descriptions.get(mode, "")

    def on_validate(protect_soc_high, protect_soc_low, power_limit_factor,
                    protect_temp_high, protect_temp_low, response_time, ramp_rate):
        """校验参数"""
        params_dict = {
            "protect_soc_high": protect_soc_high,
            "protect_soc_low": protect_soc_low,
            "power_limit_factor": power_limit_factor,
            "protect_temp_high": protect_temp_high,
            "protect_temp_low": protect_temp_low,
            "response_time": response_time,
            "ramp_rate": ramp_rate,
        }

        ok, errors = _validate_control_params(params_dict)
        if ok:
            return "✅ 参数校验通过！"
        else:
            return "❌ 校验失败:\n" + "\n".join(f"• {e}" for e in errors)

    def on_reset():
        """重置参数"""
        defaults = get_default_control_params()
        return (
            "ARBITRAGE",
            "VALLEY_CHARGE",
            "PEAK_DISCHARGE",
            "CONSTANT_POWER",
            defaults["protect_soc_high"],
            defaults["protect_soc_low"],
            defaults["power_limit_factor"],
            defaults["protect_temp_high"],
            defaults["protect_temp_low"],
            defaults["response_time"],
            defaults["ramp_rate"],
            "✅ 已重置为默认参数"
        )

    # 绑定模式切换
    components["dispatch_mode"].change(
        fn=update_mode_description,
        inputs=[components["dispatch_mode"]],
        outputs=[components["mode_description"]]
    )

    # 绑定校验按钮
    validate_inputs = [
        components["protect_soc_high"],
        components["protect_soc_low"],
        components["power_limit_factor"],
        components["protect_temp_high"],
        components["protect_temp_low"],
        components["response_time"],
        components["ramp_rate"],
    ]

    components["validate_btn"].click(
        fn=on_validate,
        inputs=validate_inputs,
        outputs=components["validation_output"]
    )

    # 绑定重置按钮
    reset_outputs = [
        components["dispatch_mode"],
        components["charge_strategy"],
        components["discharge_strategy"],
        components["power_control_mode"],
        components["protect_soc_high"],
        components["protect_soc_low"],
        components["power_limit_factor"],
        components["protect_temp_high"],
        components["protect_temp_low"],
        components["response_time"],
        components["ramp_rate"],
        components["validation_output"],
    ]

    components["reset_btn"].click(
        fn=on_reset,
        inputs=[],
        outputs=reset_outputs
    )
