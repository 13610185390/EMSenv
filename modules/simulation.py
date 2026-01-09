# -*- coding: utf-8 -*-
"""仿真计算模块

对应技术设计文档：04_仿真计算模块技术设计.md
负责储能系统运行仿真、时序计算、结果统计
"""

import math
from typing import Dict, Any, Optional, Tuple, List, Callable

import gradio as gr

from models.simulation import (
    LoadProfileType, SimulationConfig, BESSState,
    TimeStepResult, SimulationResult, SIMULATION_TEACHING_META
)
from models.bess import BESSParams
from models.economic import EconomicParams, ElectricityPriceParams
from models.control import ControlParams, DispatchSchedule, SchedulePoint
from modules.control_params import generate_dispatch_schedule


# =============================================================================
# 负荷曲线生成
# =============================================================================
def get_load_profile(
    profile_type: LoadProfileType,
    timestep_minutes: int = 15,
    duration_hours: int = 24,
    scale_factor: float = 1.0
) -> List[float]:
    """获取预设负荷曲线

    Args:
        profile_type: 负荷曲线类型
        timestep_minutes: 时间步长
        duration_hours: 时长
        scale_factor: 缩放系数

    Returns:
        List[float]: 负荷功率序列 (kW)
    """
    timesteps = int(duration_hours * 60 / timestep_minutes)

    if profile_type == LoadProfileType.INDUSTRIAL:
        base_curve = _generate_industrial_profile(timesteps)
    elif profile_type == LoadProfileType.RESIDENTIAL:
        base_curve = _generate_residential_profile(timesteps)
    elif profile_type == LoadProfileType.COMMERCIAL:
        base_curve = _generate_commercial_profile(timesteps)
    else:
        # 默认平坦负荷
        base_curve = [100.0] * timesteps

    return [p * scale_factor for p in base_curve]


def _generate_industrial_profile(timesteps: int) -> List[float]:
    """生成典型工商业负荷曲线

    特点：
    - 8:00-12:00 上升至峰值
    - 12:00-14:00 午间小幅下降
    - 14:00-18:00 维持高位
    - 18:00-22:00 逐步下降
    - 22:00-8:00 低谷
    """
    hours_per_step = 24 / timesteps
    profile = []

    for i in range(timesteps):
        hour = i * hours_per_step

        if 0 <= hour < 8:
            # 夜间低谷
            load = 40 + 10 * math.sin(hour / 8 * math.pi)
        elif 8 <= hour < 12:
            # 上午上升
            load = 50 + 50 * (hour - 8) / 4
        elif 12 <= hour < 14:
            # 午间
            load = 90 + 10 * math.sin((hour - 12) * math.pi / 2)
        elif 14 <= hour < 18:
            # 下午高峰
            load = 100 - 10 * (hour - 14) / 4
        elif 18 <= hour < 22:
            # 傍晚下降
            load = 90 - 40 * (hour - 18) / 4
        else:
            # 夜间
            load = 50 - 10 * (hour - 22) / 2

        profile.append(max(30, load))

    return profile


def _generate_residential_profile(timesteps: int) -> List[float]:
    """生成典型居民负荷曲线

    特点：
    - 早高峰 7:00-9:00
    - 晚高峰 18:00-22:00
    - 其他时段较低
    """
    hours_per_step = 24 / timesteps
    profile = []

    for i in range(timesteps):
        hour = i * hours_per_step

        if 0 <= hour < 6:
            load = 20
        elif 6 <= hour < 9:
            load = 20 + 40 * (hour - 6) / 3
        elif 9 <= hour < 17:
            load = 30
        elif 17 <= hour < 21:
            load = 30 + 70 * (1 - abs(hour - 19) / 2)
        elif 21 <= hour < 23:
            load = 60 - 30 * (hour - 21) / 2
        else:
            load = 30

        profile.append(max(15, load))

    return profile


