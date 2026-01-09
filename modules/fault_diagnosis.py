# -*- coding: utf-8 -*-
"""故障诊断模块

对应技术设计文档：08_故障诊断模块技术设计.md
提供故障模拟、报警分析、排查指南和案例复盘功能
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from datetime import datetime

import gradio as gr


# =============================================================================
# 数据类定义
# =============================================================================
class FaultCategory(Enum):
    """故障类别"""
    BATTERY = "电池类"
    PCS = "变流器类"
    COMMUNICATION = "通信类"
    PROTECTION = "保护类"
    CONTROL = "控制类"
    ENVIRONMENT = "环境类"


class FaultSeverity(Enum):
    """故障严重程度"""
    INFO = "提示"       # 蓝色
    WARNING = "一般"    # 黄色
    ALARM = "严重"      # 橙色
    CRITICAL = "紧急"   # 红色


class FaultStatus(Enum):
    """故障状态"""
    ACTIVE = "活动"
    ACKNOWLEDGED = "已确认"
    RESOLVED = "已解决"
    CLEARED = "已清除"


@dataclass
class FaultType:
    """故障类型定义"""
    id: str
    name: str
    category: FaultCategory
    severity: FaultSeverity
    description: str = ""
    possible_causes: List[str] = field(default_factory=list)
    symptoms: List[str] = field(default_factory=list)
    immediate_action: str = ""
    recovery_condition: str = ""
    handling_steps: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    related_knowledge: List[str] = field(default_factory=list)
    difficulty: str = "intermediate"


@dataclass
class FaultInstance:
    """故障实例"""
    id: str
    fault_type_id: str
    status: FaultStatus = FaultStatus.ACTIVE
    triggered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    fault_data: Dict[str, Any] = field(default_factory=dict)
    handling_log: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AlarmRecord:
    """报警记录"""
    id: str
    alarm_code: str
    alarm_name: str
    severity: FaultSeverity
    triggered_at: datetime
    trigger_value: Any = None
    threshold: Any = None
    component: str = ""
    status: str = "active"
    acknowledged_at: Optional[datetime] = None
    cleared_at: Optional[datetime] = None


@dataclass
class DiagnosisStep:
    """诊断步骤"""
    step_number: int
    title: str
    instruction: str
    check_items: List[Dict[str, Any]] = field(default_factory=list)
    hint: str = ""
    warning: str = ""
    data_to_check: List[str] = field(default_factory=list)


@dataclass
class DiagnosisGuide:
    """诊断指南"""
    id: str
    fault_type_id: str
    title: str
    steps: List[DiagnosisStep] = field(default_factory=list)
    possible_conclusions: List[Dict[str, str]] = field(default_factory=list)
    expected_time_minutes: int = 15


@dataclass
class FaultCase:
    """故障案例"""
    id: str
    fault_type_id: str
    title: str
    background: str = ""
    phenomenon: str = ""
    initial_data: Dict[str, Any] = field(default_factory=dict)
    diagnosis_process: str = ""
    root_cause: str = ""
    solution: str = ""
    prevention: str = ""
    lessons_learned: List[str] = field(default_factory=list)
    difficulty: str = "intermediate"


# =============================================================================
# 模块状态
# =============================================================================
_fault_types: Optional[Dict[str, FaultType]] = None
_diagnosis_guides: Optional[Dict[str, DiagnosisGuide]] = None
_fault_cases: Optional[Dict[str, FaultCase]] = None
_active_faults: Dict[str, FaultInstance] = {}
_alarm_records: List[AlarmRecord] = []
_current_practice_step: int = 1
_practice_answers: Dict[str, Any] = {}


# =============================================================================
# 初始化函数
# =============================================================================
def _init_fault_types() -> Dict[str, FaultType]:
    """初始化故障类型"""
    fault_types = {}

    fault_types["F001"] = FaultType(
        id="F001",
        name="SOC异常跳变",
        category=FaultCategory.BATTERY,
        severity=FaultSeverity.ALARM,
        description="SOC值在短时间内发生异常跳变，超出正常变化范围",
        possible_causes=[
            "BMS的SOC估算误差累积",
            "电流传感器零漂或故障",
            "电池单体电压异常",
            "SOC-OCV对照表不准确",
            "电池容量衰减严重"
        ],
        symptoms=[
            "SOC显示值突然变化超过5%",
            "SOC变化与充放电电量不匹配",
            "可能伴随电池电压异常"
        ],
        immediate_action="暂停充放电，记录故障数据",
        recovery_condition="SOC校准完成且连续运行正常超过24小时",
        handling_steps=[
            "记录故障发生时的SOC、电压、电流数据",
            "检查BMS通信是否正常",
            "核对电流传感器采样值",
            "执行SOC校准程序",
            "观察运行是否恢复正常"
        ],
        learning_objectives=[
            "理解SOC的计算原理",
            "掌握SOC异常的判断方法",
            "学会SOC校准操作"
        ],
        related_knowledge=["1.2"],
        difficulty="intermediate"
    )

    fault_types["F002"] = FaultType(
        id="F002",
        name="BMS通信中断",
        category=FaultCategory.COMMUNICATION,
        severity=FaultSeverity.CRITICAL,
        description="EMS与BMS之间的通信中断，无法获取电池数据",
        possible_causes=[
            "通信线缆松动或断开",
            "通信接口故障",
            "BMS设备故障",
            "通信参数配置错误",
            "电磁干扰"
        ],
        symptoms=[
            "电池数据停止更新",
            "EMS显示通信故障报警",
            "系统自动停机保护"
        ],
        immediate_action="系统立即停机，确保安全",
        recovery_condition="通信恢复正常并人工确认",
        handling_steps=[
            "检查通信线缆连接",
            "检查通信端口指示灯",
            "使用调试工具测试通信",
            "核对通信参数配置",
            "必要时重启BMS"
        ],
        learning_objectives=[
            "理解储能系统通信架构",
            "掌握通信故障的排查方法",
            "学会使用调试工具"
        ],
        related_knowledge=["2.1"],
        difficulty="beginner"
    )

    fault_types["F003"] = FaultType(
        id="F003",
        name="功率输出受限",
        category=FaultCategory.CONTROL,
        severity=FaultSeverity.WARNING,
        description="实际输出功率低于设定功率，系统主动限功率运行",
        possible_causes=[
            "SOC接近上下限",
            "电池温度过高或过低",
            "PCS过载保护",
            "电网电压异常",
            "功率限制参数设置"
        ],
        symptoms=[
            "实际功率<设定功率",
            "可能伴随限功率报警",
            "功率曲线出现平顶"
        ],
        immediate_action="记录限功率时的运行数据",
        recovery_condition="限功率条件消除",
        handling_steps=[
            "检查当前SOC是否接近限值",
            "检查电池温度是否正常",
            "检查PCS运行状态",
            "检查电网电压",
            "核对功率限制参数设置"
        ],
        learning_objectives=[
            "理解功率限制的触发条件",
            "掌握限功率原因的分析方法"
        ],
        related_knowledge=["2.2"],
        difficulty="intermediate"
    )

    fault_types["F004"] = FaultType(
        id="F004",
        name="电池过温保护",
        category=FaultCategory.PROTECTION,
        severity=FaultSeverity.ALARM,
        description="电池温度超过保护阈值，系统触发降功率或停机保护",
        possible_causes=[
            "环境温度过高",
            "空调/风扇故障",
            "电池内阻增大",
            "长时间大功率运行",
            "温度传感器故障"
        ],
        symptoms=[
            "电池温度显示超限",
            "过温报警触发",
            "系统自动降功率或停机"
        ],
        immediate_action="降低功率或停止运行",
        recovery_condition="温度降至正常范围",
        handling_steps=[
            "检查环境温度",
            "检查空调/风扇运行状态",
            "检查电池舱门是否关闭",
            "检查温度传感器是否正常",
            "等待温度下降后恢复运行"
        ],
        learning_objectives=[
            "理解电池热管理重要性",
            "掌握过温故障的处理方法"
        ],
        related_knowledge=["1.2"],
        difficulty="beginner"
    )

    return fault_types


def _init_diagnosis_guides() -> Dict[str, DiagnosisGuide]:
    """初始化诊断指南"""
    guides = {}

    # SOC跳变诊断指南
    guides["DG_F001"] = DiagnosisGuide(
        id="DG_F001",
        fault_type_id="F001",
        title="SOC异常跳变排查指南",
        steps=[
            DiagnosisStep(
                step_number=1,
                title="确认故障现象",
                instruction="首先确认SOC跳变的具体情况",
                check_items=[
                    {"id": "jump_magnitude", "question": "SOC跳变幅度是多少？",
                     "options": [">5%", ">10%", ">20%"]},
                    {"id": "jump_direction", "question": "SOC变化方向？",
                     "options": ["突升", "突降", "波动"]},
                    {"id": "timing", "question": "故障发生时系统状态？",
                     "options": ["充电中", "放电中", "静置"]}
                ],
                hint="SOC跳变幅度越大，通常问题越严重",
                data_to_check=["SOC", "电池电压", "电池电流"]
            ),
            DiagnosisStep(
                step_number=2,
                title="检查BMS数据",
                instruction="检查BMS上报的关键数据是否正常",
                check_items=[
                    {"id": "voltage_normal", "question": "电池总电压是否在正常范围？",
                     "options": ["是", "否"], "correct": "是"},
                    {"id": "current_accurate", "question": "电流采样是否与实际一致？",
                     "options": ["是", "否"], "correct": "是"},
                    {"id": "temp_normal", "question": "电池温度是否正常？",
                     "options": ["是", "否"], "correct": "是"}
                ],
                hint="电流采样不准是SOC跳变的常见原因",
                data_to_check=["电池电压", "电池电流", "电池温度", "单体电压"]
            ),
            DiagnosisStep(
                step_number=3,
                title="检查SOC计算",
                instruction="检查SOC计算相关的参数和记录",
                check_items=[
                    {"id": "ah_integral", "question": "安时积分是否有累计误差？",
                     "options": ["是", "否", "不确定"]},
                    {"id": "ocv_correction", "question": "最近是否执行过OCV修正？",
                     "options": ["是", "否"]},
                    {"id": "calibration_time", "question": "上次SOC校准是什么时候？",
                     "options": ["一周内", "一月内", "超过一月", "不清楚"]}
                ],
                hint="长时间未校准SOC可能导致累计误差"
            ),
            DiagnosisStep(
                step_number=4,
                title="处理建议",
                instruction="根据以上检查，选择处理方案",
                check_items=[
                    {"id": "solution", "question": "建议的处理方案是？",
                     "options": ["执行SOC校准", "校准电流传感器",
                                "检查电池单体", "更新SOC-OCV表", "联系技术支持"]}
                ]
            )
        ],
        possible_conclusions=[
            {"id": "current_sensor_issue", "conclusion": "电流传感器零漂或故障",
             "solution": "校准或更换电流传感器"},
            {"id": "soc_drift", "conclusion": "SOC累计误差",
             "solution": "执行SOC校准程序"},
            {"id": "ocv_table_issue", "conclusion": "SOC-OCV表不准确",
             "solution": "更新SOC-OCV对照表"},
            {"id": "battery_issue", "conclusion": "电池单体异常",
             "solution": "检查并更换异常单体"}
        ],
        expected_time_minutes=15
    )

    # BMS通信中断诊断指南
    guides["DG_F002"] = DiagnosisGuide(
        id="DG_F002",
        fault_type_id="F002",
        title="BMS通信中断排查指南",
        steps=[
            DiagnosisStep(
                step_number=1,
                title="确认通信状态",
                instruction="确认通信中断的具体情况",
                check_items=[
                    {"id": "comm_status", "question": "通信中断是完全断开还是间歇性？",
                     "options": ["完全断开", "间歇性中断", "数据异常"]},
                    {"id": "affected_devices", "question": "受影响的设备范围？",
                     "options": ["单个BMS", "多个BMS", "全部BMS"]}
                ],
                hint="间歇性中断可能是干扰或接触不良"
            ),
            DiagnosisStep(
                step_number=2,
                title="检查物理连接",
                instruction="检查通信线缆和接口的物理状态",
                check_items=[
                    {"id": "cable_check", "question": "通信线缆是否牢固连接？",
                     "options": ["是", "否", "部分松动"]},
                    {"id": "indicator_light", "question": "通信指示灯状态？",
                     "options": ["正常闪烁", "常亮", "不亮", "快速闪烁"]}
                ],
                hint="先检查最简单的物理连接问题"
            ),
            DiagnosisStep(
                step_number=3,
                title="检查通信参数",
                instruction="核对通信参数配置",
                check_items=[
                    {"id": "baudrate", "question": "波特率配置是否正确？",
                     "options": ["是", "否", "不确定"]},
                    {"id": "slave_id", "question": "从站地址是否正确？",
                     "options": ["是", "否", "不确定"]}
                ],
                hint="参数不匹配会导致通信失败"
            )
        ],
        possible_conclusions=[
            {"id": "cable_issue", "conclusion": "通信线缆故障",
             "solution": "更换通信线缆"},
            {"id": "interface_issue", "conclusion": "通信接口故障",
             "solution": "检修或更换接口"},
            {"id": "config_issue", "conclusion": "通信参数配置错误",
             "solution": "校正通信参数"},
            {"id": "bms_issue", "conclusion": "BMS设备故障",
             "solution": "重启或更换BMS"}
        ],
        expected_time_minutes=10
    )

    return guides


def _init_fault_cases() -> Dict[str, FaultCase]:
    """初始化故障案例"""
    cases = {}

    cases["F001-A"] = FaultCase(
        id="F001-A",
        fault_type_id="F001",
        title="充电后SOC骤降15%",
        background="某工商业储能项目，容量500kWh，运行6个月后出现问题",
        phenomenon="充电至90%后静置30分钟，SOC显示突然跳变至75%",
        initial_data={
            "SOC_before": 90,
            "SOC_after": 75,
            "voltage": 716.8,
            "current": 0,
            "temp": 28
        },
        diagnosis_process="""
