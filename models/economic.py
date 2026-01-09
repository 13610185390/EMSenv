# -*- coding: utf-8 -*-
"""经济参数数据模型

对应技术设计文档：02_经济参数模块技术设计.md
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import time


# =============================================================================
# 电价时段类型枚举
# =============================================================================
class PricePeriodType(Enum):
    """电价时段类型"""
    VALLEY = "谷时"
    FLAT = "平时"
    PEAK = "峰时"
    CRITICAL = "尖峰"
    # 扩展预留
    EXT_PERIOD_1 = "_扩展时段1"
    EXT_PERIOD_2 = "_扩展时段2"


# =============================================================================
# 时段定义数据类
# =============================================================================
@dataclass
class TimePeriod:
    """时段定义

    对应设计文档：02文档 2.1节
    """
    start: time          # 开始时间
    end: time            # 结束时间
    period_type: PricePeriodType

    def contains(self, t: time) -> bool:
        """判断时间点是否在此时段内"""
        if self.start <= self.end:
            return self.start <= t < self.end
        else:  # 跨日时段
            return t >= self.start or t < self.end

    def duration_hours(self) -> float:
        """计算时段时长（小时）"""
        start_minutes = self.start.hour * 60 + self.start.minute
        end_minutes = self.end.hour * 60 + self.end.minute
        if end_minutes > start_minutes:
            return (end_minutes - start_minutes) / 60
        else:  # 跨日
            return (24 * 60 - start_minutes + end_minutes) / 60


# =============================================================================
# 电价参数数据类
# =============================================================================
@dataclass
class ElectricityPriceParams:
    """电价参数数据类

    对应设计文档：02文档 2.1节
    """

    # === 基础电价 (元/kWh) ===
    price_valley: float = 0.4           # 谷时电价
    price_flat: float = 0.8             # 平时电价
    price_peak: float = 1.2             # 峰时电价
    price_critical: Optional[float] = None  # 尖峰电价（可选）
    price_feed_in: Optional[float] = 0.5    # 上网电价
    # 扩展预留
    ext_price_1: Optional[float] = None
    ext_price_2: Optional[float] = None

    # === 时段划分 ===
    periods: List[TimePeriod] = field(default_factory=list)

    # === 元数据 ===
    scheme_name: str = "默认电价方案"
    description: str = ""

    def __post_init__(self):
        """初始化默认时段"""
        if not self.periods:
            self.periods = self._default_periods()

    def _default_periods(self) -> List[TimePeriod]:
        """默认时段配置"""
        return [
            TimePeriod(time(0, 0), time(8, 0), PricePeriodType.VALLEY),
            TimePeriod(time(8, 0), time(10, 0), PricePeriodType.FLAT),
            TimePeriod(time(10, 0), time(12, 0), PricePeriodType.PEAK),
            TimePeriod(time(12, 0), time(18, 0), PricePeriodType.FLAT),
            TimePeriod(time(18, 0), time(22, 0), PricePeriodType.PEAK),
            TimePeriod(time(22, 0), time(23, 59), PricePeriodType.FLAT),
        ]

    def get_price_at(self, t: time) -> float:
        """获取指定时间的电价"""
        for period in self.periods:
            if period.contains(t):
                price_map = {
                    PricePeriodType.VALLEY: self.price_valley,
                    PricePeriodType.FLAT: self.price_flat,
                    PricePeriodType.PEAK: self.price_peak,
                    PricePeriodType.CRITICAL: self.price_critical or self.price_peak,
                }
                return price_map.get(period.period_type, self.price_flat)
        return self.price_flat  # 默认返回平时电价

    def get_price_curve(self, timestep_minutes: int = 15) -> List[float]:
        """生成24小时电价曲线"""
        prices = []
        for i in range(0, 24 * 60, timestep_minutes):
            t = time(i // 60, i % 60)
            prices.append(self.get_price_at(t))
        return prices

    def get_period_type_at(self, t: time) -> PricePeriodType:
        """获取指定时间的时段类型"""
        for period in self.periods:
            if period.contains(t):
                return period.period_type
        return PricePeriodType.FLAT

    @property
    def peak_valley_spread(self) -> float:
        """峰谷价差 (元/kWh)"""
        return self.price_peak - self.price_valley


# =============================================================================
# 成本参数数据类
# =============================================================================
@dataclass
class CostParams:
    """成本参数数据类

    对应设计文档：02文档 2.2节
    """

    # === 投资成本 ===
    cost_per_kwh: float = 1500.0        # 元/kWh，单位容量成本
    cost_per_kw: float = 500.0          # 元/kW，单位功率成本
    cost_install_ratio: float = 10.0    # %，安装成本比例
    # 扩展预留
    ext_cost_1: Optional[float] = None

    # === 运营成本 ===
    cost_om_ratio: float = 2.0          # %，年运维成本比例
    cost_insurance_ratio: float = 0.5   # %，保险费率
    # 扩展预留
    ext_om_1: Optional[float] = None

    def calculate_initial_investment(
        self,
        capacity_kwh: float,
        power_kw: float
    ) -> float:
        """
        计算初始投资成本

        Args:
            capacity_kwh: 容量 (kWh)
            power_kw: 功率 (kW)

        Returns:
            float: 总初始投资（元）
        """
        equipment_cost = (
            capacity_kwh * self.cost_per_kwh +
            power_kw * self.cost_per_kw
        )
        install_cost = equipment_cost * self.cost_install_ratio / 100
        return equipment_cost + install_cost

    def calculate_annual_opex(self, initial_investment: float) -> float:
        """
        计算年运营成本

        Args:
            initial_investment: 初始投资（元）

        Returns:
            float: 年运营成本（元）
        """
        om_cost = initial_investment * self.cost_om_ratio / 100
        insurance_cost = initial_investment * self.cost_insurance_ratio / 100
        return om_cost + insurance_cost


# =============================================================================
# 财务参数数据类
# =============================================================================
@dataclass
class FinancialParams:
    """财务参数数据类

    对应设计文档：02文档 2.3节
    """

    discount_rate: float = 8.0          # %，贴现率
    project_years: int = 15             # 年，项目周期
    residual_ratio: float = 5.0         # %，残值率
    # 扩展预留
    ext_fin_1: Optional[float] = None

    def calculate_npv(
        self,
        initial_investment: float,
        annual_cash_flows: List[float]
    ) -> float:
        """
        计算净现值 (NPV)

        Args:
            initial_investment: 初始投资
            annual_cash_flows: 各年现金流列表

        Returns:
            float: NPV值
        """
        npv = -initial_investment
        r = self.discount_rate / 100

        for year, cf in enumerate(annual_cash_flows, 1):
            npv += cf / ((1 + r) ** year)

        # 残值
        residual = initial_investment * self.residual_ratio / 100
        npv += residual / ((1 + r) ** len(annual_cash_flows))

        return npv

    def calculate_payback_period(
        self,
        initial_investment: float,
        annual_revenue: float
    ) -> float:
        """
        计算静态投资回收期

        Args:
            initial_investment: 初始投资（元）
            annual_revenue: 年净收益（元）

        Returns:
            float: 回收期（年）
        """
        if annual_revenue <= 0:
            return float('inf')
        return initial_investment / annual_revenue

    def calculate_dynamic_payback(
        self,
        initial_investment: float,
        annual_cash_flows: List[float]
    ) -> float:
        """
        计算动态投资回收期

        Args:
            initial_investment: 初始投资
            annual_cash_flows: 各年现金流列表

        Returns:
            float: 动态回收期（年）
        """
        r = self.discount_rate / 100
        cumulative = -initial_investment

        for year, cf in enumerate(annual_cash_flows, 1):
            discounted_cf = cf / ((1 + r) ** year)
            cumulative += discounted_cf
            if cumulative >= 0:
                # 线性插值计算精确回收期
                prev_cumulative = cumulative - discounted_cf
                fraction = -prev_cumulative / discounted_cf
                return year - 1 + fraction

        return float('inf')


# =============================================================================
# 经济参数汇总数据类
# =============================================================================
@dataclass
class EconomicParams:
    """经济参数汇总数据类

    对应设计文档：02文档 2.3节
    """

    price_params: ElectricityPriceParams = field(
        default_factory=ElectricityPriceParams
    )
    cost_params: CostParams = field(default_factory=CostParams)
    financial_params: FinancialParams = field(default_factory=FinancialParams)

    # 扩展预留
    ext_params: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# 经济参数教学元数据
# =============================================================================
ECONOMIC_TEACHING_META: Dict[str, Dict[str, Any]] = {
    # 电价参数
    "price_valley": {
        "help_text": "低谷时段电价，通常在夜间和凌晨，是充电的最佳时机",
        "impact_desc": "谷电价↓→充电成本↓，套利空间↑",
        "typical_range": "工商业: 0.3-0.5元/kWh",
        "learning_points": ["2.3", "3.1"]
    },
    "price_flat": {
        "help_text": "平时段电价，介于峰谷之间的普通时段",
        "impact_desc": "平电价主要影响日常运营基准",
        "typical_range": "工商业: 0.6-0.9元/kWh",
        "learning_points": ["2.3", "3.1"]
    },
    "price_peak": {
        "help_text": "高峰时段电价，用电高峰期，是放电获利的最佳时机",
        "impact_desc": "峰电价↑→放电收益↑，套利空间↑",
        "typical_range": "工商业: 1.0-1.5元/kWh",
        "learning_points": ["2.3", "3.1"]
    },
    "price_critical": {
        "help_text": "尖峰时段电价（部分地区），极端用电高峰的特殊电价",
        "impact_desc": "尖峰电价存在时，收益空间显著提升",
        "typical_range": "部分地区: 1.3-2.0元/kWh",
        "learning_points": ["2.3", "3.1"]
    },

    # 成本参数
    "cost_per_kwh": {
        "help_text": "储能系统单位容量成本，包含电池模组及配套",
        "impact_desc": "单价↓→初始投资↓，回收期↓",
        "typical_range": "磷酸铁锂: 1000-2000元/kWh (2024年)",
        "learning_points": ["2.3"]
    },
    "cost_per_kw": {
        "help_text": "储能系统单位功率成本，主要是PCS变流器成本",
        "impact_desc": "功率成本占比随功率/容量比增大而增加",
        "typical_range": "PCS: 300-800元/kW",
        "learning_points": ["2.3"]
    },
    "cost_install_ratio": {
        "help_text": "安装及配套成本占设备成本的比例",
        "impact_desc": "包含运输、安装、调试等费用",
        "typical_range": "8-15%",
        "learning_points": ["2.3"]
    },
    "cost_om_ratio": {
        "help_text": "年运维成本占初始投资的比例",
        "impact_desc": "运维成本影响年净收益",
        "typical_range": "1.5-3%",
        "learning_points": ["2.3"]
    },

    # 财务参数
    "discount_rate": {
        "help_text": "贴现率，用于计算资金时间价值的折现率",
        "impact_desc": "贴现率↑→NPV↓，项目价值评估更保守",
        "typical_range": "6-12%，取决于融资成本和风险偏好",
        "learning_points": ["2.3"]
    },
    "project_years": {
        "help_text": "项目经济分析周期，通常与设备寿命相关",
        "impact_desc": "周期↑→累计收益↑，但远期收益不确定性增加",
        "typical_range": "10-20年",
        "learning_points": ["2.3"]
    },
    "residual_ratio": {
        "help_text": "项目结束时设备残值占初始投资的比例",
        "impact_desc": "残值提高项目NPV",
        "typical_range": "3-10%",
        "learning_points": ["2.3"]
    },
}