def _generate_commercial_profile(timesteps: int) -> List[float]:
    """生成典型商业负荷曲线

    特点：
    - 营业时间 9:00-21:00 负荷较高
    - 午间和傍晚有小高峰
    """
    hours_per_step = 24 / timesteps
    profile = []

    for i in range(timesteps):
        hour = i * hours_per_step

        if 0 <= hour < 9:
            load = 30
        elif 9 <= hour < 12:
            load = 30 + 50 * (hour - 9) / 3
        elif 12 <= hour < 14:
            load = 85
        elif 14 <= hour < 18:
            load = 75
        elif 18 <= hour < 21:
            load = 90
        else:
            load = 40

        profile.append(max(20, load))

    return profile


def load_custom_profile(filepath: str) -> Tuple[Optional[List[float]], str]:
    """加载自定义负荷曲线

    Args:
        filepath: CSV文件路径

    Returns:
        Tuple[Optional[List[float]], str]: (负荷功率序列 或 None, 消息)
    """
    try:
        import pandas as pd
        df = pd.read_csv(filepath)

        # 尝试查找负荷列
        load_columns = ['load', 'power', 'kw', '负荷', '功率']
        load_col = None

        for col in df.columns:
            if col.lower() in [c.lower() for c in load_columns]:
                load_col = col
                break

        if load_col is None:
            # 使用第一个数值列
            for col in df.columns:
                if df[col].dtype in ['int64', 'float64']:
                    load_col = col
                    break

        if load_col is None:
            return None, "未找到有效的负荷数据列"

        load_data = df[load_col].tolist()
        return load_data, f"成功加载 {len(load_data)} 个数据点"

    except ImportError:
        return None, "需要安装pandas库才能加载CSV文件"
    except Exception as e:
        return None, f"加载失败: {str(e)}"


# =============================================================================
# 核心仿真引擎
# =============================================================================
def run_simulation(
    bess_params: BESSParams,
    economic_params: EconomicParams,
    control_params: ControlParams,
    config: SimulationConfig,
    progress_callback: Optional[Callable[[float], None]] = None
) -> SimulationResult:
    """执行仿真计算

    Args:
        bess_params: BESS参数
        economic_params: 经济参数
        control_params: 控制参数
        config: 仿真配置
        progress_callback: 进度回调函数，参数为进度百分比(0-100)

    Returns:
        SimulationResult: 仿真结果
    """
    # 1. 初始化结果
    result = SimulationResult(
        config=config,
        bess_params=bess_params,
        economic_params=economic_params,
        control_params=control_params
    )

    # 2. 获取负荷曲线
    if config.load_data is not None:
        load_curve = config.load_data
    else:
        load_curve = get_load_profile(
            config.load_profile_type,
            config.timestep_minutes,
            config.duration_hours,
            config.load_scale_factor
        )

    # 3. 生成调度计划
    schedule = generate_dispatch_schedule(
        control_params,
        bess_params,
        economic_params.price_params,
        load_curve,
        config.timestep_minutes,
        config.duration_hours
    )

    # 4. 初始化BESS状态
    state = BESSState(
        soc=bess_params.soc_init,
        power=0.0,
        energy_charged=0.0,
        energy_discharged=0.0,
        cycles=0.0
    )

    # 5. 获取电价曲线
    timesteps = config.timesteps
    price_curve = economic_params.price_params.get_price_curve(config.timestep_minutes)

    # 扩展价格曲线以覆盖仿真时长
    if len(price_curve) < timesteps:
        # 循环填充
        full_price = []
        for i in range(timesteps):
            full_price.append(price_curve[i % len(price_curve)])
        price_curve = full_price

    # 扩展负荷曲线
    if len(load_curve) < timesteps:
        full_load = []
        for i in range(timesteps):
            full_load.append(load_curve[i % len(load_curve)])
        load_curve = full_load

    # 6. 时序仿真循环
    for i in range(timesteps):
        # 进度回调
        if progress_callback:
            progress_callback((i + 1) / timesteps * 100)

        # 获取调度点
        if i < len(schedule.schedule):
            schedule_point = schedule.schedule[i]
        else:
            # 超出调度计划则待机
            schedule_point = SchedulePoint(
                timestamp=i,
                power=0.0,
                action="待机",
                soc_expected=state.soc
            )

        # 执行单步仿真
        step_result = _simulate_timestep(
            i,
            state,
            schedule_point,
            load_curve[i],
            price_curve[i],
            bess_params,
            control_params,
            config
        )

        result.timestep_results.append(step_result)

        # 更新状态
        state = _update_state(state, step_result, bess_params, config)

    # 7. 计算统计指标
    _calculate_summary_statistics(result, load_curve, price_curve, bess_params)

    return result


