# -*- coding: utf-8 -*-
"""默认参数配置

对应设计文档：开发规划文档 1.6节
定义各模块的默认参数值
"""

from .constants import *

# =============================================================================
# BESS默认参数
# =============================================================================
DEFAULT_BESS_PARAMS = {
    # 基础参数
    "battery_type": "LFP",              # 磷酸铁锂
    "capacity": CAPACITY_DEFAULT,        # kWh
    "power_rated": POWER_DEFAULT_RATED,  # kW

    # 充放电功率（可独立配置）
    "power_charge_max": None,            # None表示等于power_rated
    "power_discharge_max": None,         # None表示等于power_rated

    # SOC限制
    "soc_init": SOC_DEFAULT_INIT,        # %
    "soc_min": SOC_DEFAULT_MIN,          # %
    "soc_max": SOC_DEFAULT_MAX,          # %

    # 效率
    "efficiency_charge": EFFICIENCY_DEFAULT_CHARGE,      # %
    "efficiency_discharge": EFFICIENCY_DEFAULT_DISCHARGE, # %

    # 寿命
    "cycle_life": CYCLE_LIFE_DEFAULT,    # 次
    "calendar_life": CALENDAR_LIFE_DEFAULT,  # 年
    "degradation_rate": DEGRADATION_RATE_DEFAULT,  # %/年
}

# =============================================================================
# 经济默认参数
# =============================================================================
DEFAULT_ECONOMIC_PARAMS = {
    # 电价参数
    "price_valley": PRICE_DEFAULT_VALLEY,    # 元/kWh
    "price_flat": PRICE_DEFAULT_FLAT,        # 元/kWh
    "price_peak": PRICE_DEFAULT_PEAK,        # 元/kWh
    "price_critical": None,                   # 元/kWh (可选)
    "price_feed_in": 0.5,                     # 元/kWh 上网电价

    # 时段配置 (默认时段字符串)
    "periods": {
        "valley": ["00:00-08:00"],
        "flat": ["08:00-10:00", "12:00-18:00", "22:00-24:00"],
        "peak": ["10:00-12:00", "18:00-22:00"],
    },

    # 成本参数
    "cost_per_kwh": COST_PER_KWH_DEFAULT,    # 元/kWh
    "cost_per_kw": COST_PER_KW_DEFAULT,      # 元/kW
    "cost_install_ratio": 10.0,              # %
    "cost_om_ratio": 2.0,                    # %
    "cost_insurance_ratio": 0.5,             # %

    # 财务参数
    "discount_rate": DISCOUNT_RATE_DEFAULT,  # %
    "project_years": PROJECT_YEARS_DEFAULT,  # 年
    "residual_ratio": 5.0,                   # %
}

# =============================================================================
# 控制默认参数
# =============================================================================
DEFAULT_CONTROL_PARAMS = {
    # 调度模式
    "dispatch_mode": "ARBITRAGE",            # 峰谷套利

    # 充放电策略
    "charge_strategy": "VALLEY_CHARGE",      # 谷时充电
    "discharge_strategy": "PEAK_DISCHARGE",  # 峰时放电
    "power_control_mode": "CONSTANT_POWER",  # 定功率

    # 保护参数
    "protect_soc_high": SOC_PROTECT_HIGH,    # %
    "protect_soc_low": SOC_PROTECT_LOW,      # %
    "power_limit_factor": 1.0,               # 功率限制系数
    "protect_temp_high": TEMP_PROTECT_HIGH,  # ℃
    "protect_temp_low": TEMP_PROTECT_LOW,    # ℃

    # 响应参数
    "response_time": RESPONSE_TIME_DEFAULT,  # ms
    "ramp_rate": RAMP_RATE_DEFAULT,          # kW/s
}

# =============================================================================
# 仿真默认配置
# =============================================================================
DEFAULT_SIMULATION_CONFIG = {
    "duration_hours": SIMULATION_DURATION_DEFAULT,   # 小时
    "timestep_minutes": SIMULATION_TIMESTEP_DEFAULT, # 分钟
    "load_profile_type": "INDUSTRIAL",               # 工商业负荷
    "load_scale_factor": 1.0,                        # 负荷缩放系数
    "consider_degradation": False,                   # 不考虑衰减
    "consider_temperature": False,                   # 不考虑温度
}


def get_default_bess_params() -> dict:
    """获取BESS默认参数副本"""
    return DEFAULT_BESS_PARAMS.copy()


def get_default_economic_params() -> dict:
    """获取经济默认参数副本"""
    return DEFAULT_ECONOMIC_PARAMS.copy()


def get_default_control_params() -> dict:
    """获取控制默认参数副本"""
    return DEFAULT_CONTROL_PARAMS.copy()


def get_default_simulation_config() -> dict:
    """获取仿真默认配置副本"""
    return DEFAULT_SIMULATION_CONFIG.copy()