1. 首先排除通信问题 - BMS数据正常更新
2. 检查电池电压 - 总压正常但有单体电压偏低
3. 检查SOC计算 - 发现安时积分有累计误差
4. 进一步检查发现电流传感器存在零漂
        """,
        root_cause="电流传感器零漂导致安时积分累计误差",
        solution="1. 校准电流传感器\n2. 执行满充-满放SOC校准\n3. 更新SOC-OCV表",
        prevention="建议每月进行一次SOC校准，定期检查传感器状态",
        lessons_learned=[
            "SOC异常通常与电流采样相关",
            "定期校准可预防累计误差",
            "OCV修正是重要的校准手段"
        ],
        difficulty="intermediate"
    )

    cases["F001-B"] = FaultCase(
        id="F001-B",
        fault_type_id="F001",
        title="放电过程中SOC突然跳变30%",
        background="户用储能系统，容量10kWh，使用1年后",
        phenomenon="放电到60%时，SOC突然跳变至30%，系统报警停机",
        initial_data={
            "SOC_before": 60,
            "SOC_after": 30,
            "voltage": 48.2,
            "current": -20,
            "temp": 32
        },
        diagnosis_process="""
1. 检查报警记录 - 发现SOC跳变报警
2. 查看BMS单体数据 - 发现有一组单体电压明显偏低
3. 分析原因 - 该组电池容量衰减严重
4. 确认 - 该组电池SOH仅为65%
        """,
        root_cause="部分电池单体容量衰减严重，导致SOC计算不准确",
        solution="1. 更换衰减严重的电池单体\n2. 重新进行容量标定\n3. 更新SOC参数",
        prevention="定期检查电池SOH，及时发现异常单体",
        lessons_learned=[
            "单体一致性对SOC精度影响大",
            "容量衰减会导致SOC估算偏差",
            "要关注SOH变化趋势"
        ],
        difficulty="advanced"
    )

    cases["F002-A"] = FaultCase(
        id="F002-A",
        fault_type_id="F002",
        title="雷雨天气后BMS通信中断",
        background="工业储能电站，运行正常，某次雷雨天气后出现问题",
        phenomenon="雷雨过后，EMS与BMS通信完全中断，系统停机",
        initial_data={
            "comm_status": "timeout",
            "last_data_time": "14:35:22",
            "error_code": "COMM_TIMEOUT"
        },
        diagnosis_process="""
