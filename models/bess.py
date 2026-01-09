# -*- coding: utf-8 -*-
"""BESS参数数据模型

对应技术设计文档：01_基础参数模块技术设计.md
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from abc import ABC, abstractmethod


# =============================================================================
# 电池类型枚举
# =============================================================================
class BatteryType(Enum):
    """电池类型枚举"""
    LITHIUM_ION = "锂电池"
    LEAD_ACID = "铅酸电池"
    LFP = "磷酸铁锂"
    NMC = "三元锂电池"
    # 扩展预留
    EXT_TYPE_1 = "_扩展类型1"
    EXT_TYPE_2 = "_扩展类型2"


# =============================================================================
# BESS参数数据类
# =============================================================================
@dataclass
class BESSParams:
    """电池储能系统参数数据类

    对应设计文档：01文档 2.1节
    """

    # === 设备基本信息 ===
    name: str = "BESS_01"
    battery_type: BatteryType = BatteryType.LFP
    enabled: bool = True

    # === 容量与功率参数 ===
    capacity: float = 100.0              # kWh，额定容量
    power_rated: float = 50.0            # kW，额定功率
    power_charge_max: Optional[float] = None    # kW，充电功率上限
    power_discharge_max: Optional[float] = None # kW，放电功率上限
    # 扩展预留
    ext_power_1: Optional[Any] = None
    ext_power_2: Optional[Any] = None

    # === 效率参数 ===
    efficiency_charge: float = 95.0      # %，充电效率
    efficiency_discharge: float = 95.0   # %，放电效率
    self_discharge_rate: float = 0.1     # %/天，自放电率
    # 扩展预留
    ext_eff_1: Optional[Any] = None

    # === SOC参数 ===
    soc_min: float = 10.0                # %，SOC下限
    soc_max: float = 90.0                # %，SOC上限
    soc_init: float = 50.0               # %，初始SOC
    soc_target: Optional[float] = None   # %，目标SOC
    # 扩展预留
    ext_soc_1: Optional[Any] = None

    # === 寿命参数 ===
    cycle_life: int = 6000               # 次，循环寿命
    calendar_life: int = 15              # 年，日历寿命
    degradation_rate: float = 2.0        # %/年，容量衰减
    # 扩展预留
    ext_life_1: Optional[Any] = None

    # === 元数据 ===
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理：设置默认值"""
        if self.power_charge_max is None:
            self.power_charge_max = self.power_rated
        if self.power_discharge_max is None:
            self.power_discharge_max = self.power_rated
        if self.soc_target is None:
            self.soc_target = self.soc_init

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'name': self.name,
            'battery_type': self.battery_type.value if isinstance(self.battery_type, BatteryType) else self.battery_type,
            'enabled': self.enabled,
            'capacity': self.capacity,
            'power_rated': self.power_rated,
            'power_charge_max': self.power_charge_max,
            'power_discharge_max': self.power_discharge_max,
            'efficiency_charge': self.efficiency_charge,
            'efficiency_discharge': self.efficiency_discharge,
            'self_discharge_rate': self.self_discharge_rate,
            'soc_min': self.soc_min,
            'soc_max': self.soc_max,
            'soc_init': self.soc_init,
            'soc_target': self.soc_target,
            'cycle_life': self.cycle_life,
            'calendar_life': self.calendar_life,
            'degradation_rate': self.degradation_rate,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BESSParams':
        """从字典创建实例"""
        # 处理电池类型
        battery_type = data.get('battery_type', 'LFP')
        if isinstance(battery_type, str):
            # 尝试从值匹配
            for bt in BatteryType:
                if bt.value == battery_type or bt.name == battery_type:
                    battery_type = bt
                    break
            else:
                battery_type = BatteryType.LFP

        return cls(
            name=data.get('name', 'BESS_01'),
            battery_type=battery_type,
            enabled=data.get('enabled', True),
            capacity=data.get('capacity', 100.0),
            power_rated=data.get('power_rated', 50.0),
            power_charge_max=data.get('power_charge_max'),
            power_discharge_max=data.get('power_discharge_max'),
            efficiency_charge=data.get('efficiency_charge', 95.0),
            efficiency_discharge=data.get('efficiency_discharge', 95.0),
            self_discharge_rate=data.get('self_discharge_rate', 0.1),
            soc_min=data.get('soc_min', 10.0),
            soc_max=data.get('soc_max', 90.0),
            soc_init=data.get('soc_init', 50.0),
            soc_target=data.get('soc_target'),
            cycle_life=data.get('cycle_life', 6000),
            calendar_life=data.get('calendar_life', 15),
            degradation_rate=data.get('degradation_rate', 2.0),
            metadata=data.get('metadata', {}),
        )

    @property
    def usable_capacity(self) -> float:
        """可用容量 (kWh)"""
        return self.capacity * (self.soc_max - self.soc_min) / 100

    @property
    def duration_hours(self) -> float:
        """储能时长 (小时) = 容量/功率"""
        if self.power_rated > 0:
            return self.capacity / self.power_rated
        return 0.0

    @property
    def round_trip_efficiency(self) -> float:
        """往返效率 (%)"""
        return self.efficiency_charge * self.efficiency_discharge / 100