# =============================================================================
# 数据类实例创建函数
# =============================================================================
def create_default_bess_params():
    """创建默认BESS参数数据类实例

    Returns:
        BESSParams: BESS参数数据类实例
    """
    from models.bess import BESSParams, BatteryType
    return BESSParams(
        name="BESS_01",
        battery_type=BatteryType.LFP,
        capacity=DEFAULT_BESS_PARAMS["capacity"],
        power_rated=DEFAULT_BESS_PARAMS["power_rated"],
        soc_init=DEFAULT_BESS_PARAMS["soc_init"],
        soc_min=DEFAULT_BESS_PARAMS["soc_min"],
        soc_max=DEFAULT_BESS_PARAMS["soc_max"],
        efficiency_charge=DEFAULT_BESS_PARAMS["efficiency_charge"],
        efficiency_discharge=DEFAULT_BESS_PARAMS["efficiency_discharge"],
        cycle_life=DEFAULT_BESS_PARAMS["cycle_life"],
        calendar_life=DEFAULT_BESS_PARAMS["calendar_life"],
        degradation_rate=DEFAULT_BESS_PARAMS["degradation_rate"],
    )


def create_default_economic_params():
    """创建默认经济参数数据类实例

    Returns:
        EconomicParams: 经济参数数据类实例
    """
    from models.economic import (
        EconomicParams, ElectricityPriceParams,
        CostParams, FinancialParams
    )

    price_params = ElectricityPriceParams(
        price_valley=DEFAULT_ECONOMIC_PARAMS["price_valley"],
        price_flat=DEFAULT_ECONOMIC_PARAMS["price_flat"],
        price_peak=DEFAULT_ECONOMIC_PARAMS["price_peak"],
        price_critical=DEFAULT_ECONOMIC_PARAMS["price_critical"],
        price_feed_in=DEFAULT_ECONOMIC_PARAMS["price_feed_in"],
    )

    cost_params = CostParams(
        cost_per_kwh=DEFAULT_ECONOMIC_PARAMS["cost_per_kwh"],
        cost_per_kw=DEFAULT_ECONOMIC_PARAMS["cost_per_kw"],
        cost_install_ratio=DEFAULT_ECONOMIC_PARAMS["cost_install_ratio"],
        cost_om_ratio=DEFAULT_ECONOMIC_PARAMS["cost_om_ratio"],
        cost_insurance_ratio=DEFAULT_ECONOMIC_PARAMS["cost_insurance_ratio"],
    )

    financial_params = FinancialParams(
        discount_rate=DEFAULT_ECONOMIC_PARAMS["discount_rate"],
        project_years=DEFAULT_ECONOMIC_PARAMS["project_years"],
        residual_ratio=DEFAULT_ECONOMIC_PARAMS["residual_ratio"],
    )

    return EconomicParams(
        price_params=price_params,
        cost_params=cost_params,
        financial_params=financial_params,
    )


def create_default_control_params():
    """创建默认控制参数数据类实例

    Returns:
        ControlParams: 控制参数数据类实例
    """
    from models.control import (
        ControlParams, DispatchMode, ChargeStrategy, DischargeStrategy,
        PowerControlMode, ChargeDischargeStrategy, ProtectionParams, ResponseParams
    )

    strategy = ChargeDischargeStrategy(
        charge_strategy=ChargeStrategy.VALLEY_CHARGE,
        discharge_strategy=DischargeStrategy.PEAK_DISCHARGE,
        power_control_mode=PowerControlMode.CONSTANT_POWER,
    )

    protection = ProtectionParams(
        protect_soc_high=DEFAULT_CONTROL_PARAMS["protect_soc_high"],
        protect_soc_low=DEFAULT_CONTROL_PARAMS["protect_soc_low"],
        power_limit_factor=DEFAULT_CONTROL_PARAMS["power_limit_factor"],
        protect_temp_high=DEFAULT_CONTROL_PARAMS["protect_temp_high"],
        protect_temp_low=DEFAULT_CONTROL_PARAMS["protect_temp_low"],
    )

    response = ResponseParams(
        response_time=DEFAULT_CONTROL_PARAMS["response_time"],
        ramp_rate=DEFAULT_CONTROL_PARAMS["ramp_rate"],
    )

    return ControlParams(
        dispatch_mode=DispatchMode.ARBITRAGE,
        strategy=strategy,
        protection=protection,
        response=response,
    )


def create_default_simulation_config():
    """创建默认仿真配置数据类实例

    Returns:
        SimulationConfig: 仿真配置数据类实例
    """
    from models.simulation import SimulationConfig, LoadProfileType

    return SimulationConfig(
        duration_hours=DEFAULT_SIMULATION_CONFIG["duration_hours"],
        timestep_minutes=DEFAULT_SIMULATION_CONFIG["timestep_minutes"],
        load_profile_type=LoadProfileType.INDUSTRIAL,
        load_scale_factor=DEFAULT_SIMULATION_CONFIG["load_scale_factor"],
        consider_degradation=DEFAULT_SIMULATION_CONFIG["consider_degradation"],
        consider_temperature=DEFAULT_SIMULATION_CONFIG["consider_temperature"],
    )