def _simulate_timestep(
    index: int,
    state: BESSState,
    schedule_point: SchedulePoint,
    load_power: float,
    price: float,
    bess_params: BESSParams,
    control_params: ControlParams,
    config: SimulationConfig
) -> TimeStepResult:
    """单时间步仿真

    Args:
        index: 时间步索引
        state: 当前BESS状态
        schedule_point: 调度点
        load_power: 负荷功率 (kW)
        price: 当时电价 (元/kWh)
        bess_params: BESS参数
        control_params: 控制参数
        config: 仿真配置

    Returns:
        TimeStepResult: 单步仿真结果
    """
    timestep_hours = config.timestep_hours

    # 获取调度功率
    scheduled_power = schedule_point.power  # 正放负充

    # 应用保护逻辑
    actual_power = _apply_protection(
        scheduled_power,
        state,
        bess_params,
        control_params.protection
    )

    # 计算充放电量和SOC变化
    if actual_power < 0:  # 充电
        energy_charge = abs(actual_power) * timestep_hours
        energy_discharge = 0.0
        eta = bess_params.efficiency_charge / 100
        soc_delta = energy_charge * eta / bess_params.capacity * 100
    elif actual_power > 0:  # 放电
        energy_charge = 0.0
        energy_discharge = actual_power * timestep_hours
        eta = bess_params.efficiency_discharge / 100
        soc_delta = -energy_discharge / eta / bess_params.capacity * 100
    else:  # 待机
        energy_charge = 0.0
        energy_discharge = 0.0
        soc_delta = 0.0

    # 更新SOC（限制在合理范围内）
    new_soc = state.soc + soc_delta
    new_soc = max(0, min(100, new_soc))

    # 计算电网功率（正值表示从电网购电，负值表示向电网售电）
    grid_power = load_power - actual_power

    # 计算净负荷
    net_load = load_power - actual_power

    # 计算电费
    if grid_power > 0:
        cost = grid_power * timestep_hours * price
    else:
        # 售电
        feed_in_price = economic_params.price_params.price_feed_in if hasattr(
            economic_params, 'price_params'
        ) else price * 0.5
        cost = grid_power * timestep_hours * feed_in_price

    # 确定动作描述
    action = schedule_point.action
    if actual_power != scheduled_power:
        if actual_power == 0:
            action = f"{action}(保护停止)"
        else:
            action = f"{action}(功率限制)"

    return TimeStepResult(
        timestamp=index,
        time_hours=index * timestep_hours,
        soc=new_soc,
        power_bess=actual_power,
        energy_charge=energy_charge,
        energy_discharge=energy_discharge,
        load_power=load_power,
        grid_power=grid_power,
        net_load=net_load,
        electricity_price=price,
        cost=cost,
        action=action
    )


def _apply_protection(
    scheduled_power: float,
    state: BESSState,
    bess_params: BESSParams,
    protection_params
) -> float:
    """应用保护逻辑

    Args:
        scheduled_power: 调度功率
        state: 当前状态
        bess_params: BESS参数
        protection_params: 保护参数

    Returns:
        float: 实际功率
    """
    actual_power = scheduled_power

    # 过充保护
    if scheduled_power < 0:  # 充电
        if state.soc >= protection_params.protect_soc_high:
            actual_power = 0.0  # 停止充电

    # 过放保护
    if scheduled_power > 0:  # 放电
        if state.soc <= protection_params.protect_soc_low:
            actual_power = 0.0  # 停止放电

    # 功率限制
    max_power = bess_params.power_rated * protection_params.power_limit_factor
    if actual_power > max_power:
        actual_power = max_power
    elif actual_power < -max_power:
        actual_power = -max_power

    # 充放电功率上限
    if actual_power < 0:  # 充电
        max_charge = bess_params.power_charge_max or bess_params.power_rated
        if abs(actual_power) > max_charge:
            actual_power = -max_charge
    elif actual_power > 0:  # 放电
        max_discharge = bess_params.power_discharge_max or bess_params.power_rated
        if actual_power > max_discharge:
            actual_power = max_discharge

    return actual_power