# =============================================================================
# 参数教学元数据
# =============================================================================
@dataclass
class ParamTeachingMeta:
    """参数教学元数据

    对应设计文档：01文档 2.1节
    """
    help_text: str = ""                    # 参数概念解释
    impact_desc: str = ""                  # 参数变化影响说明
    typical_range: str = ""                # 典型应用场景的建议范围
    related_params: List[str] = field(default_factory=list)  # 关联参数列表
    warning_conditions: List[str] = field(default_factory=list)  # 警示条件
    learning_points: List[str] = field(default_factory=list)  # 关联知识点编号


# BESS参数教学元数据配置
BESS_TEACHING_META: Dict[str, ParamTeachingMeta] = {
    "capacity": ParamTeachingMeta(
        help_text="储能系统可存储的总电量，类似于\"油箱大小\"",
        impact_desc="容量↑→可调度能量↑，但投资成本↑",
        typical_range="工商业: 100-10000kWh",
        related_params=["power_rated"],
        warning_conditions=["容量与功率比(时长)建议在0.5-4小时之间"],
        learning_points=["1.1", "4.1"]
    ),
    "power_rated": ParamTeachingMeta(
        help_text="最大充放电速率，类似于\"加油/放油速度\"",
        impact_desc="功率↑→响应能力↑，但PCS成本↑",
        typical_range="通常为容量的0.25-2倍",
        related_params=["capacity", "power_charge_max", "power_discharge_max"],
        learning_points=["1.1", "4.1"]
    ),
    "power_charge_max": ParamTeachingMeta(
        help_text="允许的最大充电功率，保护电池寿命",
        impact_desc="过高会加速电池老化",
        typical_range="通常等于或小于额定功率",
        related_params=["power_rated"],
        learning_points=["1.3", "4.1"]
    ),
    "power_discharge_max": ParamTeachingMeta(
        help_text="允许的最大放电功率",
        impact_desc="过高会加速电池老化",
        typical_range="通常等于或小于额定功率",
        related_params=["power_rated"],
        learning_points=["1.3", "4.1"]
    ),
    "efficiency_charge": ParamTeachingMeta(
        help_text="充电时电能转化为化学能的效率",
        impact_desc="效率↓→能量损耗↑，运行成本↑",
        typical_range="锂电池: 94-97%",
        related_params=["efficiency_discharge"],
        learning_points=["1.3"]
    ),
    "efficiency_discharge": ParamTeachingMeta(
        help_text="放电时化学能转化为电能的效率",
        impact_desc="效率↓→能量损耗↑，运行成本↑",
        typical_range="锂电池: 94-97%",
        related_params=["efficiency_charge"],
        learning_points=["1.3"]
    ),
    "self_discharge_rate": ParamTeachingMeta(
        help_text="电池静置时SOC的自然下降速率",
        impact_desc="长期静置需考虑能量损失",
        typical_range="锂电池: 0.05-0.2%/天",
        learning_points=["1.2"]
    ),
    "soc_min": ParamTeachingMeta(
        help_text="允许放电的最低SOC，保护电池深放",
        impact_desc="下限↓→可用容量↑，但影响寿命",
        typical_range="工商业: 10-20%，备电: 5-10%",
        related_params=["soc_max", "soc_init"],
        warning_conditions=["设置过低会加速电池老化"],
        learning_points=["1.2", "4.2"]
    ),
    "soc_max": ParamTeachingMeta(
        help_text="允许充电的最高SOC，保护电池过充",
        impact_desc="上限↑→可用容量↑，但影响寿命",
        typical_range="工商业: 90-95%",
        related_params=["soc_min", "soc_init"],
        warning_conditions=["设置过高会加速电池老化"],
        learning_points=["1.2", "4.2"]
    ),
    "soc_init": ParamTeachingMeta(
        help_text="仿真开始时的SOC状态",
        impact_desc="影响首次充放电时机",
        typical_range="通常设为50%左右",
        related_params=["soc_min", "soc_max"],
        learning_points=["1.2"]
    ),
    "cycle_life": ParamTeachingMeta(
        help_text="电池可承受的等效满充满放次数",
        impact_desc="循环次数决定电池更换周期",
        typical_range="磷酸铁锂: 4000-8000次，三元锂: 2000-4000次",
        related_params=["calendar_life", "degradation_rate"],
        learning_points=["1.4"]
    ),
    "calendar_life": ParamTeachingMeta(
        help_text="电池的物理使用年限",
        impact_desc="即使不使用也会老化",
        typical_range="10-20年",
        related_params=["cycle_life"],
        learning_points=["1.4"]
    ),
    "degradation_rate": ParamTeachingMeta(
        help_text="电池容量每年的衰减比例",
        impact_desc="影响长期经济性计算",
        typical_range="1.5-3%/年",
        related_params=["cycle_life", "calendar_life"],
        learning_points=["1.4"]
    ),
}


