# -*- coding: utf-8 -*-
"""EMS架构展示模块

对应技术设计文档：07_EMS架构模块技术设计.md
展示储能系统拓扑结构、状态机、通信协议、数据流
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

import gradio as gr
import plotly.graph_objects as go


# =============================================================================
# 数据类定义
# =============================================================================
class ComponentType(Enum):
    """组件类型"""
    GRID = "电网"
    PCS = "储能变流器"
    BATTERY = "电池组"
    BMS = "电池管理系统"
    EMS = "能量管理系统"
    LOAD = "负荷"
    PV = "光伏"
    METER = "电表"
    CLOUD = "云平台"


class EMSState(Enum):
    """EMS状态"""
    STOPPED = "停机"
    INITIALIZING = "初始化"
    STANDBY = "待机"
    RUNNING = "运行"
    FAULT = "故障"
    CHARGING = "充电中"
    DISCHARGING = "放电中"
    IDLE = "空闲"


class DataType(Enum):
    """数据类型"""
    UINT16 = "UINT16"
    INT16 = "INT16"
    UINT32 = "UINT32"
    INT32 = "INT32"
    FLOAT32 = "FLOAT32"
    STRING = "STRING"


class AccessMode(Enum):
    """访问模式"""
    READ = "R"
    WRITE = "W"
    READ_WRITE = "RW"


@dataclass
class SystemComponent:
    """系统组件"""
    id: str
    name: str
    component_type: ComponentType
    position_x: float = 0.0
    position_y: float = 0.0
    description: str = ""
    functions: List[str] = field(default_factory=list)
    key_parameters: List[str] = field(default_factory=list)
    connected_to: List[str] = field(default_factory=list)
    related_knowledge: List[str] = field(default_factory=list)
    current_state: str = "normal"


@dataclass
class Connection:
    """组件连接"""
    id: str
    from_component: str
    to_component: str
    connection_type: str = "data"  # data, power, control
    protocol: str = ""
    data_direction: str = "both"  # up, down, both
    description: str = ""


@dataclass
class SystemTopology:
    """系统拓扑"""
    components: Dict[str, SystemComponent] = field(default_factory=dict)
    connections: List[Connection] = field(default_factory=list)

    def get_component(self, comp_id: str) -> Optional[SystemComponent]:
        return self.components.get(comp_id)

    def get_connections_for(self, comp_id: str) -> List[Connection]:
        return [
            c for c in self.connections
            if c.from_component == comp_id or c.to_component == comp_id
        ]


@dataclass
class StateTransition:
    """状态转换"""
    from_state: EMSState
    to_state: EMSState
    trigger: str
    action: str = ""
    description: str = ""


@dataclass
class StateMachine:
    """状态机定义"""
    states: List[EMSState] = field(default_factory=list)
    transitions: List[StateTransition] = field(default_factory=list)
    initial_state: EMSState = EMSState.STOPPED
    current_state: EMSState = EMSState.STOPPED

    def get_available_transitions(self) -> List[StateTransition]:
        """获取当前状态可用的转换"""
        return [
            t for t in self.transitions
            if t.from_state == self.current_state
        ]

    def trigger_transition(self, trigger: str) -> Optional[StateTransition]:
        """触发状态转换"""
        for t in self.transitions:
            if t.from_state == self.current_state and t.trigger == trigger:
                self.current_state = t.to_state
                return t
        return None


@dataclass
class ModbusRegister:
    """Modbus寄存器定义"""
    address: int
    name: str
    data_type: DataType = DataType.UINT16
    access_mode: AccessMode = AccessMode.READ
    unit: str = ""
    scale: float = 1.0
    description: str = ""
    value_range: str = ""
    enum_values: Dict[int, str] = field(default_factory=dict)
    importance: str = "normal"
    related_knowledge: List[str] = field(default_factory=list)


@dataclass
class ModbusProtocol:
    """Modbus协议定义"""
    slave_id: int = 1
    registers: List[ModbusRegister] = field(default_factory=list)

    def get_register(self, address: int) -> Optional[ModbusRegister]:
        for r in self.registers:
            if r.address == address:
                return r
        return None

    def get_registers_by_category(self, category: str) -> List[ModbusRegister]:
        """按类别获取寄存器"""
        categories = {
            "status": (40001, 40100),
            "control": (40101, 40200),
            "alarm": (40201, 40300),
        }
        if category not in categories:
            return self.registers
        start, end = categories[category]
        return [r for r in self.registers if start <= r.address <= end]


@dataclass
class DataFlow:
    """数据流定义"""
    id: str
    name: str
    from_component: str
    to_component: str
    direction: str  # up, down
    data_items: List[str] = field(default_factory=list)
    update_frequency: str = ""
    protocol: str = ""
    description: str = ""


# =============================================================================
# 模块状态
# =============================================================================
_system_topology: Optional[SystemTopology] = None
_state_machine: Optional[StateMachine] = None
_modbus_protocol: Optional[ModbusProtocol] = None


# =============================================================================
# 初始化函数
# =============================================================================
def _init_system_topology() -> SystemTopology:
    """初始化系统拓扑"""
    topology = SystemTopology()

    # 电网
    topology.components["grid"] = SystemComponent(
        id="grid",
        name="电网",
        component_type=ComponentType.GRID,
        position_x=0.1,
        position_y=0.5,
        description="公共电网，储能系统的能量来源和输出目标",
        functions=["供电", "接收余电"],
        connected_to=["pcs"],
        related_knowledge=["1.1"],
    )

    # PCS
    topology.components["pcs"] = SystemComponent(
        id="pcs",
        name="储能变流器 (PCS)",
        component_type=ComponentType.PCS,
        position_x=0.35,
        position_y=0.5,
        description="Power Conversion System，实现交直流转换",
        functions=["AC/DC双向转换", "功率控制", "并网/离网切换", "保护功能"],
        key_parameters=["额定功率", "转换效率", "直流电压范围", "交流电压"],
        connected_to=["grid", "battery", "ems"],
        related_knowledge=["1.1", "2.1"],
    )

    # 电池组
    topology.components["battery"] = SystemComponent(
        id="battery",
        name="电池组",
        component_type=ComponentType.BATTERY,
        position_x=0.6,
        position_y=0.5,
        description="储能电池系统，存储和释放电能",
        functions=["储存电能", "释放电能"],
        key_parameters=["容量", "电压", "电流", "温度"],
        connected_to=["pcs", "bms"],
        related_knowledge=["1.1", "1.2"],
    )

    # BMS
    topology.components["bms"] = SystemComponent(
        id="bms",
        name="电池管理系统 (BMS)",
        component_type=ComponentType.BMS,
        position_x=0.8,
        position_y=0.5,
        description="Battery Management System，监测和保护电池",
        functions=["电池状态监测", "SOC/SOH估算", "均衡管理", "安全保护"],
        key_parameters=["SOC", "SOH", "电压", "电流", "温度"],
        connected_to=["battery", "ems"],
        related_knowledge=["1.1", "1.2"],
    )

    # EMS
    topology.components["ems"] = SystemComponent(
        id="ems",
        name="能量管理系统 (EMS)",
        component_type=ComponentType.EMS,
        position_x=0.5,
        position_y=0.2,
        description="Energy Management System，统筹调度优化",
        functions=["数据采集汇总", "策略计算优化", "指令下发控制", "报警管理"],
        key_parameters=["运行模式", "功率设定", "SOC范围", "调度策略"],
        connected_to=["pcs", "bms", "meter", "cloud"],
        related_knowledge=["2.1", "2.2"],
    )

    # 电表
    topology.components["meter"] = SystemComponent(
        id="meter",
        name="电表",
        component_type=ComponentType.METER,
        position_x=0.2,
        position_y=0.2,
        description="计量电网与储能系统的电能交换",
        functions=["功率计量", "电量统计"],
        connected_to=["ems"],
        related_knowledge=["2.1"],
    )

    # 负荷
    topology.components["load"] = SystemComponent(
        id="load",
        name="负荷",
        component_type=ComponentType.LOAD,
        position_x=0.1,
        position_y=0.8,
        description="用电设备和用电需求",
        connected_to=["grid"],
        related_knowledge=["3.1", "3.2"],
    )

    # 云平台
    topology.components["cloud"] = SystemComponent(
        id="cloud",
        name="云平台/SCADA",
        component_type=ComponentType.CLOUD,
        position_x=0.8,
        position_y=0.2,
        description="远程监控和管理平台",
        functions=["远程监控", "数据存储", "策略下发"],
        connected_to=["ems"],
        related_knowledge=["2.1"],
    )

    # 定义连接
    topology.connections = [
        Connection(
            id="grid_pcs",
            from_component="grid",
            to_component="pcs",
            connection_type="power",
            description="交流电能传输"
        ),
        Connection(
            id="pcs_battery",
            from_component="pcs",
            to_component="battery",
            connection_type="power",
            description="直流电能传输"
        ),
        Connection(
            id="bms_ems",
            from_component="bms",
            to_component="ems",
            connection_type="data",
            protocol="Modbus RTU",
            data_direction="up",
            description="电池状态数据上报"
        ),
        Connection(
            id="ems_pcs",
            from_component="ems",
            to_component="pcs",
            connection_type="control",
            protocol="Modbus TCP",
            data_direction="down",
            description="功率控制指令"
        ),
        Connection(
            id="meter_ems",
            from_component="meter",
            to_component="ems",
            connection_type="data",
            protocol="Modbus RTU",
            data_direction="up",
            description="电量数据"
        ),
        Connection(
            id="ems_cloud",
            from_component="ems",
            to_component="cloud",
            connection_type="data",
            protocol="MQTT/HTTP",
            data_direction="both",
            description="远程通信"
        ),
        Connection(
            id="grid_load",
            from_component="grid",
            to_component="load",
            connection_type="power",
            description="负荷供电"
        ),
        Connection(
            id="battery_bms",
            from_component="battery",
            to_component="bms",
            connection_type="data",
            description="电池信号采集"
        ),
    ]

    return topology


def _init_state_machine() -> StateMachine:
    """初始化EMS状态机"""
    sm = StateMachine()
    sm.states = [EMSState.STOPPED, EMSState.INITIALIZING, EMSState.STANDBY,
                 EMSState.RUNNING, EMSState.FAULT]
    sm.initial_state = EMSState.STOPPED
    sm.current_state = EMSState.STOPPED

    sm.transitions = [
        StateTransition(
            from_state=EMSState.STOPPED,
            to_state=EMSState.INITIALIZING,
            trigger="上电",
            action="系统自检",
            description="系统上电后进入初始化状态"
        ),
        StateTransition(
            from_state=EMSState.INITIALIZING,
            to_state=EMSState.STANDBY,
            trigger="自检通过",
            action="进入待机",
            description="自检完成后进入待机状态"
        ),
        StateTransition(
            from_state=EMSState.INITIALIZING,
            to_state=EMSState.FAULT,
            trigger="自检失败",
            action="报警",
            description="自检发现故障"
        ),
        StateTransition(
            from_state=EMSState.STANDBY,
            to_state=EMSState.RUNNING,
            trigger="启动指令",
            action="开始运行",
            description="收到启动指令后开始运行"
        ),
        StateTransition(
            from_state=EMSState.RUNNING,
            to_state=EMSState.STANDBY,
            trigger="停止指令",
            action="停止运行",
            description="收到停止指令后回到待机"
        ),
        StateTransition(
            from_state=EMSState.RUNNING,
            to_state=EMSState.FAULT,
            trigger="故障触发",
            action="紧急停机",
            description="运行中发生故障"
        ),
        StateTransition(
            from_state=EMSState.STANDBY,
            to_state=EMSState.FAULT,
            trigger="故障触发",
            action="报警",
            description="待机时发生故障"
        ),
        StateTransition(
            from_state=EMSState.FAULT,
            to_state=EMSState.STOPPED,
            trigger="故障复位",
            action="清除报警",
            description="故障处理后复位"
        ),
        StateTransition(
            from_state=EMSState.RUNNING,
            to_state=EMSState.STOPPED,
            trigger="紧急停机",
            action="立即停机",
            description="紧急情况立即停机"
        ),
    ]

    return sm


def _init_modbus_protocol() -> ModbusProtocol:
    """初始化Modbus协议"""
    protocol = ModbusProtocol(slave_id=1)

    # 状态类寄存器 (40001-40100)
    protocol.registers.extend([
        ModbusRegister(
            address=40001,
            name="系统状态",
            data_type=DataType.UINT16,
            access_mode=AccessMode.READ,
            description="EMS运行状态",
            enum_values={0: "停机", 1: "待机", 2: "运行", 3: "故障"},
            importance="high",
        ),
        ModbusRegister(
            address=40002,
            name="实时功率",
            data_type=DataType.INT16,
            access_mode=AccessMode.READ,
            unit="kW",
            description="当前充放电功率，正值放电，负值充电",
            value_range="-500 ~ 500",
            importance="high",
        ),
        ModbusRegister(
            address=40003,
            name="当前SOC",
            data_type=DataType.UINT16,
            access_mode=AccessMode.READ,
            unit="0.1%",
            scale=0.1,
            description="电池当前SOC",
            value_range="0 ~ 1000 (代表0-100%)",
            importance="high",
        ),
        ModbusRegister(
            address=40004,
            name="电池电压",
            data_type=DataType.UINT16,
            access_mode=AccessMode.READ,
            unit="0.1V",
            scale=0.1,
            description="电池组总电压",
        ),
        ModbusRegister(
            address=40005,
            name="电池电流",
            data_type=DataType.INT16,
            access_mode=AccessMode.READ,
            unit="0.1A",
            scale=0.1,
            description="电池组电流，正值放电，负值充电",
        ),
        ModbusRegister(
            address=40006,
            name="电池温度",
            data_type=DataType.INT16,
            access_mode=AccessMode.READ,
            unit="0.1C",
            scale=0.1,
            description="电池最高温度",
        ),
    ])

    # 控制类寄存器 (40101-40200)
    protocol.registers.extend([
        ModbusRegister(
            address=40101,
            name="运行模式",
            data_type=DataType.UINT16,
            access_mode=AccessMode.READ_WRITE,
            description="EMS运行模式",
            enum_values={0: "手动", 1: "自动", 2: "远程"},
            importance="high",
        ),
        ModbusRegister(
            address=40102,
            name="功率设定",
            data_type=DataType.INT16,
            access_mode=AccessMode.READ_WRITE,
            unit="kW",
            description="目标功率设定值",
            value_range="-500 ~ 500",
            importance="high",
        ),
        ModbusRegister(
            address=40103,
            name="SOC下限",
            data_type=DataType.UINT16,
            access_mode=AccessMode.READ_WRITE,
            unit="%",
            description="允许放电的最低SOC",
            value_range="0 ~ 50",
            importance="high",
        ),
        ModbusRegister(
            address=40104,
            name="SOC上限",
            data_type=DataType.UINT16,
            access_mode=AccessMode.READ_WRITE,
            unit="%",
            description="允许充电的最高SOC",
            value_range="50 ~ 100",
            importance="high",
        ),
        ModbusRegister(
            address=40105,
            name="启停控制",
            data_type=DataType.UINT16,
            access_mode=AccessMode.READ_WRITE,
            description="系统启停指令",
            enum_values={0: "停止", 1: "启动"},
            importance="high",
        ),
    ])

    # 报警类寄存器 (40201-40300)
    protocol.registers.extend([
        ModbusRegister(
            address=40201,
            name="报警状态字1",
            data_type=DataType.UINT16,
            access_mode=AccessMode.READ,
            description="报警位状态，按位表示",
            importance="high",
        ),
        ModbusRegister(
            address=40202,
            name="报警状态字2",
            data_type=DataType.UINT16,
            access_mode=AccessMode.READ,
            description="报警位状态，按位表示",
        ),
    ])

    return protocol


# =============================================================================
# 公开接口
# =============================================================================
def get_system_topology() -> SystemTopology:
    """获取系统拓扑结构"""
    global _system_topology
    if _system_topology is None:
        _system_topology = _init_system_topology()
    return _system_topology


def get_state_machine() -> StateMachine:
    """获取EMS状态机"""
    global _state_machine
    if _state_machine is None:
        _state_machine = _init_state_machine()
    return _state_machine


def get_modbus_protocol() -> ModbusProtocol:
    """获取Modbus协议"""
    global _modbus_protocol
    if _modbus_protocol is None:
        _modbus_protocol = _init_modbus_protocol()
    return _modbus_protocol


def get_component_detail(component_id: str) -> Optional[SystemComponent]:
    """获取组件详情"""
    topology = get_system_topology()
    return topology.get_component(component_id)


def render_topology_diagram(
    highlight_component: Optional[str] = None,
    show_data_flow: bool = False,
    show_power_flow: bool = False
) -> go.Figure:
    """渲染交互式拓扑图"""
    topology = get_system_topology()
    fig = go.Figure()

    # 组件颜色映射
    color_map = {
        ComponentType.GRID: "#4CAF50",
        ComponentType.PCS: "#2196F3",
        ComponentType.BATTERY: "#FF9800",
        ComponentType.BMS: "#9C27B0",
        ComponentType.EMS: "#F44336",
        ComponentType.LOAD: "#607D8B",
        ComponentType.METER: "#795548",
        ComponentType.CLOUD: "#00BCD4",
    }

    # 绘制连接线
    for conn in topology.connections:
        from_comp = topology.components.get(conn.from_component)
        to_comp = topology.components.get(conn.to_component)
        if not from_comp or not to_comp:
            continue

        line_width = 2
        line_dash = "solid"
        if conn.connection_type == "power":
            line_color = "#FF5722"
            line_width = 3
            if not show_power_flow:
                continue
        elif conn.connection_type == "data":
            line_color = "#2196F3"
            line_dash = "dash"
            if not show_data_flow:
                continue
        elif conn.connection_type == "control":
            line_color = "#4CAF50"
            if not show_data_flow:
                continue
        else:
            line_color = "#999999"
            continue

        fig.add_trace(go.Scatter(
            x=[from_comp.position_x, to_comp.position_x],
            y=[from_comp.position_y, to_comp.position_y],
            mode="lines",
            line=dict(color=line_color, width=line_width, dash=line_dash),
            hoverinfo="text",
            hovertext=f"{conn.description}<br>协议: {conn.protocol}" if conn.protocol else conn.description,
            showlegend=False,
        ))

    # 如果没有选中流向显示，则显示所有连接
    if not show_data_flow and not show_power_flow:
        for conn in topology.connections:
            from_comp = topology.components.get(conn.from_component)
            to_comp = topology.components.get(conn.to_component)
            if not from_comp or not to_comp:
                continue

            if conn.connection_type == "power":
                line_color = "#FF5722"
                line_width = 3
                line_dash = "solid"
            elif conn.connection_type == "data":
                line_color = "#2196F3"
                line_width = 2
                line_dash = "dash"
            elif conn.connection_type == "control":
                line_color = "#4CAF50"
                line_width = 2
                line_dash = "solid"
            else:
                line_color = "#CCCCCC"
                line_width = 1
                line_dash = "dot"

            fig.add_trace(go.Scatter(
                x=[from_comp.position_x, to_comp.position_x],
                y=[from_comp.position_y, to_comp.position_y],
                mode="lines",
                line=dict(color=line_color, width=line_width, dash=line_dash),
                hoverinfo="text",
                hovertext=f"{conn.description}<br>协议: {conn.protocol}" if conn.protocol else conn.description,
                showlegend=False,
            ))

    # 绘制组件
    for comp_id, comp in topology.components.items():
        color = color_map.get(comp.component_type, "#999999")
        size = 40

        if highlight_component == comp_id:
            size = 50
            color = "#FFD700"

        fig.add_trace(go.Scatter(
            x=[comp.position_x],
            y=[comp.position_y],
            mode="markers+text",
            marker=dict(
                size=size,
                color=color,
                symbol="square",
                line=dict(width=2, color="white")
            ),
            text=[comp.name.split(" ")[0]],  # 只显示短名称
            textposition="bottom center",
            textfont=dict(size=10),
            hoverinfo="text",
            hovertext=f"<b>{comp.name}</b><br>{comp.description}",
            customdata=[comp_id],
            showlegend=False,
        ))

    fig.update_layout(
        title="储能系统架构图",
        showlegend=False,
        hovermode="closest",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.05, 1.05]
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.05, 1.05]
        ),
        height=450,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="white",
    )

    return fig


def render_state_machine_diagram(current_state: Optional[EMSState] = None) -> go.Figure:
    """渲染状态机图"""
    fig = go.Figure()

    # 状态节点位置
    states = {
        "停机": (0.1, 0.5),
        "初始化": (0.3, 0.5),
        "待机": (0.5, 0.5),
        "运行": (0.7, 0.5),
        "故障": (0.5, 0.15),
    }

    # 状态机
    sm = get_state_machine()
    current = current_state if current_state else sm.current_state

    # 绘制状态节点
    for state, (x, y) in states.items():
        is_current = (current.value == state)
        color = "#FFD700" if is_current else "#2196F3"
        size = 65 if is_current else 55

        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode="markers+text",
            marker=dict(size=size, color=color, symbol="circle",
                       line=dict(width=3 if is_current else 1, color="white")),
            text=[state],
            textposition="middle center",
            textfont=dict(color="white", size=11),
            hoverinfo="text",
            hovertext=f"状态: {state}",
            showlegend=False,
        ))

    # 绘制转换箭头（简化为线段）
    transitions = [
        ((0.1, 0.5), (0.3, 0.5), "上电"),
        ((0.3, 0.5), (0.5, 0.5), "自检通过"),
        ((0.5, 0.5), (0.7, 0.5), "启动"),
        ((0.7, 0.5), (0.5, 0.5), "停止"),
        ((0.3, 0.5), (0.5, 0.15), "自检失败"),
        ((0.5, 0.5), (0.5, 0.15), "故障"),
        ((0.7, 0.5), (0.5, 0.15), "故障"),
        ((0.5, 0.15), (0.1, 0.5), "复位"),
    ]

    for (x1, y1), (x2, y2), label in transitions:
        # 箭头线
        fig.add_annotation(
            x=x2, y=y2,
            ax=x1, ay=y1,
            xref="x", yref="y",
            axref="x", ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1.5,
            arrowcolor="#666666",
        )

    fig.update_layout(
        title="EMS状态机",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 0.85]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 0.7]),
        height=280,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="white",
    )

    return fig


def get_register_table_data(category: str = "all") -> List[List[str]]:
    """获取寄存器表数据"""
    protocol = get_modbus_protocol()

    if category == "status":
        registers = protocol.get_registers_by_category("status")
    elif category == "control":
        registers = protocol.get_registers_by_category("control")
    elif category == "alarm":
        registers = protocol.get_registers_by_category("alarm")
    else:
        registers = protocol.registers

    data = []
    for r in registers:
        enum_str = ""
        if r.enum_values:
            enum_str = " ".join([f"{k}:{v}" for k, v in r.enum_values.items()])
        desc = enum_str if enum_str else r.description

        data.append([
            str(r.address),
            r.name,
            r.data_type.value,
            r.access_mode.value,
            r.unit,
            desc
        ])

    return data


def get_data_flow_table() -> List[List[str]]:
    """获取数据流表格数据"""
    return [
        ["BMS -> EMS", "上行", "SOC/电压/电流/温度/报警", "1s", "Modbus RTU"],
        ["PCS -> EMS", "上行", "实际功率/状态/故障", "1s", "Modbus TCP"],
        ["电表 -> EMS", "上行", "电网功率/电量", "1s", "Modbus RTU"],
        ["EMS -> PCS", "下行", "功率指令/启停", "1s", "Modbus TCP"],
        ["EMS -> 云平台", "双向", "运行数据/远程指令", "1-60s", "MQTT"],
    ]


# =============================================================================
# Gradio UI组件
# =============================================================================
def create_ems_architecture_tab() -> Tuple[gr.Tab, Dict[str, Any]]:
    """创建EMS架构标签页

    Returns:
        Tuple[gr.Tab, Dict]: (标签页, 组件字典)
    """
    with gr.Tab("EMS架构") as tab:

        gr.Markdown("### EMS系统架构")
        gr.Markdown("了解储能EMS在系统中的位置、功能和工作原理。")

        # 系统拓扑图
        with gr.Group():
            gr.Markdown("#### 系统拓扑图")

            topology_plot = gr.Plot(
                value=render_topology_diagram()
            )

            with gr.Row():
                show_data_flow_cb = gr.Checkbox(
                    label="显示数据流",
                    value=False
                )
                show_power_flow_cb = gr.Checkbox(
                    label="显示电能流",
                    value=False
                )
                refresh_topology_btn = gr.Button("刷新", scale=0)

        # 组件详情
        with gr.Accordion("组件详情", open=True):
            component_select = gr.Dropdown(
                label="选择组件",
                choices=[
                    ("电网", "grid"),
                    ("储能变流器 (PCS)", "pcs"),
                    ("电池组", "battery"),
                    ("电池管理系统 (BMS)", "bms"),
                    ("能量管理系统 (EMS)", "ems"),
                    ("电表", "meter"),
                    ("负荷", "load"),
                    ("云平台/SCADA", "cloud"),
                ],
                value="ems"
            )
            component_detail = gr.Markdown(
                value=_get_component_detail_markdown("ems")
            )

        # 子模块标签
        with gr.Tabs():
            # 状态机
            with gr.Tab("状态机"):
                gr.Markdown("#### EMS状态机")
                state_machine_plot = gr.Plot(
                    value=render_state_machine_diagram()
                )
                with gr.Row():
                    current_state_display = gr.Textbox(
                        label="当前状态",
                        value="停机",
                        interactive=False,
                        scale=1
                    )
                    trigger_select = gr.Dropdown(
                        label="触发事件",
                        choices=["上电", "自检通过", "自检失败", "启动指令",
                                "停止指令", "故障触发", "故障复位", "紧急停机"],
                        value="上电",
                        scale=1
                    )
                    trigger_btn = gr.Button("触发", scale=0)
                transition_log = gr.Textbox(
                    label="转换日志",
                    lines=3,
                    interactive=False
                )

            # 通信协议
            with gr.Tab("通信协议"):
                gr.Markdown("#### Modbus寄存器表")
                with gr.Row():
                    register_category = gr.Dropdown(
                        label="类别筛选",
                        choices=[
                            ("全部", "all"),
                            ("状态类", "status"),
                            ("控制类", "control"),
                            ("报警类", "alarm")
                        ],
                        value="all"
                    )
                register_table = gr.Dataframe(
                    headers=["地址", "名称", "类型", "读写", "单位", "说明"],
                    value=get_register_table_data("all"),
                    interactive=False
                )

            # 数据流
            with gr.Tab("数据流"):
                gr.Markdown("#### 数据流向")
                data_flow_table = gr.Dataframe(
                    headers=["数据流", "方向", "内容", "频率", "协议"],
                    value=get_data_flow_table(),
                    interactive=False
                )

                gr.Markdown("""