1. 检查物理连接 - 线缆完好
2. 检查通信接口 - 发现RS485接口芯片损坏
3. 分析原因 - 雷击导致浪涌损坏接口
        """,
        root_cause="雷击浪涌损坏RS485通信接口",
        solution="1. 更换RS485接口模块\n2. 加装防雷浪涌保护器",
        prevention="安装通信接口防雷保护，做好接地",
        lessons_learned=[
            "通信接口防雷很重要",
            "雷雨后要检查通信状态",
            "备件准备要充足"
        ],
        difficulty="beginner"
    )

    return cases


# =============================================================================
# 公开接口
# =============================================================================
def get_fault_types() -> Dict[str, FaultType]:
    """获取所有故障类型"""
    global _fault_types
    if _fault_types is None:
        _fault_types = _init_fault_types()
    return _fault_types


def get_fault_type(fault_id: str) -> Optional[FaultType]:
    """获取指定故障类型"""
    return get_fault_types().get(fault_id)


def get_diagnosis_guides() -> Dict[str, DiagnosisGuide]:
    """获取诊断指南"""
    global _diagnosis_guides
    if _diagnosis_guides is None:
        _diagnosis_guides = _init_diagnosis_guides()
    return _diagnosis_guides


def get_diagnosis_guide(fault_type_id: str) -> Optional[DiagnosisGuide]:
    """获取指定故障的诊断指南"""
    guide_id = f"DG_{fault_type_id}"
    return get_diagnosis_guides().get(guide_id)


def get_fault_cases() -> Dict[str, FaultCase]:
    """获取故障案例"""
    global _fault_cases
    if _fault_cases is None:
        _fault_cases = _init_fault_cases()
    return _fault_cases


def get_fault_case(case_id: str) -> Optional[FaultCase]:
    """获取指定案例"""
    return get_fault_cases().get(case_id)


def inject_fault(fault_type_id: str, fault_params: Optional[Dict[str, Any]] = None) -> FaultInstance:
    """注入故障"""
    global _active_faults, _alarm_records

    fault_type = get_fault_type(fault_type_id)
    if not fault_type:
        raise ValueError(f"未知的故障类型: {fault_type_id}")

    instance_id = f"{fault_type_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    instance = FaultInstance(
        id=instance_id,
        fault_type_id=fault_type_id,
        triggered_at=datetime.now(),
        fault_data=fault_params or {}
    )

    # 生成报警
    alarm = AlarmRecord(
        id=f"ALM_{instance_id}",
        alarm_code=fault_type_id,
        alarm_name=fault_type.name,
        severity=fault_type.severity,
        triggered_at=datetime.now(),
        trigger_value=fault_params,
        component=fault_type.category.value
    )
    _alarm_records.append(alarm)
    _active_faults[instance_id] = instance

    return instance


def clear_fault(instance_id: str) -> bool:
    """清除故障"""
    global _active_faults

    if instance_id not in _active_faults:
        return False

    instance = _active_faults[instance_id]
    instance.status = FaultStatus.CLEARED
    instance.resolved_at = datetime.now()
    del _active_faults[instance_id]
    return True


def clear_all_faults():
    """清除所有故障"""
    global _active_faults, _alarm_records
    _active_faults.clear()
    _alarm_records.clear()


def get_active_faults() -> List[FaultInstance]:
    """获取当前活动的故障"""
    return list(_active_faults.values())


def get_alarm_records() -> List[AlarmRecord]:
    """获取报警记录"""
    return _alarm_records.copy()


def acknowledge_alarm(alarm_id: str) -> bool:
    """确认报警"""
    for alarm in _alarm_records:
        if alarm.id == alarm_id:
            alarm.status = "acknowledged"
            alarm.acknowledged_at = datetime.now()
            return True
    return False


# =============================================================================
# Gradio UI组件
# =============================================================================
def create_fault_diagnosis_tab() -> Tuple[gr.Tab, Dict[str, Any]]:
    """创建故障诊断标签页

    Returns:
        Tuple[gr.Tab, Dict]: (标签页, 组件字典)
    """
    with gr.Tab("故障诊断") as tab:

        gr.Markdown("### 故障诊断训练")
        gr.Markdown("模拟储能系统故障，学习诊断和处理方法。")

        # 故障模拟器
        with gr.Group():
            gr.Markdown("#### 故障模拟器")
            with gr.Row():
                fault_type_select = gr.Dropdown(
                    label="选择故障类型",
                    choices=[
                        ("F001 - SOC异常跳变", "F001"),
                        ("F002 - BMS通信中断", "F002"),
                        ("F003 - 功率输出受限", "F003"),
                        ("F004 - 电池过温保护", "F004"),
                    ],
                    value="F001"
                )
                inject_btn = gr.Button("注入故障", variant="primary")
                clear_btn = gr.Button("清除故障")

            fault_description = gr.Markdown(
                value=_get_fault_description("F001")
            )

        with gr.Row():
            # 系统状态
            with gr.Column(scale=1):
                gr.Markdown("#### 系统状态")
                system_status = gr.Textbox(
                    label="运行状态",
                    value="正常运行",
                    interactive=False
                )
                with gr.Row():
                    current_soc = gr.Number(
                        label="当前SOC (%)",
                        value=50,
                        interactive=False
                    )
                    current_power = gr.Number(
                        label="当前功率 (kW)",
                        value=0,
                        interactive=False
                    )
                with gr.Row():
                    battery_voltage = gr.Number(
                        label="电池电压 (V)",
                        value=716.8,
                        interactive=False
                    )
                    battery_temp = gr.Number(
                        label="电池温度 (C)",
                        value=25,
                        interactive=False
                    )

            # 报警列表
            with gr.Column(scale=1):
                gr.Markdown("#### 报警列表")
                alarm_list = gr.Dataframe(
                    headers=["等级", "报警名称", "时间", "状态"],
                    value=[],
                    interactive=False
                )
                ack_btn = gr.Button("确认所有报警")

        # 排查指南
        with gr.Accordion("故障排查指南", open=True):
            guide_progress = gr.Markdown("**当前步骤**: 等待注入故障...")

            step_content = gr.Markdown(
                value="请先注入一个故障，然后按照排查指南进行诊断练习。"
            )

            # 检查项区域
            with gr.Group():
                check_radio_1 = gr.Radio(
                    label="检查项1",
                    choices=[],
                    visible=False
                )
                check_radio_2 = gr.Radio(
                    label="检查项2",
                    choices=[],
                    visible=False
                )
                check_radio_3 = gr.Radio(
                    label="检查项3",
                    choices=[],
                    visible=False
                )

            with gr.Row():
                prev_step_btn = gr.Button("上一步")
                hint_btn = gr.Button("提示")
                next_step_btn = gr.Button("下一步", variant="primary")

            hint_text = gr.Markdown("", visible=False)

        # 诊断结论
        with gr.Accordion("诊断结论", open=False):
            conclusion_select = gr.Dropdown(
                label="选择诊断结论",
                choices=[
                    "电流传感器零漂或故障",
                    "SOC累计误差",
                    "SOC-OCV表不准确",
                    "电池单体异常",
                    "通信线缆故障",
                    "通信接口故障",
                    "通信参数配置错误",
                    "其他原因"
                ],
                value=None
            )
            submit_conclusion_btn = gr.Button("提交结论", variant="primary")
            conclusion_feedback = gr.Markdown("")

        # 案例库
        with gr.Accordion("故障案例库", open=False):
            gr.Markdown("#### 相关案例")
            case_select = gr.Dropdown(
                label="选择案例",
                choices=[
                    ("F001-A: 充电后SOC骤降15%", "F001-A"),
                    ("F001-B: 放电过程中SOC突然跳变30%", "F001-B"),
                    ("F002-A: 雷雨天气后BMS通信中断", "F002-A"),
                ],
                value=None
            )
            view_case_btn = gr.Button("查看案例详情")
            case_detail = gr.Markdown("")

    components = {
        "fault_type_select": fault_type_select,
        "inject_btn": inject_btn,
        "clear_btn": clear_btn,
        "fault_description": fault_description,
        "system_status": system_status,
        "current_soc": current_soc,
        "current_power": current_power,
        "battery_voltage": battery_voltage,
        "battery_temp": battery_temp,
        "alarm_list": alarm_list,
        "ack_btn": ack_btn,
        "guide_progress": guide_progress,
        "step_content": step_content,
        "check_radio_1": check_radio_1,
        "check_radio_2": check_radio_2,
        "check_radio_3": check_radio_3,
        "prev_step_btn": prev_step_btn,
        "hint_btn": hint_btn,
        "next_step_btn": next_step_btn,
        "hint_text": hint_text,
        "conclusion_select": conclusion_select,
        "submit_conclusion_btn": submit_conclusion_btn,
        "conclusion_feedback": conclusion_feedback,
        "case_select": case_select,
        "view_case_btn": view_case_btn,
        "case_detail": case_detail,
    }

    return tab, components


def setup_fault_diagnosis_events(components: Dict[str, Any]):
    """设置故障诊断事件绑定"""

    current_step = {"value": 1}
    current_fault = {"id": None}

    def on_fault_type_change(fault_id):
        """故障类型变更"""
        return _get_fault_description(fault_id)

    def on_inject_fault(fault_id):
        """注入故障"""
        nonlocal current_fault
        clear_all_faults()
        current_step["value"] = 1

        instance = inject_fault(fault_id)
        current_fault["id"] = instance.id

        # 更新系统状态显示
        fault_type = get_fault_type(fault_id)

        # 根据故障类型设置模拟数据
        soc = 50
        power = 0
        voltage = 716.8
        temp = 25
        status = "故障"

        if fault_id == "F001":
            soc = 35  # SOC跳变
            status = "SOC异常报警"
        elif fault_id == "F002":
            status = "通信故障 - 停机"
        elif fault_id == "F003":
            power = 30  # 限功率
            status = "功率受限运行"
        elif fault_id == "F004":
            temp = 52  # 过温
            status = "过温保护 - 降功率"

        # 更新报警列表
        alarm_data = [[
            fault_type.severity.value,
            fault_type.name,
            datetime.now().strftime("%H:%M:%S"),
            "活动"
        ]]

        # 更新排查指南
        guide = get_diagnosis_guide(fault_id)
        if guide and guide.steps:
            step = guide.steps[0]
            progress = f"**当前步骤**: 1/{len(guide.steps)} - {step.title}"
            content = f"### 步骤1: {step.title}\n\n{step.instruction}"

            # 获取检查项
            choices_1 = []
            choices_2 = []
            choices_3 = []
            label_1 = ""
            label_2 = ""
            label_3 = ""

            for i, item in enumerate(step.check_items[:3]):
                choices = item.get("options", [])
                label = item.get("question", "")
                if i == 0:
                    choices_1 = choices
                    label_1 = label
                elif i == 1:
                    choices_2 = choices
                    label_2 = label
                elif i == 2:
                    choices_3 = choices
                    label_3 = label

            return (
                status, soc, power, voltage, temp,
                alarm_data, progress, content,
                gr.update(choices=choices_1, label=label_1, visible=bool(choices_1), value=None),
                gr.update(choices=choices_2, label=label_2, visible=bool(choices_2), value=None),
                gr.update(choices=choices_3, label=label_3, visible=bool(choices_3), value=None),
                gr.update(visible=False)
            )

        return (
            status, soc, power, voltage, temp,
            alarm_data, "等待注入故障...", "请注入故障",
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
            gr.update(visible=False)
        )

    def on_clear_fault():
        """清除故障"""
        nonlocal current_fault
        clear_all_faults()
        current_step["value"] = 1
        current_fault["id"] = None

        return (
            "正常运行", 50, 0, 716.8, 25,
            [], "**当前步骤**: 等待注入故障...",
            "请先注入一个故障，然后按照排查指南进行诊断练习。",
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
            gr.update(visible=False)
        )

    def on_next_step(fault_id):
        """下一步"""
        current_step["value"] += 1
        guide = get_diagnosis_guide(fault_id)

        if not guide:
            return ("无指南", "", gr.update(), gr.update(), gr.update(), gr.update())

        step_num = current_step["value"]
        if step_num > len(guide.steps):
            return (
                f"**完成**: 请在下方提交诊断结论",
                "### 诊断完成\n\n请根据排查结果，在下方选择诊断结论并提交。",
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False)
            )

        step = guide.steps[step_num - 1]
        progress = f"**当前步骤**: {step_num}/{len(guide.steps)} - {step.title}"
        content = f"### 步骤{step_num}: {step.title}\n\n{step.instruction}"

        choices_1, choices_2, choices_3 = [], [], []
        label_1, label_2, label_3 = "", "", ""

        for i, item in enumerate(step.check_items[:3]):
            choices = item.get("options", [])
            label = item.get("question", "")
            if i == 0:
                choices_1, label_1 = choices, label
            elif i == 1:
                choices_2, label_2 = choices, label
            elif i == 2:
                choices_3, label_3 = choices, label

        return (
            progress, content,
            gr.update(choices=choices_1, label=label_1, visible=bool(choices_1), value=None),
            gr.update(choices=choices_2, label=label_2, visible=bool(choices_2), value=None),
            gr.update(choices=choices_3, label=label_3, visible=bool(choices_3), value=None),
            gr.update(visible=False)
        )

    def on_prev_step(fault_id):
        """上一步"""
        if current_step["value"] > 1:
            current_step["value"] -= 1

        guide = get_diagnosis_guide(fault_id)
        if not guide:
            return ("无指南", "", gr.update(), gr.update(), gr.update(), gr.update())

        step_num = current_step["value"]
        step = guide.steps[step_num - 1]
        progress = f"**当前步骤**: {step_num}/{len(guide.steps)} - {step.title}"
        content = f"### 步骤{step_num}: {step.title}\n\n{step.instruction}"

        choices_1, choices_2, choices_3 = [], [], []
        label_1, label_2, label_3 = "", "", ""

        for i, item in enumerate(step.check_items[:3]):
            choices = item.get("options", [])
            label = item.get("question", "")
            if i == 0:
                choices_1, label_1 = choices, label
            elif i == 1:
                choices_2, label_2 = choices, label
            elif i == 2:
                choices_3, label_3 = choices, label

        return (
            progress, content,
            gr.update(choices=choices_1, label=label_1, visible=bool(choices_1), value=None),
            gr.update(choices=choices_2, label=label_2, visible=bool(choices_2), value=None),
            gr.update(choices=choices_3, label=label_3, visible=bool(choices_3), value=None),
            gr.update(visible=False)
        )

    def on_show_hint(fault_id):
        """显示提示"""
        guide = get_diagnosis_guide(fault_id)
        if not guide:
            return gr.update(value="无提示", visible=True)

        step_num = current_step["value"]
        if step_num <= len(guide.steps):
            step = guide.steps[step_num - 1]
            hint = step.hint if step.hint else "本步骤无提示"
            return gr.update(value=f"**提示**: {hint}", visible=True)

        return gr.update(value="无提示", visible=True)

    def on_submit_conclusion(conclusion, fault_id):
        """提交诊断结论"""
        guide = get_diagnosis_guide(fault_id)
        if not guide:
            return "无法评估结论"

        is_correct = False
        correct_solution = ""
        for c in guide.possible_conclusions:
            if c["conclusion"] == conclusion:
                is_correct = True
                correct_solution = c["solution"]
                break

        if is_correct:
            return f"""
