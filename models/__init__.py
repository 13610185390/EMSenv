# -*- coding: utf-8 -*-
"""数据模型模块

包含BESS参数、经济参数、控制策略、仿真结果、故障诊断等数据类定义

对应开发规划文档：阶段1 基础架构层
"""

# BESS参数模型
from .bess import (
    BatteryType,
    BESSParams,
    ParamTeachingMeta,
    ParamConstraint,
    BESS_TEACHING_META,
    BESS_CONSTRAINTS,
    EnergyStorageBase,
)

# 经济参数模型
from .economic import (
    PricePeriodType,
    TimePeriod,
    ElectricityPriceParams,
    CostParams,
    FinancialParams,
    EconomicParams,
    ECONOMIC_TEACHING_META,
)

# 控制策略模型
from .control import (
    DispatchMode,
    ChargeStrategy,
    DischargeStrategy,
    PowerControlMode,
    ChargeDischargeStrategy,
    ProtectionParams,
    ResponseParams,
    ControlParams,
    SchedulePoint,
    DispatchSchedule,
    CONTROL_TEACHING_META,
)

# 仿真结果模型
from .simulation import (
    LoadProfileType,
    SimulationConfig,
    BESSState,
    TimeStepResult,
    SimulationResult,
    SIMULATION_TEACHING_META,
)

# 故障诊断模型
from .fault import (
    FaultCategory,
    FaultSeverity,
    FaultStatus,
    FaultType,
    FaultInstance,
    AlarmRecord,
    DiagnosisStep,
    DiagnosisGuide,
    FaultCase,
    FaultCaseLibrary,
    DiagnosisPractice,
    FAULT_TEACHING_META,
)


__all__ = [
    # BESS
    'BatteryType', 'BESSParams', 'ParamTeachingMeta', 'ParamConstraint',
    'BESS_TEACHING_META', 'BESS_CONSTRAINTS', 'EnergyStorageBase',
    # Economic
    'PricePeriodType', 'TimePeriod', 'ElectricityPriceParams',
    'CostParams', 'FinancialParams', 'EconomicParams', 'ECONOMIC_TEACHING_META',
    # Control
    'DispatchMode', 'ChargeStrategy', 'DischargeStrategy', 'PowerControlMode',
    'ChargeDischargeStrategy', 'ProtectionParams', 'ResponseParams',
    'ControlParams', 'SchedulePoint', 'DispatchSchedule', 'CONTROL_TEACHING_META',
    # Simulation
    'LoadProfileType', 'SimulationConfig', 'BESSState', 'TimeStepResult',
    'SimulationResult', 'SIMULATION_TEACHING_META',
    # Fault
    'FaultCategory', 'FaultSeverity', 'FaultStatus', 'FaultType',
    'FaultInstance', 'AlarmRecord', 'DiagnosisStep', 'DiagnosisGuide',
    'FaultCase', 'FaultCaseLibrary', 'DiagnosisPractice', 'FAULT_TEACHING_META',
]