**图例说明：**
- **上行**: 数据从设备采集到EMS
- **下行**: EMS下发控制指令到设备
- **双向**: 数据和指令双向通信
                """)

    components = {
        "topology_plot": topology_plot,
        "show_data_flow": show_data_flow_cb,
        "show_power_flow": show_power_flow_cb,
        "refresh_topology": refresh_topology_btn,
        "component_select": component_select,
        "component_detail": component_detail,
        "state_machine_plot": state_machine_plot,
        "current_state": current_state_display,
        "trigger_select": trigger_select,
        "trigger_btn": trigger_btn,
        "transition_log": transition_log,
        "register_category": register_category,
        "register_table": register_table,
    }

    return tab, components


def setup_ems_architecture_events(components: Dict[str, Any]):
    """设置EMS架构事件绑定"""

    # 状态机状态（使用闭包保存）
    state_log = []

    def update_topology(show_data, show_power):
        """更新拓扑图"""
        return render_topology_diagram(
            show_data_flow=show_data,
            show_power_flow=show_power
        )

    def on_component_select(comp_id):
        """组件选择"""
        return _get_component_detail_markdown(comp_id)

    def on_trigger_click(trigger):
        """触发状态转换"""
        nonlocal state_log
        sm = get_state_machine()
        old_state = sm.current_state.value
        transition = sm.trigger_transition(trigger)

        if transition:
            new_state = sm.current_state.value
            log_entry = f"[{old_state}] --({trigger})--> [{new_state}] : {transition.action}"
            state_log.append(log_entry)
            if len(state_log) > 10:
                state_log = state_log[-10:]

            return (
                render_state_machine_diagram(sm.current_state),
                new_state,
                "\n".join(state_log)
            )
        else:
            log_entry = f"[{old_state}] 无法响应触发: {trigger}"
            state_log.append(log_entry)
            if len(state_log) > 10:
                state_log = state_log[-10:]
            return (
                render_state_machine_diagram(sm.current_state),
                old_state,
                "\n".join(state_log)
            )

    def on_register_category_change(category):
        """寄存器类别筛选"""
        return get_register_table_data(category)

    # 绑定拓扑图更新
    components["show_data_flow"].change(
        fn=update_topology,
        inputs=[components["show_data_flow"], components["show_power_flow"]],
        outputs=[components["topology_plot"]]
    )
    components["show_power_flow"].change(
        fn=update_topology,
        inputs=[components["show_data_flow"], components["show_power_flow"]],
        outputs=[components["topology_plot"]]
    )
    components["refresh_topology"].click(
        fn=update_topology,
        inputs=[components["show_data_flow"], components["show_power_flow"]],
        outputs=[components["topology_plot"]]
    )

    # 绑定组件详情
    components["component_select"].change(
        fn=on_component_select,
        inputs=[components["component_select"]],
        outputs=[components["component_detail"]]
    )

    # 绑定状态机触发
    components["trigger_btn"].click(
        fn=on_trigger_click,
        inputs=[components["trigger_select"]],
        outputs=[
            components["state_machine_plot"],
            components["current_state"],
            components["transition_log"]
        ]
    )

    # 绑定寄存器筛选
    components["register_category"].change(
        fn=on_register_category_change,
        inputs=[components["register_category"]],
        outputs=[components["register_table"]]
    )


def _get_component_detail_markdown(comp_id: str) -> str:
    """获取组件详情Markdown"""
    comp = get_component_detail(comp_id)
    if not comp:
        return "请选择组件"

    md = f"## {comp.name}\n\n"
    md += f"*{comp.description}*\n\n"

    if comp.functions:
        md += "**主要功能：**\n"
        for func in comp.functions:
            md += f"- {func}\n"
        md += "\n"

    if comp.key_parameters:
        md += "**关键参数：**\n"
        md += ", ".join(comp.key_parameters) + "\n\n"

    if comp.connected_to:
        topology = get_system_topology()
        connected_names = []
        for cid in comp.connected_to:
            c = topology.get_component(cid)
            if c:
                connected_names.append(c.name.split(" ")[0])
        if connected_names:
            md += f"**连接设备**: {', '.join(connected_names)}\n"

    return md


# =============================================================================
# 教学元数据
# =============================================================================
EMS_ARCHITECTURE_TEACHING_META: Dict[str, Dict[str, Any]] = {
    "topology": {
        "title": "系统拓扑",
        "help_text": "展示储能系统各组件及其连接关系",
    },
    "state_machine": {
        "title": "状态机",
        "help_text": "展示EMS运行状态及转换逻辑",
    },
    "modbus": {
        "title": "通信协议",
        "help_text": "展示Modbus寄存器定义",
    },
}
