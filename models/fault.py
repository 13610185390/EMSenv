# -*- coding: utf-8 -*-
"""故障诊断数据模型

对应技术设计文档：08_故障诊断模块技术设计.md
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# =============================================================================
# 故障类别枚举
# =============================================================================
class FaultCategory(Enum):
    """故障类别

    对应设计文档：08文档 2.1节
    """
    BATTERY = "电池类"
    PCS = "变流器类"
    COMMUNICATION = "通信类"
    PROTECTION = "保护类"
    CONTROL = "控制类"
    ENVIRONMENT = "环境类"
    # 扩展预留
    EXT_CATEGORY_1 = "_扩展类别1"
    EXT_CATEGORY_2 = "_扩展类别2"


class FaultSeverity(Enum):
    """故障严重程度

    对应设计文档：08文档 2.1节
    """
    INFO = "提示"           # 蓝色，仅记录
    WARNING = "一般"        # 黄色，提醒
    ALARM = "严重"          # 橙色，降功率
    CRITICAL = "紧急"       # 红色，停机


class FaultStatus(Enum):
    """故障状态

    对应设计文档：08文档 2.1节
    """
    ACTIVE = "活动"
    ACKNOWLEDGED = "已确认"
    RESOLVED = "已解决"
    CLEARED = "已清除"


# =============================================================================
# 故障类型定义数据类
# =============================================================================
@dataclass
class FaultType:
    """故障类型定义

    对应设计文档：08文档 2.1节
    """

    id: str                                 # 故障代码，如 F001
    name: str                               # 故障名称
    category: FaultCategory
    severity: FaultSeverity

    # 描述
    description: str = ""                   # 故障描述
    possible_causes: List[str] = field(default_factory=list)    # 可能原因
    symptoms: List[str] = field(default_factory=list)           # 故障现象

    # 处理
    immediate_action: str = ""              # 立即动作
    recovery_condition: str = ""            # 恢复条件
    handling_steps: List[str] = field(default_factory=list)     # 处理步骤

    # 教学
    learning_objectives: List[str] = field(default_factory=list)
    related_knowledge: List[str] = field(default_factory=list)
    difficulty: str = "intermediate"        # beginner, intermediate, advanced

    # 扩展预留
    ext_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.value if isinstance(
                self.category, FaultCategory
            ) else self.category,
            'severity': self.severity.value if isinstance(
                self.severity, FaultSeverity
            ) else self.severity,
            'description': self.description,
            'possible_causes': self.possible_causes,
            'symptoms': self.symptoms,
            'immediate_action': self.immediate_action,
            'recovery_condition': self.recovery_condition,
            'handling_steps': self.handling_steps,
            'learning_objectives': self.learning_objectives,
            'related_knowledge': self.related_knowledge,
            'difficulty': self.difficulty,
        }


# =============================================================================
# 故障实例数据类
# =============================================================================
@dataclass
class FaultInstance:
    """故障实例（模拟的具体故障）

    对应设计文档：08文档 2.2节
    """

    id: str                                 # 实例ID
    fault_type_id: str                      # 故障类型ID

    # 状态
    status: FaultStatus = FaultStatus.ACTIVE
    triggered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    # 故障数据
    fault_data: Dict[str, Any] = field(default_factory=dict)
    # 例如: {"soc_before": 50, "soc_after": 35, "jump_value": -15}

    # 处理记录
    handling_log: List[Dict[str, Any]] = field(default_factory=list)

    # 扩展预留
    ext_instance: Optional[Any] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'fault_type_id': self.fault_type_id,
            'status': self.status.value if isinstance(
                self.status, FaultStatus
            ) else self.status,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'fault_data': self.fault_data,
            'handling_log': self.handling_log,
        }


# =============================================================================
# 报警记录数据类
# =============================================================================
@dataclass
class AlarmRecord:
    """报警记录

    对应设计文档：08文档 2.2节
    """

    id: str
    alarm_code: str
    alarm_name: str
    severity: FaultSeverity
    triggered_at: datetime

    # 报警数据
    trigger_value: Any = None               # 触发值
    threshold: Any = None                   # 阈值
    component: str = ""                     # 相关组件

    # 状态
    status: str = "active"                  # active, acknowledged, cleared
    acknowledged_at: Optional[datetime] = None
    cleared_at: Optional[datetime] = None
    clear_reason: str = ""

    # 扩展预留
    ext_alarm: Optional[Any] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'alarm_code': self.alarm_code,
            'alarm_name': self.alarm_name,
            'severity': self.severity.value if isinstance(
                self.severity, FaultSeverity
            ) else self.severity,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'trigger_value': self.trigger_value,
            'threshold': self.threshold,
            'component': self.component,
            'status': self.status,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'cleared_at': self.cleared_at.isoformat() if self.cleared_at else None,
            'clear_reason': self.clear_reason,
        }


# =============================================================================
# 诊断步骤数据类
# =============================================================================
@dataclass
class DiagnosisStep:
    """诊断步骤

    对应设计文档：08文档 2.3节
    """

    step_number: int
    title: str
    instruction: str                        # 操作指引

    # 检查项
    check_items: List[Dict[str, Any]] = field(default_factory=list)
    # 格式: [{"question": "电压是否正常?", "options": ["是", "否"],
    #         "correct": "是", "next_if_yes": 3, "next_if_no": "voltage_issue"}]

    # 提示
    hint: str = ""
    warning: str = ""

    # 数据查看
    data_to_check: List[str] = field(default_factory=list)      # 需要查看的数据项
    expected_values: Dict[str, str] = field(default_factory=dict)

    # 扩展预留
    ext_step: Optional[Any] = None


# =============================================================================
# 诊断指南数据类
# =============================================================================
@dataclass
class DiagnosisGuide:
    """诊断指南

    对应设计文档：08文档 2.3节
    """

    id: str
    fault_type_id: str                      # 对应的故障类型
    title: str

    steps: List[DiagnosisStep] = field(default_factory=list)
    decision_tree: Dict[str, Any] = field(default_factory=dict)     # 决策树结构

    # 结论
    possible_conclusions: List[Dict[str, str]] = field(default_factory=list)
    # 格式: [{"id": "sensor_issue", "conclusion": "电流传感器故障",
    #         "solution": "校准或更换传感器"}]

    # 时限
    expected_time_minutes: int = 15

    # 扩展预留
    ext_guide: Optional[Any] = None

    def get_step(self, step_number: int) -> Optional[DiagnosisStep]:
        """获取指定步骤"""
        for step in self.steps:
            if step.step_number == step_number:
                return step
        return None

    def get_conclusion(self, conclusion_id: str) -> Optional[Dict[str, str]]:
        """获取指定结论"""
        for c in self.possible_conclusions:
            if c.get("id") == conclusion_id:
                return c
        return None


# =============================================================================
# 故障案例数据类
# =============================================================================
@dataclass
class FaultCase:
    """故障案例

    对应设计文档：08文档 2.4节
    """

    id: str                                 # 案例ID，如 F001-A
    fault_type_id: str
    title: str

    # 案例内容
    background: str = ""                    # 项目背景
    phenomenon: str = ""                    # 故障现象
    initial_data: Dict[str, Any] = field(default_factory=dict)  # 故障时数据

    # 诊断过程
    diagnosis_process: str = ""             # 诊断过程描述
    root_cause: str = ""                    # 根本原因

    # 解决方案
    solution: str = ""                      # 解决方案
    prevention: str = ""                    # 预防措施
    lessons_learned: List[str] = field(default_factory=list)    # 经验教训

    # 附件
    images: List[str] = field(default_factory=list)             # 图片URL
    data_files: List[str] = field(default_factory=list)         # 数据文件

    # 教学
    difficulty: str = "intermediate"
    related_knowledge: List[str] = field(default_factory=list)

    # 扩展预留
    ext_case: Optional[Any] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'fault_type_id': self.fault_type_id,
            'title': self.title,
            'background': self.background,
            'phenomenon': self.phenomenon,
            'initial_data': self.initial_data,
            'diagnosis_process': self.diagnosis_process,
            'root_cause': self.root_cause,
            'solution': self.solution,
            'prevention': self.prevention,
            'lessons_learned': self.lessons_learned,
            'difficulty': self.difficulty,
            'related_knowledge': self.related_knowledge,
        }


# =============================================================================
# 故障案例库数据类
# =============================================================================
@dataclass
class FaultCaseLibrary:
    """故障案例库

    对应设计文档：08文档 2.4节
    """

    cases: Dict[str, FaultCase] = field(default_factory=dict)

    def add_case(self, case: FaultCase) -> None:
        """添加案例"""
        self.cases[case.id] = case

    def get_case(self, case_id: str) -> Optional[FaultCase]:
        """获取指定案例"""
        return self.cases.get(case_id)

    def get_cases_by_type(self, fault_type_id: str) -> List[FaultCase]:
        """按故障类型获取案例"""
        return [c for c in self.cases.values() if c.fault_type_id == fault_type_id]

    def get_cases_by_difficulty(self, difficulty: str) -> List[FaultCase]:
        """按难度获取案例"""
        return [c for c in self.cases.values() if c.difficulty == difficulty]

    def search_cases(self, keyword: str) -> List[FaultCase]:
        """搜索案例"""
        keyword_lower = keyword.lower()
        return [
            c for c in self.cases.values()
            if keyword_lower in c.title.lower() or
               keyword_lower in c.phenomenon.lower() or
               keyword_lower in c.root_cause.lower()
        ]


# =============================================================================
# 诊断练习记录数据类
# =============================================================================
@dataclass
class DiagnosisPractice:
    """诊断练习记录

    对应设计文档：08文档 2.5节
    """

    id: str
    user_id: str
    fault_type_id: str
    guide_id: str

    # 时间
    started_at: datetime
    completed_at: Optional[datetime] = None
    time_spent_seconds: int = 0

    # 过程记录
    steps_completed: List[int] = field(default_factory=list)
    answers: Dict[str, Any] = field(default_factory=dict)   # {step_id: {check_id: answer}}
    hints_used: int = 0

    # 结果
    final_conclusion: str = ""
    is_correct: bool = False
    score: float = 0.0
    feedback: str = ""

    # 扩展预留
    ext_practice: Optional[Any] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'fault_type_id': self.fault_type_id,
            'guide_id': self.guide_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'time_spent_seconds': self.time_spent_seconds,
            'steps_completed': self.steps_completed,
            'hints_used': self.hints_used,
            'final_conclusion': self.final_conclusion,
            'is_correct': self.is_correct,
            'score': self.score,
            'feedback': self.feedback,
        }


# =============================================================================
# 故障诊断教学元数据
# =============================================================================
FAULT_TEACHING_META: Dict[str, Dict[str, Any]] = {
    # 故障类别说明
    "fault_categories": {
        "BATTERY": {
            "name": "电池类故障",
            "description": "与电池本体、BMS相关的故障",
            "typical_faults": ["SOC异常", "温度异常", "电压异常", "容量衰减"],
            "learning_points": ["1.2", "1.4", "5.1"]
        },
        "PCS": {
            "name": "变流器类故障",
            "description": "与PCS/逆变器相关的故障",
            "typical_faults": ["过流保护", "过压保护", "功率异常", "谐波超标"],
            "learning_points": ["2.1", "5.2"]
        },
        "COMMUNICATION": {
            "name": "通信类故障",
            "description": "与系统通信相关的故障",
            "typical_faults": ["通信中断", "数据异常", "协议错误"],
            "learning_points": ["6.1", "6.2"]
        },
        "PROTECTION": {
            "name": "保护类故障",
            "description": "保护功能触发导致的故障",
            "typical_faults": ["过充保护", "过放保护", "过温保护", "过流保护"],
            "learning_points": ["4.2", "5.3"]
        },
        "CONTROL": {
            "name": "控制类故障",
            "description": "与控制策略相关的故障",
            "typical_faults": ["功率受限", "调度异常", "策略冲突"],
            "learning_points": ["3.1", "3.2"]
        },
        "ENVIRONMENT": {
            "name": "环境类故障",
            "description": "与环境条件相关的故障",
            "typical_faults": ["环境过温", "湿度异常", "粉尘堵塞"],
            "learning_points": ["5.3"]
        }
    },

    # 故障严重程度说明
    "severity_levels": {
        "INFO": {
            "name": "提示",
            "color": "蓝色",
            "action": "仅记录，无需立即处理",
            "icon": "ℹ️"
        },
        "WARNING": {
            "name": "一般",
            "color": "黄色",
            "action": "提醒关注，建议检查",
            "icon": "⚠️"
        },
        "ALARM": {
            "name": "严重",
            "color": "橙色",
            "action": "需要处理，可能降功率运行",
            "icon": "🔶"
        },
        "CRITICAL": {
            "name": "紧急",
            "color": "红色",
            "action": "立即停机，紧急处理",
            "icon": "🔴"
        }
    },

    # 诊断流程说明
    "diagnosis_process": {
        "help_text": "故障诊断遵循标准化流程：确认现象→收集数据→分析原因→验证判断→制定方案",
        "steps": [
            "1. 确认故障现象：明确故障表现",
            "2. 收集数据：记录相关参数和日志",
            "3. 分析原因：根据数据推断原因",
            "4. 验证判断：通过测试验证推断",
            "5. 制定方案：确定处理措施"
        ],
        "learning_points": ["5.1", "5.2", "5.3"]
    },

    # 常见故障说明
    "common_faults": {
        "F001": {
            "name": "SOC异常跳变",
            "frequency": "常见",
            "difficulty": "中等",
            "key_checks": ["电流传感器", "BMS通信", "SOC校准状态"],
            "learning_points": ["1.2", "5.1"]
        },
        "F002": {
            "name": "BMS通信中断",
            "frequency": "较少",
            "difficulty": "简单",
            "key_checks": ["通信线缆", "端口状态", "通信参数"],
            "learning_points": ["6.1", "6.2"]
        },
        "F003": {
            "name": "功率输出受限",
            "frequency": "常见",
            "difficulty": "中等",
            "key_checks": ["SOC状态", "温度", "功率参数"],
            "learning_points": ["2.2", "4.3"]
        },
        "F004": {
            "name": "电池过温保护",
            "frequency": "季节性",
            "difficulty": "简单",
            "key_checks": ["环境温度", "空调状态", "温度传感器"],
            "learning_points": ["1.4", "5.3"]
        }
    }
}