# =============================================================================
# 参数约束定义
# =============================================================================
@dataclass
class ParamConstraint:
    """参数约束定义

    对应设计文档：01文档 2.2节
    """
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    required: bool = True
    depends_on: Optional[str] = None      # 依赖其他参数
    validator: Optional[callable] = None  # 自定义校验函数


# BESS参数约束配置
BESS_CONSTRAINTS: Dict[str, ParamConstraint] = {
    "capacity": ParamConstraint(min_value=10, max_value=10000, required=True),
    "power_rated": ParamConstraint(min_value=5, max_value=5000, required=True),
    "power_charge_max": ParamConstraint(
        min_value=0,
        depends_on="power_rated",
        required=False
    ),
    "power_discharge_max": ParamConstraint(
        min_value=0,
        depends_on="power_rated",
        required=False
    ),
    "efficiency_charge": ParamConstraint(min_value=80, max_value=99, required=True),
    "efficiency_discharge": ParamConstraint(min_value=80, max_value=99, required=True),
    "self_discharge_rate": ParamConstraint(min_value=0, max_value=5, required=False),
    "soc_min": ParamConstraint(min_value=0, max_value=50, required=True),
    "soc_max": ParamConstraint(min_value=50, max_value=100, required=True),
    "soc_init": ParamConstraint(
        depends_on="soc_min,soc_max",
        required=True
    ),
    "cycle_life": ParamConstraint(min_value=1000, max_value=15000, required=True),
    "calendar_life": ParamConstraint(min_value=5, max_value=25, required=True),
    "degradation_rate": ParamConstraint(min_value=0, max_value=10, required=False),
}


# =============================================================================
# 储能设备抽象基类（扩展预留）
# =============================================================================
class EnergyStorageBase(ABC):
    """储能设备抽象基类 - 用于扩展其他储能类型

    对应设计文档：01文档 2.3节
    """

    @abstractmethod
    def get_parameters(self) -> dataclass:
        """获取参数数据类实例"""
        pass

    @abstractmethod
    def get_constraints(self) -> Dict[str, ParamConstraint]:
        """获取参数约束配置"""
        pass

    @abstractmethod
    def validate(self) -> tuple:
        """校验参数，返回(是否通过, 错误信息列表)"""
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        """转换为字典"""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> 'EnergyStorageBase':
        """从字典创建实例"""
        pass

    # 扩展方法预留
    def ext_method_1(self):
        """扩展方法预留"""
        pass
