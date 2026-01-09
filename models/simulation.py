# -*- coding: utf-8 -*-
"""仿真计算数据模型

对应技术设计文档：04_仿真计算模块技术设计.md
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


# =============================================================================
# 负荷曲线类型枚举
# =============================================================================
class LoadProfileType(Enum):
    """负荷曲线类型

    对应设计文档：04文档 2.1节
    """
    INDUSTRIAL = "典型工商业"
    RESIDENTIAL = "典型居民"
    COMMERCIAL = "典型商业"
    CUSTOM = "自定义"
    # 扩展预留
    EXT_PROFILE_1 = "_扩展曲线1"
    EXT_PROFILE_2 = "_扩展曲线2"


# =============================================================================
# 仿真配置数据类
# =============================================================================
@dataclass
class SimulationConfig:
    """仿真配置

    对应设计文档：04文档 2.1节
    """

    # === 时间设置 ===
    duration_hours: int = 24                # 仿真时长（小时）
    timestep_minutes: int = 15              # 时间步长（分钟）

    # === 负荷设置 ===
    load_profile_type: LoadProfileType = LoadProfileType.INDUSTRIAL
    load_data: Optional[List[float]] = None     # 自定义负荷数据
    load_scale_factor: float = 1.0              # 负荷缩放系数

    # === 仿真选项 ===
    consider_degradation: bool = False          # 是否考虑容量衰减
    consider_temperature: bool = False          # 是否考虑温度影响
    random_seed: Optional[int] = None           # 随机种子（可重复性）

    # 扩展预留
    ext_config_1: Optional[Any] = None
    ext_config_2: Optional[Any] = None

    @property
    def timesteps(self) -> int:
        """计算总时间步数"""
        return int(self.duration_hours * 60 / self.timestep_minutes)

    @property
    def timestep_hours(self) -> float:
        """时间步长（小时）"""
        return self.timestep_minutes / 60

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'duration_hours': self.duration_hours,
            'timestep_minutes': self.timestep_minutes,
            'load_profile_type': self.load_profile_type.value if isinstance(
                self.load_profile_type, LoadProfileType
            ) else self.load_profile_type,
            'load_scale_factor': self.load_scale_factor,
            'consider_degradation': self.consider_degradation,
            'consider_temperature': self.consider_temperature,
            'timesteps': self.timesteps,
            'timestep_hours': self.timestep_hours,
        }


# =============================================================================
# BESS运行状态数据类
# =============================================================================
@dataclass
class BESSState:
    """BESS运行状态

    对应设计文档：04文档 2.2节
    """

    soc: float                              # 当前SOC (%)
    power: float                            # 当前功率 (kW)，正放负充
    energy_charged: float                   # 累计充电量 (kWh)
    energy_discharged: float                # 累计放电量 (kWh)
    cycles: float                           # 等效循环次数
    temperature: float = 25.0               # 电池温度 (℃)

    # 扩展预留
    ext_state_1: Optional[Any] = None
    ext_state_2: Optional[Any] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'soc': self.soc,
            'power': self.power,
            'energy_charged': self.energy_charged,
            'energy_discharged': self.energy_discharged,
            'cycles': self.cycles,
            'temperature': self.temperature,
        }


# =============================================================================
# 单时间步仿真结果数据类
# =============================================================================
@dataclass
class TimeStepResult:
    """单时间步仿真结果

    对应设计文档：04文档 2.2节
    """

    timestamp: int                          # 时间步索引
    time_hours: float                       # 时间（小时）

    # BESS状态
    soc: float                              # SOC (%)
    power_bess: float                       # BESS功率 (kW)

    # 能量
    energy_charge: float                    # 本时段充电量 (kWh)
    energy_discharge: float                 # 本时段放电量 (kWh)

    # 负荷与电网
    load_power: float                       # 负荷功率 (kW)
    grid_power: float                       # 电网功率 (kW)，正买负卖
    net_load: float                         # 净负荷 (kW)

    # 经济
    electricity_price: float                # 当时电价 (元/kWh)
    cost: float                             # 本时段电费 (元)

    # 状态
    action: str                             # 动作描述

    # 扩展预留
    ext_result_1: Optional[Any] = None
    ext_result_2: Optional[Any] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'timestamp': self.timestamp,
            'time_hours': self.time_hours,
            'soc': self.soc,
            'power_bess': self.power_bess,
            'energy_charge': self.energy_charge,
            'energy_discharge': self.energy_discharge,
            'load_power': self.load_power,
            'grid_power': self.grid_power,
            'net_load': self.net_load,
            'electricity_price': self.electricity_price,
            'cost': self.cost,
            'action': self.action,
        }


# =============================================================================
# 仿真结果汇总数据类
# =============================================================================
@dataclass
class SimulationResult:
    """仿真结果汇总

    对应设计文档：04文档 2.3节
    """

    # === 配置信息 ===
    config: SimulationConfig
    bess_params: Any                        # BESSParams
    economic_params: Any                    # EconomicParams
    control_params: Any                     # ControlParams

    # === 时序数据 ===
    timestep_results: List[TimeStepResult] = field(default_factory=list)

    # === 运行统计 ===
    total_charge_kwh: float = 0.0           # 总充电量
    total_discharge_kwh: float = 0.0        # 总放电量
    system_efficiency: float = 0.0          # 系统效率 (%)
    equivalent_cycles: float = 0.0          # 等效循环次数
    capacity_utilization: float = 0.0       # 容量利用率 (%)
    power_utilization: float = 0.0          # 功率利用率 (%)

    # === 经济统计 ===
    total_charge_cost: float = 0.0          # 总充电成本 (元)
    total_discharge_revenue: float = 0.0    # 总放电收益 (元)
    arbitrage_profit: float = 0.0           # 套利利润 (元)
    baseline_cost: float = 0.0              # 基准电费（无储能）(元)
    cost_saving: float = 0.0                # 节约电费 (元)

    # === SOC统计 ===
    soc_min_actual: float = 0.0             # 实际最低SOC
    soc_max_actual: float = 0.0             # 实际最高SOC
    soc_final: float = 0.0                  # 最终SOC

    # 扩展统计预留
    ext_stats: Dict[str, Any] = field(default_factory=dict)

    # === 数据提取方法 ===
    def get_time_array(self) -> List[float]:
        """获取时间序列（小时）"""
        return [r.time_hours for r in self.timestep_results]

    def get_soc_array(self) -> List[float]:
        """获取SOC序列"""
        return [r.soc for r in self.timestep_results]

    def get_power_array(self) -> List[float]:
        """获取BESS功率序列"""
        return [r.power_bess for r in self.timestep_results]

    def get_load_array(self) -> List[float]:
        """获取负荷序列"""
        return [r.load_power for r in self.timestep_results]

    def get_grid_power_array(self) -> List[float]:
        """获取电网功率序列"""
        return [r.grid_power for r in self.timestep_results]

    def get_price_array(self) -> List[float]:
        """获取电价序列"""
        return [r.electricity_price for r in self.timestep_results]

    def get_charge_array(self) -> List[float]:
        """获取充电量序列"""
        return [r.energy_charge for r in self.timestep_results]

    def get_discharge_array(self) -> List[float]:
        """获取放电量序列"""
        return [r.energy_discharge for r in self.timestep_results]

    def get_cost_array(self) -> List[float]:
        """获取电费序列"""
        return [r.cost for r in self.timestep_results]

    def get_action_array(self) -> List[str]:
        """获取动作描述序列"""
        return [r.action for r in self.timestep_results]

    def to_dataframe(self):
        """转换为Pandas DataFrame"""
        try:
            import pandas as pd
            data = [r.to_dict() for r in self.timestep_results]
            return pd.DataFrame(data)
        except ImportError:
            raise ImportError("需要安装pandas库才能使用此功能")

    def get_summary_dict(self) -> Dict[str, Any]:
        """获取统计摘要字典"""
        return {
            # 运行统计
            'total_charge_kwh': self.total_charge_kwh,
            'total_discharge_kwh': self.total_discharge_kwh,
            'system_efficiency': self.system_efficiency,
            'equivalent_cycles': self.equivalent_cycles,
            'capacity_utilization': self.capacity_utilization,
            'power_utilization': self.power_utilization,
            # 经济统计
            'total_charge_cost': self.total_charge_cost,
            'total_discharge_revenue': self.total_discharge_revenue,
            'arbitrage_profit': self.arbitrage_profit,
            'baseline_cost': self.baseline_cost,
            'cost_saving': self.cost_saving,
            # SOC统计
            'soc_min_actual': self.soc_min_actual,
            'soc_max_actual': self.soc_max_actual,
            'soc_final': self.soc_final,
        }


# =============================================================================
# 仿真教学元数据
# =============================================================================
SIMULATION_TEACHING_META: Dict[str, Dict[str, Any]] = {
    # 仿真配置参数
    "duration_hours": {
        "help_text": "仿真模拟的总时长，通常为24小时（一个完整运营日）或更长",
        "impact_desc": "时长↑→数据量↑，可观察更完整的运行周期",
        "typical_range": "24小时（日）、168小时（周）",
        "learning_points": ["4.1"]
    },
    "timestep_minutes": {
        "help_text": "仿真计算的时间间隔，影响结果精度和计算量",
        "impact_desc": "步长↓→精度↑，但计算量↑",
        "typical_range": "5-60分钟，常用15分钟",
        "learning_points": ["4.1"]
    },
    "load_profile_type": {
        "help_text": "负荷曲线类型，不同用户类型有不同的用电规律",
        "impact_desc": "负荷曲线形状直接影响储能调度策略的效果",
        "typical_range": "工商业、居民、商业",
        "learning_points": ["2.2", "3.1"]
    },

    # 仿真过程概念
    "soc_calculation": {
        "help_text": "SOC计算基于安时积分法：充电时SOC增加，放电时SOC减少",
        "formula": "SOC_new = SOC_old + (充电量×效率 - 放电量/效率) / 容量 × 100%",
        "learning_points": ["1.2", "4.2"],
        "debug_hint": "观察SOC变化是否符合能量守恒"
    },
    "power_protection": {
        "help_text": "保护逻辑会在SOC接近边界时自动限制功率或停止运行",
        "trigger_conditions": [
            "SOC ≥ 过充保护阈值 → 停止充电",
            "SOC ≤ 过放保护阈值 → 停止放电"
        ],
        "learning_points": ["4.2", "5.3"],
        "debug_hint": "观察保护逻辑何时触发，理解其对调度的影响"
    },
    "efficiency_loss": {
        "help_text": "充放电效率导致的能量损失，系统效率 = 放电量/充电量",
        "formula": "往返效率 ≈ 充电效率 × 放电效率",
        "typical_value": "锂电池往返效率约90%",
        "learning_points": ["1.3", "2.3"],
        "debug_hint": "比较充放电量差异，理解效率损失"
    },
    "grid_power": {
        "help_text": "电网功率 = 负荷功率 - 储能放电功率（正值买电，负值卖电）",
        "formula": "P_grid = P_load - P_bess",
        "learning_points": ["2.2", "3.1"],
        "debug_hint": "观察储能如何改变电网功率曲线"
    },
    "arbitrage_profit": {
        "help_text": "套利利润 = 放电收益 - 充电成本",
        "formula": "利润 = Σ(放电电量×放电时电价) - Σ(充电电量×充电时电价)",
        "key_factors": ["峰谷价差", "充放电电量", "效率损失"],
        "learning_points": ["2.3", "3.1"],
        "debug_hint": "对比峰谷时段的充放电行为和收益"
    },

    # 调试模式
    "debug_mode": {
        "help_text": "单步调试模式允许逐步执行仿真，观察每个时间步的计算过程",
        "features": ["暂停/继续执行", "查看中间变量", "修改参数热重载"],
        "learning_points": ["4.2"],
        "usage_hint": "初学者建议使用调试模式，深入理解仿真计算过程"
    },

    # 负荷曲线类型说明
    "load_profiles": {
        "INDUSTRIAL": {
            "name": "典型工商业",
            "description": "白天用电高峰，夜间低谷，适合峰谷套利策略",
            "characteristics": [
                "8:00-18:00 高负荷",
                "12:00-14:00 午间小幅下降",
                "22:00-8:00 低谷"
            ],
            "suitable_strategies": ["峰谷套利", "需量管理"]
        },
        "RESIDENTIAL": {
            "name": "典型居民",
            "description": "早晚双高峰特征，中午负荷较低",
            "characteristics": [
                "7:00-9:00 早高峰",
                "18:00-22:00 晚高峰",
                "其他时段较低"
            ],
            "suitable_strategies": ["峰谷套利"]
        },
        "COMMERCIAL": {
            "name": "典型商业",
            "description": "营业时间负荷较高，夜间低",
            "characteristics": [
                "9:00-21:00 营业时间高负荷",
                "12:00-14:00 午间小高峰",
                "18:00-21:00 傍晚高峰"
            ],
            "suitable_strategies": ["峰谷套利", "负荷跟踪"]
        }
    }
}