def _update_state(
    state: BESSState,
    step_result: TimeStepResult,
    bess_params: BESSParams,
    config: SimulationConfig
) -> BESSState:
    """更新BESS状态

    Args:
        state: 当前状态
        step_result: 单步结果
        bess_params: BESS参数
        config: 仿真配置

    Returns:
        BESSState: 新状态
    """
    # 更新累计能量
    new_energy_charged = state.energy_charged + step_result.energy_charge
    new_energy_discharged = state.energy_discharged + step_result.energy_discharge

    # 计算等效循环次数
    total_throughput = (new_energy_charged + new_energy_discharged) / 2
    new_cycles = total_throughput / bess_params.capacity

    return BESSState(
        soc=step_result.soc,
        power=step_result.power_bess,
        energy_charged=new_energy_charged,
        energy_discharged=new_energy_discharged,
        cycles=new_cycles,
        temperature=state.temperature  # 温度模型待实现
    )


def _calculate_summary_statistics(
    result: SimulationResult,
    load_curve: List[float],
    price_curve: List[float],
    bess_params: BESSParams
):
    """计算汇总统计指标

    Args:
        result: 仿真结果（将被修改）
        load_curve: 负荷曲线
        price_curve: 电价曲线
        bess_params: BESS参数
    """
    timestep_hours = result.config.timestep_hours

    # 能量统计
    result.total_charge_kwh = sum(r.energy_charge for r in result.timestep_results)
    result.total_discharge_kwh = sum(r.energy_discharge for r in result.timestep_results)

    # 系统效率
    if result.total_charge_kwh > 0:
        result.system_efficiency = (
            result.total_discharge_kwh / result.total_charge_kwh * 100
        )

    # 等效循环
    throughput = (result.total_charge_kwh + result.total_discharge_kwh) / 2
    result.equivalent_cycles = throughput / bess_params.capacity

    # 利用率
    max_possible_discharge = bess_params.capacity * (
        bess_params.soc_max - bess_params.soc_min
    ) / 100
    if max_possible_discharge > 0:
        result.capacity_utilization = (
            result.total_discharge_kwh / max_possible_discharge * 100
        )

    max_energy = bess_params.power_rated * result.config.duration_hours
    if max_energy > 0:
        result.power_utilization = (
            (result.total_charge_kwh + result.total_discharge_kwh) /
            (2 * max_energy) * 100
        )

    # 经济统计
    charge_costs = []
    discharge_revenues = []

    for r in result.timestep_results:
        if r.energy_charge > 0:
            charge_costs.append(r.energy_charge * r.electricity_price)
        if r.energy_discharge > 0:
            discharge_revenues.append(r.energy_discharge * r.electricity_price)

    result.total_charge_cost = sum(charge_costs)
    result.total_discharge_revenue = sum(discharge_revenues)
    result.arbitrage_profit = result.total_discharge_revenue - result.total_charge_cost

    # 基准电费（无储能情况）
    timesteps = len(result.timestep_results)
    result.baseline_cost = sum(
        load_curve[i] * timestep_hours * price_curve[i]
        for i in range(min(len(load_curve), timesteps))
    )

    # 实际电费
    actual_cost = sum(r.cost for r in result.timestep_results)
    result.cost_saving = result.baseline_cost - actual_cost

    # SOC统计
    soc_values = [r.soc for r in result.timestep_results]
    if soc_values:
        result.soc_min_actual = min(soc_values)
        result.soc_max_actual = max(soc_values)
        result.soc_final = soc_values[-1]
    else:
        result.soc_min_actual = bess_params.soc_init
        result.soc_max_actual = bess_params.soc_init
        result.soc_final = bess_params.soc_init


# =============================================================================
# 统计与预测
# =============================================================================
def calculate_statistics(result: SimulationResult) -> Dict[str, float]:
    """计算仿真统计指标

    Args:
        result: 仿真结果

    Returns:
        dict: 统计指标字典
    """
    return result.get_summary_dict()


