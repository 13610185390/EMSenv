# -*- coding: utf-8 -*-
"""控制策略数据模型

对应技术设计文档：03_控制策略模块技术设计.md
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from enum import Enum


# =============================================================================
# 调度模式枚举
# =============================================================================
class DispatchMode(Enum):
    """调度模式枚举

    对应设计文档：03文档 2.1节
    """
    ARBITRAGE = "峰谷套利"              # 谷充峰放
    LOAD_FOLLOW = "负荷跟踪"            # 削峰填谷
    # 扩展预留
    RE_SMOOTHING = "新能源消纳"         # 待实现
    DEMAND_MANAGEMENT = "需量管理"      # 待实现
    EXT_MODE_1 = "_扩展模式1"
    EXT_MODE_2 = "_扩展模式2"


class ChargeStrategy(Enum):
    """充电策略枚举"""
    VALLEY_CHARGE = "谷时充电"
    SOC_TRIGGER_LOW = "低于目标SOC充电"
    PRICE_TRIGGER_LOW = "低电价充电"
    # 扩展预留
    EXT_CHARGE_1 = "_扩展充电策略1"


class DischargeStrategy(Enum):
    """放电策略枚举"""
    PEAK_DISCHARGE = "峰时放电"
    SOC_TRIGGER_HIGH = "高于目标SOC放电"
    PRICE_TRIGGER_HIGH = "高电价放电"
    # 扩展预留
    EXT_DISCHARGE_1 = "_扩展放电策略1"


class PowerControlMode(Enum):
    """功率控制模式枚举"""
    CONSTANT_POWER = "定功率"
    VARIABLE_POWER = "变功率"
    OPTIMIZED = "优化控制"
    # 扩展预留
    EXT_CONTROL_1 = "_扩展控制模式1"


# =============================================================================
# 充放电策略数据类
# =============================================================================
@dataclass
class ChargeDischargeStrategy:
    """充放电策略参数

    对应设计文档：03文档 2.2节
    """

    charge_strategy: ChargeStrategy = ChargeStrategy.VALLEY_CHARGE
    discharge_strategy: DischargeStrategy = DischargeStrategy.PEAK_DISCHARGE
    power_control_mode: PowerControlMode = PowerControlMode.CONSTANT_POWER

    # 价格触发阈值（用于价格触发策略）
    price_charge_threshold: Optional[float] = None   # 低于此价格开始充电
    price_discharge_threshold: Optional[float] = None # 高于此价格开始放电

    # SOC触发阈值（用于SOC触发策略）
    soc_charge_trigger: Optional[float] = None       # SOC低于此值开始充电
    soc_discharge_trigger: Optional[float] = None    # SOC高于此值开始放电

    # 扩展预留
    ext_strategy_1: Optional[Any] = None


# =============================================================================
# 保护参数数据类
# =============================================================================
@dataclass
class ProtectionParams:
    """保护参数数据类

    对应设计文档：03文档 2.2节
    """

    protect_soc_high: float = 95.0      # %，过充保护阈值
    protect_soc_low: float = 5.0        # %，过放保护阈值
    power_limit_factor: float = 1.0     # 功率限制系数
    protect_temp_high: float = 45.0     # ℃，高温保护阈值
    protect_temp_low: float = 0.0       # ℃，低温保护阈值

    # 扩展预留
    ext_protect_1: Optional[Any] = None
    ext_protect_2: Optional[Any] = None


# =============================================================================
# 响应参数数据类
# =============================================================================
@dataclass
class ResponseParams:
    """响应参数数据类

    对应设计文档：03文档 2.2节
    """

    response_time: float = 100.0        # ms，响应时间
    ramp_rate: float = 10.0             # kW/s，爬坡速率

    # 扩展预留
    ext_response_1: Optional[Any] = None


# =============================================================================
# 控制参数汇总数据类
# =============================================================================
@dataclass
class ControlParams:
    """控制策略参数汇总

    对应设计文档：03文档 2.2节
    """

    dispatch_mode: DispatchMode = DispatchMode.ARBITRAGE
    strategy: ChargeDischargeStrategy = field(
        default_factory=ChargeDischargeStrategy
    )
    protection: ProtectionParams = field(default_factory=ProtectionParams)
    response: ResponseParams = field(default_factory=ResponseParams)

    # 扩展预留
    ext_params: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# 调度计划数据类
# =============================================================================
@dataclass
class SchedulePoint:
    """调度计划时间点

    对应设计文档：03文档 2.3节
    """
    timestamp: int                      # 时间索引
    power: float                        # 功率 (kW)，正值放电，负值充电
    action: str                         # 动作描述
    soc_expected: float                 # 预期SOC


@dataclass
class DispatchSchedule:
    """调度计划

    对应设计文档：03文档 2.3节
    """

    schedule: List[SchedulePoint] = field(default_factory=list)
    timestep_minutes: int = 15
    total_charge_kwh: float = 0.0
    total_discharge_kwh: float = 0.0

    def get_power_array(self) -> List[float]:
        """获取功率序列"""
        return [p.power for p in self.schedule]

    def get_charge_array(self) -> List[float]:
        """获取充电功率序列（正值）"""
        return [max(0, -p.power) for p in self.schedule]

    def get_discharge_array(self) -> List[float]:
        """获取放电功率序列（正值）"""
        return [max(0, p.power) for p in self.schedule]

    def get_action_array(self) -> List[str]:
        """获取动作描述序列"""
        return [p.action for p in self.schedule]


# =============================================================================
# 控制策略教学元数据
# =============================================================================
CONTROL_TEACHING_META: Dict[str, Dict[str, Any]] = {
    # 调度模式说明
    "dispatch_modes": {
        "ARBITRAGE": {
            "name": "峰谷套利",
            "description": "在低电价时段（谷时）充电，高电价时段（峰时）放电，赚取电价差收益",
            "suitable_scenes": ["工商业用户", "有明显峰谷价差的地区"],
            "key_factors": ["峰谷电价差", "可用容量", "充放电效率"],
            "learning_points": ["3.1", "2.3"],
            "example": "假设峰谷价差0.8元/kWh，100kWh电池日收益约60-70元"
        },
        "LOAD_FOLLOW": {
            "name": "负荷跟踪",
            "description": "根据负荷曲线削峰填谷，降低最大负荷，平滑用电曲线",
            "suitable_scenes": ["大型工业用户", "有需量电费的用户"],
            "key_factors": ["负荷曲线形状", "峰值需量", "储能功率"],
            "learning_points": ["3.2", "2.2"],
            "example": "通过削减100kW峰值需量，月可节省需量电费4000元"
        },
        "RE_SMOOTHING": {
            "name": "新能源消纳",
            "description": "配合光伏/风电出力，平滑新能源波动，提高自消纳比例",
            "suitable_scenes": ["光储一体化项目", "分布式光伏电站"],
            "key_factors": ["新能源出力曲线", "负荷匹配度", "上网电价"],
            "learning_points": ["3.3"],
            "example": "提高光伏自消纳率从50%到90%，减少弃光损失"
        },
        "DEMAND_MANAGEMENT": {
            "name": "需量管理",
            "description": "通过储能放电控制用电需量，降低需量电费",
            "suitable_scenes": ["大工业用户", "有高需量电费的用户"],
            "key_factors": ["合同需量", "实际最大负荷", "需量电价"],
            "learning_points": ["3.2"],
            "example": "将需量从500kW降至400kW，月节省需量电费4000元"
        }
    },

    # 保护参数说明
    "protection_params": {
        "protect_soc_high": {
            "help_text": "电池SOC超过此值时强制停止充电，防止过充",
            "impact_desc": "设置过高增加过充风险，设置过低减少可用容量",
            "typical_range": "93-98%",
            "learning_points": ["1.4", "4.2"]
        },
        "protect_soc_low": {
            "help_text": "电池SOC低于此值时强制停止放电，防止过放",
            "impact_desc": "设置过低增加过放风险，设置过高减少可用容量",
            "typical_range": "3-8%",
            "learning_points": ["1.4", "4.2"]
        },
        "power_limit_factor": {
            "help_text": "功率限制系数，用于限制实际充放电功率",
            "impact_desc": "降低功率可保护电池但减少调度能力",
            "typical_range": "0.8-1.0",
            "learning_points": ["4.3"]
        },
        "protect_temp_high": {
            "help_text": "电池温度超过此值时触发降功率或停机保护",
            "impact_desc": "高温运行会加速电池老化",
            "typical_range": "40-50℃",
            "learning_points": ["1.4", "5.3"]
        }
    },

    # 响应参数说明
    "response_params": {
        "response_time": {
            "help_text": "从收到指令到功率输出达到目标值的时间",
            "impact_desc": "响应越快，调频等辅助服务价值越高",
            "typical_range": "电池储能: 50-200ms",
            "learning_points": ["2.1"]
        },
        "ramp_rate": {
            "help_text": "功率变化的最大速率，限制功率突变",
            "impact_desc": "过快的功率变化可能影响电池寿命和电网稳定",
            "typical_range": "5-20 kW/s",
            "learning_points": ["2.1", "4.3"]
        }
    }
}