### 诊断正确!

**您的结论**: {conclusion}

**解决方案**: {correct_solution}

继续保持，您已掌握此故障的诊断方法。
            """
        else:
            correct_conclusions = [c["conclusion"] for c in guide.possible_conclusions]
            return f"""
### 诊断结论不正确

**您的结论**: {conclusion}

**可能的正确结论**: {', '.join(correct_conclusions)}

建议重新检查排查步骤，注意关键数据的分析。
            """

    def on_view_case(case_id):
        """查看案例详情"""
        if not case_id:
            return "请选择一个案例"

        case = get_fault_case(case_id)
        if not case:
            return "案例不存在"

        return f"""
## {case.title}

### 背景
{case.background}

### 故障现象
{case.phenomenon}

### 故障时数据
- SOC: {case.initial_data.get('SOC_before', 'N/A')}% -> {case.initial_data.get('SOC_after', 'N/A')}%
- 电压: {case.initial_data.get('voltage', 'N/A')}V
- 温度: {case.initial_data.get('temp', 'N/A')}C

### 诊断过程
{case.diagnosis_process}

### 根本原因
{case.root_cause}

### 解决方案
{case.solution}

### 预防措施
{case.prevention}

### 经验教训
{chr(10).join(['- ' + lesson for lesson in case.lessons_learned])}
        """

    def on_ack_alarms():
        """确认所有报警"""
        for alarm in _alarm_records:
            alarm.status = "acknowledged"
            alarm.acknowledged_at = datetime.now()

        alarm_data = [[
            alarm.severity.value,
            alarm.alarm_name,
            alarm.triggered_at.strftime("%H:%M:%S"),
            "已确认"
        ] for alarm in _alarm_records]

        return alarm_data

    # 绑定事件
    components["fault_type_select"].change(
        fn=on_fault_type_change,
        inputs=[components["fault_type_select"]],
        outputs=[components["fault_description"]]
    )

    components["inject_btn"].click(
        fn=on_inject_fault,
        inputs=[components["fault_type_select"]],
        outputs=[
            components["system_status"],
            components["current_soc"],
            components["current_power"],
            components["battery_voltage"],
            components["battery_temp"],
            components["alarm_list"],
            components["guide_progress"],
            components["step_content"],
            components["check_radio_1"],
            components["check_radio_2"],
            components["check_radio_3"],
            components["hint_text"],
        ]
    )

    components["clear_btn"].click(
        fn=on_clear_fault,
        outputs=[
            components["system_status"],
            components["current_soc"],
            components["current_power"],
            components["battery_voltage"],
            components["battery_temp"],
            components["alarm_list"],
            components["guide_progress"],
            components["step_content"],
            components["check_radio_1"],
            components["check_radio_2"],
            components["check_radio_3"],
            components["hint_text"],
        ]
    )

    components["next_step_btn"].click(
        fn=on_next_step,
        inputs=[components["fault_type_select"]],
        outputs=[
            components["guide_progress"],
            components["step_content"],
            components["check_radio_1"],
            components["check_radio_2"],
            components["check_radio_3"],
            components["hint_text"],
        ]
    )

    components["prev_step_btn"].click(
        fn=on_prev_step,
        inputs=[components["fault_type_select"]],
        outputs=[
            components["guide_progress"],
            components["step_content"],
            components["check_radio_1"],
            components["check_radio_2"],
            components["check_radio_3"],
            components["hint_text"],
        ]
    )

    components["hint_btn"].click(
        fn=on_show_hint,
        inputs=[components["fault_type_select"]],
        outputs=[components["hint_text"]]
    )

    components["submit_conclusion_btn"].click(
        fn=on_submit_conclusion,
        inputs=[components["conclusion_select"], components["fault_type_select"]],
        outputs=[components["conclusion_feedback"]]
    )

    components["view_case_btn"].click(
        fn=on_view_case,
        inputs=[components["case_select"]],
        outputs=[components["case_detail"]]
    )

    components["ack_btn"].click(
        fn=on_ack_alarms,
        outputs=[components["alarm_list"]]
    )


def _get_fault_description(fault_id: str) -> str:
    """获取故障描述"""
    fault_type = get_fault_type(fault_id)
    if not fault_type:
        return "选择故障类型以查看详情"

    causes = "\n".join([f"- {c}" for c in fault_type.possible_causes[:3]])
    symptoms = "\n".join([f"- {s}" for s in fault_type.symptoms])
    objectives = "\n".join([f"- {o}" for o in fault_type.learning_objectives])

    return f"""
### {fault_type.name}

**类别**: {fault_type.category.value} | **严重程度**: {fault_type.severity.value} | **难度**: {fault_type.difficulty}

**描述**: {fault_type.description}

**可能原因**:
{causes}

**故障现象**:
{symptoms}

**学习目标**:
{objectives}
    """


# =============================================================================
# 教学元数据
# =============================================================================
FAULT_DIAGNOSIS_TEACHING_META: Dict[str, Dict[str, Any]] = {
    "fault_simulator": {
        "title": "故障模拟器",
        "help_text": "模拟各类储能系统故障，用于诊断练习",
    },
    "diagnosis_guide": {
        "title": "排查指南",
        "help_text": "提供分步骤的故障排查指引",
    },
    "case_library": {
        "title": "案例库",
        "help_text": "真实故障案例学习和复盘",
    },
}