def calculate_annual_projection(
    daily_result: SimulationResult,
    bess_params: BESSParams,
    economic_params: EconomicParams
) -> Dict[str, float]:
    """计算年度经济预测

    Args:
        daily_result: 日仿真结果
        bess_params: BESS参数
        economic_params: 经济参数

    Returns:
        dict: 年度经济指标
    """
    cost_params = economic_params.cost_params
    fin_params = economic_params.financial_params

    # 日收益
    daily_profit = daily_result.arbitrage_profit

    # 年运营天数（假设365天）
    operating_days = 365

    # 年收益
    annual_revenue = daily_profit * operating_days

    # 初始投资
    initial_investment = cost_params.calculate_initial_investment(
        bess_params.capacity,
        bess_params.power_rated
    )

    # 年运营成本
    annual_opex = cost_params.calculate_annual_opex(initial_investment)

    # 净年收益
    net_annual_revenue = annual_revenue - annual_opex

    # 静态回收期
    if net_annual_revenue > 0:
        static_payback = initial_investment / net_annual_revenue
    else:
        static_payback = float('inf')

    # 年等效循环
    annual_cycles = daily_result.equivalent_cycles * operating_days

    # 预计寿命（按循环寿命计算）
    if annual_cycles > 0:
        expected_life_years = bess_params.cycle_life / annual_cycles
    else:
        expected_life_years = bess_params.calendar_life

    return {
        'daily_profit': daily_profit,
        'annual_revenue': annual_revenue,
        'annual_opex': annual_opex,
        'net_annual_revenue': net_annual_revenue,
        'initial_investment': initial_investment,
        'static_payback': static_payback,
        'annual_cycles': annual_cycles,
        'expected_life_years': min(expected_life_years, bess_params.calendar_life),
        # 扩展指标预留
        'npv': None,
        'irr': None,
        'lcoe': None,
    }


