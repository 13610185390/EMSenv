# -*- coding: utf-8 -*-
"""仿真核心功能测试 - 不依赖Gradio"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.default_params import (
    create_default_bess_params,
    create_default_economic_params,
    create_default_control_params
)
from models.simulation import SimulationConfig, LoadProfileType, SimulationResult
from models.bess import BESSParams
from models.economic import EconomicParams
from models.control import ControlParams, DispatchSchedule, SchedulePoint, DispatchMode


def run_simple_simulation(
    bess_params: BESSParams,
    economic_params: EconomicParams,
    control_params: ControlParams,
    config: SimulationConfig
) -> SimulationResult:
    """简化的仿真引擎 - 不依赖Gradio"""
    from models.economic import PricePeriodType
    from datetime import time as dt_time

    result = SimulationResult(
        config=config,
        bess_params=bess_params,
        economic_params=economic_params,
        control_params=control_params
    )

    timesteps = config.timesteps
    timestep_hours = config.timestep_hours

    # 生成工业负荷曲线
    load_curve = []
    import math
    for i in range(timesteps):
        hour = i * timestep_hours
        if 0 <= hour < 8:
            load = 40 + 10 * math.sin(hour / 8 * math.pi)
        elif 8 <= hour < 12:
            load = 50 + 50 * (hour - 8) / 4
        elif 12 <= hour < 14:
            load = 90 + 10 * math.sin((hour - 12) * math.pi / 2)
        elif 14 <= hour < 18:
            load = 100 - 10 * (hour - 14) / 4
        elif 18 <= hour < 22:
            load = 90 - 40 * (hour - 18) / 4
        else:
            load = 50 - 10 * (hour - 22) / 2 if hour < 24 else 40
        load_curve.append(max(30, load) * config.load_scale_factor)

    # 获取电价曲线
    price_params = economic_params.price_params
    price_curve = price_params.get_price_curve(config.timestep_minutes)
    while len(price_curve) < timesteps:
        price_curve.extend(price_curve[:min(len(price_curve), timesteps - len(price_curve))])

    # 仿真状态
    current_soc = bess_params.soc_init
    total_charge_kwh = 0.0
    total_discharge_kwh = 0.0
    charge_cost = 0.0
    discharge_revenue = 0.0

    from models.simulation import TimeStepResult, BESSState

    for i in range(timesteps):
        hour = int((i * config.timestep_minutes) // 60)
        minute = (i * config.timestep_minutes) % 60
        current_time = dt_time(hour % 24, minute)

        period_type = price_params.get_period_type_at(current_time)
        price = price_curve[i] if i < len(price_curve) else price_params.price_flat
        load = load_curve[i]

        power = 0.0
        action = "待机"
        energy_charge = 0.0
        energy_discharge = 0.0

        # 峰谷套利策略
        if period_type == PricePeriodType.VALLEY:
            if current_soc < bess_params.soc_max:
                power = -bess_params.power_charge_max
                action = "谷时充电"
                # 充电：输入能量，存储能量=输入*效率
                energy_charge = abs(power) * timestep_hours
                eta_charge = bess_params.efficiency_charge / 100
                soc_change = energy_charge * eta_charge / bess_params.capacity * 100
                current_soc = min(bess_params.soc_max, current_soc + soc_change)
                charge_cost += energy_charge * price
                total_charge_kwh += energy_charge

        elif period_type in [PricePeriodType.PEAK, PricePeriodType.CRITICAL]:
            if current_soc > bess_params.soc_min:
                power = bess_params.power_discharge_max
                action = "峰时放电"
                # 放电：输出能量，消耗电池能量=输出/效率
                energy_discharge = power * timestep_hours
                eta_discharge = bess_params.efficiency_discharge / 100
                soc_change = energy_discharge / eta_discharge / bess_params.capacity * 100
                current_soc = max(bess_params.soc_min, current_soc - soc_change)
                discharge_revenue += energy_discharge * price
                total_discharge_kwh += energy_discharge

        grid_power = load - power
        cost = grid_power * timestep_hours * price if grid_power > 0 else 0

        step_result = TimeStepResult(
            timestamp=i,
            time_hours=i * timestep_hours,
            soc=current_soc,
            power_bess=power,
            energy_charge=energy_charge,
            energy_discharge=energy_discharge,
            load_power=load,
            grid_power=grid_power,
            net_load=load - power,
            electricity_price=price,
            cost=cost,
            action=action
        )
        result.timestep_results.append(step_result)

    # 计算统计
    result.total_charge_kwh = total_charge_kwh
    result.total_discharge_kwh = total_discharge_kwh
    result.total_charge_cost = charge_cost
    result.total_discharge_revenue = discharge_revenue
    result.arbitrage_profit = discharge_revenue - charge_cost

    if total_charge_kwh > 0:
        result.system_efficiency = total_discharge_kwh / total_charge_kwh * 100

    throughput = (total_charge_kwh + total_discharge_kwh) / 2
    result.equivalent_cycles = throughput / bess_params.capacity

    # 基准电费
    result.baseline_cost = sum(
        load_curve[i] * timestep_hours * price_curve[i]
        for i in range(min(len(load_curve), len(price_curve), timesteps))
    )

    actual_cost = sum(r.cost for r in result.timestep_results)
    result.cost_saving = result.baseline_cost - actual_cost

    # SOC统计
    soc_values = [r.soc for r in result.timestep_results]
    result.soc_min_actual = min(soc_values)
    result.soc_max_actual = max(soc_values)
    result.soc_final = soc_values[-1]

    return result


def test_simulation():
    """测试仿真引擎"""
    print("=" * 50)
    print("储能仿真核心功能测试")
    print("=" * 50)

    # 创建默认参数
    bess_params = create_default_bess_params()
    economic_params = create_default_economic_params()
    control_params = create_default_control_params()

    print(f"\nBESS参数:")
    print(f"  容量: {bess_params.capacity} kWh")
    print(f"  额定功率: {bess_params.power_rated} kW")
    print(f"  SOC范围: {bess_params.soc_min}% - {bess_params.soc_max}%")

    print(f"\n电价参数:")
    print(f"  谷时: {economic_params.price_params.price_valley} 元/kWh")
    print(f"  平时: {economic_params.price_params.price_flat} 元/kWh")
    print(f"  峰时: {economic_params.price_params.price_peak} 元/kWh")

    # 创建仿真配置
    config = SimulationConfig(
        duration_hours=24,
        timestep_minutes=15,
        load_profile_type=LoadProfileType.INDUSTRIAL,
        load_scale_factor=1.0
    )

    print(f"\n仿真配置:")
    print(f"  时长: {config.duration_hours} 小时")
    print(f"  步长: {config.timestep_minutes} 分钟")
    print(f"  总步数: {config.timesteps}")

    # 执行仿真
    print("\n执行仿真...")
    result = run_simple_simulation(bess_params, economic_params, control_params, config)

    print(f"\n仿真结果:")
    print(f"  时间步数: {len(result.timestep_results)}")
    print(f"  总充电量: {result.total_charge_kwh:.2f} kWh")
    print(f"  总放电量: {result.total_discharge_kwh:.2f} kWh")
    print(f"  系统效率: {result.system_efficiency:.1f}%")
    print(f"  等效循环: {result.equivalent_cycles:.3f} 次")

    print(f"\n经济指标:")
    print(f"  充电成本: {result.total_charge_cost:.2f} 元")
    print(f"  放电收益: {result.total_discharge_revenue:.2f} 元")
    print(f"  套利利润: {result.arbitrage_profit:.2f} 元")
    print(f"  基准电费: {result.baseline_cost:.2f} 元")
    print(f"  节约电费: {result.cost_saving:.2f} 元")

    print(f"\nSOC统计:")
    print(f"  最低SOC: {result.soc_min_actual:.1f}%")
    print(f"  最高SOC: {result.soc_max_actual:.1f}%")
    print(f"  最终SOC: {result.soc_final:.1f}%")

    # 验证
    assert len(result.timestep_results) == config.timesteps, "时间步数不匹配"
    assert result.total_charge_kwh > 0, "充电量应大于0"
    assert result.total_discharge_kwh > 0, "放电量应大于0"
    assert result.arbitrage_profit > 0, "套利应有利润"
    assert 0 <= result.soc_min_actual <= 100, "SOC应在0-100%之间"
    assert 0 <= result.soc_max_actual <= 100, "SOC应在0-100%之间"

    print("\n" + "=" * 50)
    print("[OK] All tests passed!")
    print("=" * 50)

    return result


if __name__ == "__main__":
    test_simulation()