# =============================================================================
# 可视化函数
# =============================================================================
def plot_simulation_results(result: SimulationResult):
    """绘制仿真结果图表

    Args:
        result: 仿真结果

    Returns:
        Tuple: (功率图, SOC图)
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        time_data = result.get_time_array()
        soc_data = result.get_soc_array()
        power_data = result.get_power_array()
        load_data = result.get_load_array()
        grid_data = result.get_grid_power_array()
        price_data = result.get_price_array()

        # 功率曲线图
        power_fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=("功率曲线", "电价曲线")
        )

        # 负荷曲线
        power_fig.add_trace(
            go.Scatter(
                x=time_data, y=load_data,
                mode='lines', name='负荷功率',
                line=dict(color='#1f77b4', width=2)
            ),
            row=1, col=1
        )

        # 电网功率
        power_fig.add_trace(
            go.Scatter(
                x=time_data, y=grid_data,
                mode='lines', name='电网功率',
                line=dict(color='#ff7f0e', width=2)
            ),
            row=1, col=1
        )

        # BESS功率（正放负充）
        charge_power = [-p if p < 0 else 0 for p in power_data]
        discharge_power = [p if p > 0 else 0 for p in power_data]

        power_fig.add_trace(
            go.Bar(
                x=time_data, y=discharge_power,
                name='放电功率',
                marker_color='rgba(255, 99, 71, 0.7)'
            ),
            row=1, col=1
        )

        power_fig.add_trace(
            go.Bar(
                x=time_data, y=charge_power,
                name='充电功率',
                marker_color='rgba(50, 205, 50, 0.7)'
            ),
            row=1, col=1
        )

        # 电价曲线
        power_fig.add_trace(
            go.Scatter(
                x=time_data, y=price_data,
                mode='lines', name='电价',
                line=dict(color='purple', shape='hv'),
                fill='tozeroy',
                fillcolor='rgba(128, 0, 128, 0.2)'
            ),
            row=2, col=1
        )

        power_fig.update_layout(
            title="储能系统运行曲线",
            height=500,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            hovermode='x unified'
        )
        power_fig.update_xaxes(title_text="时间 (小时)", row=2, col=1)
        power_fig.update_yaxes(title_text="功率 (kW)", row=1, col=1)
        power_fig.update_yaxes(title_text="电价 (元/kWh)", row=2, col=1)

        # SOC曲线图
        soc_fig = go.Figure()

        soc_fig.add_trace(
            go.Scatter(
                x=time_data, y=soc_data,
                mode='lines', name='SOC',
                line=dict(color='#2ca02c', width=3),
                fill='tozeroy',
                fillcolor='rgba(44, 160, 44, 0.2)'
            )
        )

        # 添加SOC上下限参考线
        bess_params = result.bess_params
        soc_fig.add_hline(
            y=bess_params.soc_max, line_dash="dash",
            line_color="red",
            annotation_text=f"SOC上限: {bess_params.soc_max}%"
        )
        soc_fig.add_hline(
            y=bess_params.soc_min, line_dash="dash",
            line_color="orange",
            annotation_text=f"SOC下限: {bess_params.soc_min}%"
        )

        soc_fig.update_layout(
            title="SOC变化曲线",
            xaxis_title="时间 (小时)",
            yaxis_title="SOC (%)",
            yaxis=dict(range=[0, 100]),
            height=350,
            hovermode='x unified'
        )

        return power_fig, soc_fig

    except ImportError:
        # 使用matplotlib作为后备
        import matplotlib.pyplot as plt

        time_data = result.get_time_array()
        soc_data = result.get_soc_array()
        power_data = result.get_power_array()
        load_data = result.get_load_array()

        # 功率图
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        ax1.plot(time_data, load_data, label='负荷', color='blue')
        ax1.bar(time_data, power_data, label='BESS功率', alpha=0.7, color='green')
        ax1.set_xlabel('时间 (小时)')
        ax1.set_ylabel('功率 (kW)')
        ax1.set_title('功率曲线')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        plt.tight_layout()

        # SOC图
        fig2, ax2 = plt.subplots(figsize=(10, 3))
        ax2.plot(time_data, soc_data, label='SOC', color='green', linewidth=2)
        ax2.fill_between(time_data, soc_data, alpha=0.3)
        ax2.axhline(y=result.bess_params.soc_max, color='r', linestyle='--', label='SOC上限')
        ax2.axhline(y=result.bess_params.soc_min, color='orange', linestyle='--', label='SOC下限')
        ax2.set_xlabel('时间 (小时)')
        ax2.set_ylabel('SOC (%)')
        ax2.set_title('SOC变化曲线')
        ax2.set_ylim(0, 100)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        plt.tight_layout()

        return fig1, fig2


def format_statistics_table(result: SimulationResult) -> Tuple[List, List]:
    """格式化统计表格

    Args:
        result: 仿真结果

    Returns:
        Tuple[List, List]: (经济统计数据, 运行统计数据)
    """
    # 经济统计
    economic_data = [
        ["充电成本", f"{result.total_charge_cost:.2f}", "元"],
        ["放电收益", f"{result.total_discharge_revenue:.2f}", "元"],
        ["套利利润", f"{result.arbitrage_profit:.2f}", "元"],
        ["基准电费", f"{result.baseline_cost:.2f}", "元"],
        ["节约电费", f"{result.cost_saving:.2f}", "元"],
    ]

    # 运行统计
    operation_data = [
        ["总充电量", f"{result.total_charge_kwh:.2f}", "kWh"],
        ["总放电量", f"{result.total_discharge_kwh:.2f}", "kWh"],
        ["系统效率", f"{result.system_efficiency:.1f}", "%"],
        ["等效循环", f"{result.equivalent_cycles:.3f}", "次"],
        ["容量利用率", f"{result.capacity_utilization:.1f}", "%"],
        ["最低SOC", f"{result.soc_min_actual:.1f}", "%"],
        ["最高SOC", f"{result.soc_max_actual:.1f}", "%"],
        ["最终SOC", f"{result.soc_final:.1f}", "%"],
    ]

    return economic_data, operation_data


def format_annual_table(annual_data: Dict[str, float]) -> List:
    """格式化年度预测表格

    Args:
        annual_data: 年度预测数据

    Returns:
        List: 表格数据
    """
    payback_text = (
        f"{annual_data['static_payback']:.1f}"
        if annual_data['static_payback'] < 100
        else "无法回收"
    )

    return [
        ["日套利利润", f"{annual_data['daily_profit']:.2f}", "元"],
        ["年套利收益", f"{annual_data['annual_revenue'] / 10000:.2f}", "万元"],
        ["年运维成本", f"{annual_data['annual_opex'] / 10000:.2f}", "万元"],
        ["年净收益", f"{annual_data['net_annual_revenue'] / 10000:.2f}", "万元"],
        ["初始投资", f"{annual_data['initial_investment'] / 10000:.2f}", "万元"],
        ["静态回收期", payback_text, "年"],
        ["年等效循环", f"{annual_data['annual_cycles']:.1f}", "次"],
        ["预计寿命", f"{annual_data['expected_life_years']:.1f}", "年"],
    ]


# =============================================================================
# Gradio UI组件
# =============================================================================
def create_simulation_tab():
    """创建仿真结果标签页

    Returns:
        Tuple[gr.Tab, Dict]: (标签页, 组件字典)
    """
    with gr.Tab("仿真计算") as tab:

        gr.Markdown("### 仿真计算")
        gr.Markdown("执行储能系统运行仿真，查看运行曲线和经济统计。")

        # 仿真设置
        with gr.Group():
            gr.Markdown("#### 仿真设置")

            with gr.Row():
                duration_dropdown = gr.Dropdown(
                    label="仿真周期",
                    choices=[
                        ("24小时", 24),
                        ("48小时", 48),
                        ("168小时(一周)", 168),
                    ],
                    value=24,
                    info=SIMULATION_TEACHING_META["duration_hours"]["help_text"]
                )
                timestep_dropdown = gr.Dropdown(
                    label="时间步长",
                    choices=[
                        ("5分钟", 5),
                        ("15分钟", 15),
                        ("30分钟", 30),
                        ("60分钟", 60),
                    ],
                    value=15,
                    info=SIMULATION_TEACHING_META["timestep_minutes"]["help_text"]
                )
                load_profile_dropdown = gr.Dropdown(
                    label="负荷曲线",
                    choices=[
                        ("典型工商业", "INDUSTRIAL"),
                        ("典型居民", "RESIDENTIAL"),
                        ("典型商业", "COMMERCIAL"),
                        ("自定义上传", "CUSTOM"),
                    ],
                    value="INDUSTRIAL",
                    info=SIMULATION_TEACHING_META["load_profile_type"]["help_text"]
                )

            with gr.Row():
                load_file_upload = gr.File(
                    label="上传负荷数据 (CSV)",
                    file_types=[".csv"],
                    visible=False
                )
                load_scale = gr.Slider(
                    label="负荷缩放系数",
                    minimum=0.1,
                    maximum=10.0,
                    value=1.0,
                    step=0.1,
                    info="调整负荷曲线的整体幅度"
                )

            with gr.Row():
                run_btn = gr.Button("开始仿真", variant="primary", scale=2)
                status_text = gr.Textbox(
                    label="状态",
                    value="就绪",
                    interactive=False,
                    scale=1
                )

        # 结果展示
        with gr.Row():
            power_plot = gr.Plot(label="功率曲线")

        with gr.Row():
            soc_plot = gr.Plot(label="SOC变化曲线")

        with gr.Row():
            # 经济统计
            with gr.Column(scale=1):
                gr.Markdown("#### 经济统计")
                economic_stats = gr.Dataframe(
                    headers=["指标", "数值", "单位"],
                    label="",
                    interactive=False,
                    row_count=5
                )

            # 运行统计
            with gr.Column(scale=1):
                gr.Markdown("#### 运行统计")
                operation_stats = gr.Dataframe(
                    headers=["指标", "数值", "单位"],
                    label="",
                    interactive=False,
                    row_count=8
                )

        # 年度预测
        with gr.Accordion("年度经济预测", open=False):
            annual_stats = gr.Dataframe(
                headers=["指标", "数值", "单位"],
                label="",
                interactive=False,
                row_count=8
            )

        # 导出按钮
        with gr.Row():
            export_data_btn = gr.Button("导出数据 (CSV)")
            export_report_btn = gr.Button("导出报告 (待实现)", interactive=False)

        download_file = gr.File(label="下载", visible=False)

    # 返回组件字典
    components = {
        "duration": duration_dropdown,
        "timestep": timestep_dropdown,
        "load_profile": load_profile_dropdown,
        "load_file": load_file_upload,
        "load_scale": load_scale,
        "run_btn": run_btn,
        "status_text": status_text,
        "power_plot": power_plot,
        "soc_plot": soc_plot,
        "economic_stats": economic_stats,
        "operation_stats": operation_stats,
        "annual_stats": annual_stats,
        "export_data_btn": export_data_btn,
        "export_report_btn": export_report_btn,
        "download_file": download_file,
    }

    return tab, components


def setup_simulation_events(
    components: Dict[str, Any],
    get_bess_params_fn: Callable,
    get_economic_params_fn: Callable,
    get_control_params_fn: Callable
):
    """设置仿真事件绑定

    Args:
        components: 组件字典
        get_bess_params_fn: 获取BESS参数的函数
        get_economic_params_fn: 获取经济参数的函数
        get_control_params_fn: 获取控制参数的函数
    """

    # 存储最近一次仿真结果
    simulation_state = {"result": None}

    def on_load_profile_change(profile_type):
        """负荷类型变化"""
        visible = (profile_type == "CUSTOM")
        return gr.update(visible=visible)

    def on_run_simulation(duration, timestep, load_profile, load_file, load_scale):
        """执行仿真"""
        try:
            # 获取参数
            bess_params = get_bess_params_fn()
            economic_params = get_economic_params_fn()
            control_params = get_control_params_fn()

            # 解析负荷类型
            load_type = LoadProfileType.INDUSTRIAL
            for lt in LoadProfileType:
                if lt.name == load_profile:
                    load_type = lt
                    break

            # 加载自定义负荷
            custom_load = None
            if load_type == LoadProfileType.CUSTOM and load_file is not None:
                custom_load, msg = load_custom_profile(load_file.name)
                if custom_load is None:
                    return (
                        None, None,
                        [], [],
                        [],
                        f"负荷加载失败: {msg}"
                    )

            # 创建配置
            config = SimulationConfig(
                duration_hours=int(duration),
                timestep_minutes=int(timestep),
                load_profile_type=load_type,
                load_data=custom_load,
                load_scale_factor=load_scale
            )

            # 执行仿真
            result = run_simulation(
                bess_params,
                economic_params,
                control_params,
                config
            )

            # 存储结果
            simulation_state["result"] = result

            # 绘制图表
            power_fig, soc_fig = plot_simulation_results(result)

            # 格式化统计表格
            economic_data, operation_data = format_statistics_table(result)

            # 年度预测
            annual_data = calculate_annual_projection(
                result, bess_params, economic_params
            )
            annual_table = format_annual_table(annual_data)

            return (
                power_fig, soc_fig,
                economic_data, operation_data,
                annual_table,
                f"仿真完成 - {config.timesteps}个时间步"
            )

        except Exception as e:
            import traceback
            return (
                None, None,
                [], [],
                [],
                f"仿真失败: {str(e)}\n{traceback.format_exc()}"
            )

    def on_export_data():
        """导出数据"""
        result = simulation_state.get("result")
        if result is None:
            return gr.update(visible=False)

        try:
            import tempfile
            import os

            # 创建临时文件
            fd, filepath = tempfile.mkstemp(suffix=".csv")
            os.close(fd)

            # 导出数据
            df = result.to_dataframe()
            df.to_csv(filepath, index=False, encoding='utf-8-sig')

            return gr.update(value=filepath, visible=True)

        except Exception as e:
            return gr.update(visible=False)

    # 绑定负荷类型变化
    components["load_profile"].change(
        fn=on_load_profile_change,
        inputs=[components["load_profile"]],
        outputs=[components["load_file"]]
    )

    # 绑定仿真按钮
    components["run_btn"].click(
        fn=on_run_simulation,
        inputs=[
            components["duration"],
            components["timestep"],
            components["load_profile"],
            components["load_file"],
            components["load_scale"],
        ],
        outputs=[
            components["power_plot"],
            components["soc_plot"],
            components["economic_stats"],
            components["operation_stats"],
            components["annual_stats"],
            components["status_text"],
        ]
    )

    # 绑定导出按钮
    components["export_data_btn"].click(
        fn=on_export_data,
        inputs=[],
        outputs=[components["download_file"]]
    )
