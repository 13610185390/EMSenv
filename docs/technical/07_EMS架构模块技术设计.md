# EMS架构展示模块技术设计文档

> 模块名称：ems_architecture
> 版本：v0.1
> 日期：2026-01-08

---

## 1. 模块概述

### 1.1 功能描述
EMS架构展示模块用于帮助学员理解储能EMS在系统中的位置、功能和工作原理，通过交互式拓扑图、状态机演示、通信协议展示等方式进行直观教学。

### 1.2 模块职责
- 展示储能系统拓扑结构（交互式）
- 演示EMS状态机转换
- 展示数据流向和通信链路
- 展示Modbus寄存器表
- 提供组件详情查看
- 支持动画演示工作流程

### 1.3 依赖关系
```
ems_architecture.py
    ├── config/ems_config.py        # EMS配置数据
    ├── models/ems_model.py         # EMS相关数据模型
    ├── utils/animation.py          # 动画工具
    └── modules/learning_center.py  # 关联知识点
```

---

## 2. 数据结构定义

### 2.1 系统组件数据类

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


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
    # 🔲 扩展预留
    EXT_COMPONENT_1 = "_扩展组件1"


@dataclass
class SystemComponent:
    """系统组件"""

    id: str
    name: str
    component_type: ComponentType

    # 位置（用于拓扑图绘制）
    position_x: float = 0.0
    position_y: float = 0.0

    # 描述信息
    description: str = ""
    functions: List[str] = field(default_factory=list)
    key_parameters: List[str] = field(default_factory=list)

    # 关联
    connected_to: List[str] = field(default_factory=list)  # 连接的组件ID
    related_knowledge: List[str] = field(default_factory=list)

    # 状态（用于动画）
    current_state: str = "normal"

    # 🔲 扩展预留
    ext_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Connection:
    """组件连接"""

    id: str
    from_component: str             # 起始组件ID
    to_component: str               # 目标组件ID
    connection_type: str = "data"   # data, power, control
    protocol: str = ""              # 通信协议
    data_direction: str = "both"    # up, down, both
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
```

### 2.2 状态机数据类

```python
class EMSState(Enum):
    """EMS状态"""
    STOPPED = "停机"
    INITIALIZING = "初始化"
    STANDBY = "待机"
    RUNNING = "运行"
    FAULT = "故障"
    # 运行子状态
    CHARGING = "充电中"
    DISCHARGING = "放电中"
    IDLE = "空闲"


@dataclass
class StateTransition:
    """状态转换"""

    from_state: EMSState
    to_state: EMSState
    trigger: str                    # 触发条件
    action: str = ""                # 执行动作
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

    def trigger_transition(self, trigger: str) -> bool:
        """触发状态转换"""
        for t in self.transitions:
            if t.from_state == self.current_state and t.trigger == trigger:
                self.current_state = t.to_state
                return True
        return False
```

### 2.3 通信协议数据类

```python
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
class ModbusRegister:
    """Modbus寄存器定义"""

    address: int                    # 寄存器地址
    name: str                       # 参数名称
    data_type: DataType = DataType.UINT16
    access_mode: AccessMode = AccessMode.READ
    unit: str = ""                  # 单位
    scale: float = 1.0              # 缩放系数
    description: str = ""
    value_range: str = ""           # 取值范围说明
    enum_values: Dict[int, str] = field(default_factory=dict)  # 枚举值映射

    # 教学相关
    importance: str = "normal"      # high, normal, low
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
        """按类别获取寄存器（根据地址范围）"""
        categories = {
            "status": (40001, 40100),    # 状态类
            "measurement": (40101, 40200), # 测量类
            "control": (40201, 40300),   # 控制类
            "config": (40301, 40400),    # 配置类
        }
        if category not in categories:
            return []
        start, end = categories[category]
        return [r for r in self.registers if start <= r.address <= end]
```

### 2.4 数据流数据类

```python
@dataclass
class DataFlow:
    """数据流定义"""

    id: str
    name: str
    from_component: str
    to_component: str
    direction: str                  # up, down
    data_items: List[str] = field(default_factory=list)
    update_frequency: str = ""      # 如 "1s", "100ms"
    protocol: str = ""
    description: str = ""


@dataclass
class DataFlowDiagram:
    """数据流图"""

    flows: List[DataFlow] = field(default_factory=list)

    def get_flows_for_component(self, comp_id: str) -> Dict[str, List[DataFlow]]:
        """获取组件相关的数据流"""
        incoming = [f for f in self.flows if f.to_component == comp_id]
        outgoing = [f for f in self.flows if f.from_component == comp_id]
        return {"incoming": incoming, "outgoing": outgoing}
```

---

## 3. 接口设计

### 3.1 模块公开接口

```python
# ems_architecture.py 公开接口

def create_ems_architecture_tab() -> gr.Tab:
    """
    创建EMS架构标签页

    Returns:
        gr.Tab: Gradio标签页组件
    """
    pass


# === 拓扑图 ===
def get_system_topology() -> SystemTopology:
    """获取系统拓扑结构"""
    pass


def get_component_detail(component_id: str) -> Optional[SystemComponent]:
    """获取组件详情"""
    pass


def render_topology_diagram(
    highlight_component: Optional[str] = None,
    show_data_flow: bool = False,
    show_power_flow: bool = False,
    animation_mode: Optional[str] = None
) -> Any:
    """
    渲染拓扑图

    Args:
        highlight_component: 高亮的组件ID
        show_data_flow: 显示数据流向
        show_power_flow: 显示电能流向
        animation_mode: 动画模式 (charging, discharging, standby)

    Returns:
        Plotly图表或HTML
    """
    pass


# === 状态机 ===
def get_state_machine() -> StateMachine:
    """获取EMS状态机定义"""
    pass


def render_state_machine_diagram(
    current_state: Optional[EMSState] = None
) -> Any:
    """渲染状态机图"""
    pass


def simulate_state_transition(trigger: str) -> Dict[str, Any]:
    """
    模拟状态转换

    Returns:
        dict: {
            'success': bool,
            'from_state': str,
            'to_state': str,
            'action': str
        }
    """
    pass


# === 通信协议 ===
def get_modbus_protocol() -> ModbusProtocol:
    """获取Modbus协议定义"""
    pass


def get_register_detail(address: int) -> Optional[ModbusRegister]:
    """获取寄存器详情"""
    pass


def render_register_table(
    category: Optional[str] = None,
    search_query: Optional[str] = None
) -> List[List[str]]:
    """
    渲染寄存器表格

    Returns:
        List[List[str]]: 表格数据
    """
    pass


# === 数据流 ===
def get_data_flow_diagram() -> DataFlowDiagram:
    """获取数据流图"""
    pass


def render_data_flow(component_id: Optional[str] = None) -> Any:
    """渲染数据流图"""
    pass


# 🔲 扩展接口预留
def register_custom_component(component: SystemComponent) -> bool:
    """注册自定义组件"""
    pass
```

---

## 4. 核心逻辑

### 4.1 系统拓扑初始化

```python
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
        functions=[
            "AC/DC双向转换",
            "功率控制",
            "并网/离网切换",
            "保护功能"
        ],
        key_parameters=[
            "额定功率",
            "转换效率",
            "直流电压范围",
            "交流电压"
        ],
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
        functions=[
            "电池状态监测",
            "SOC/SOH估算",
            "均衡管理",
            "安全保护"
        ],
        key_parameters=["SOC", "SOH", "电压", "电流", "温度"],
        connected_to=["battery", "ems"],
        related_knowledge=["1.1", "1.2", "5.1"],
    )

    # EMS
    topology.components["ems"] = SystemComponent(
        id="ems",
        name="能量管理系统 (EMS)",
        component_type=ComponentType.EMS,
        position_x=0.5,
        position_y=0.2,
        description="Energy Management System，统筹调度优化",
        functions=[
            "数据采集汇总",
            "策略计算优化",
            "指令下发控制",
            "报警管理"
        ],
        key_parameters=["运行模式", "功率设定", "SOC范围", "调度策略"],
        connected_to=["pcs", "bms", "meter", "cloud"],
        related_knowledge=["2.1", "2.2", "2.3", "2.4"],
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
        position_x=0.5,
        position_y=0.05,
        description="远程监控和管理平台",
        functions=["远程监控", "数据存储", "策略下发"],
        connected_to=["ems"],
        related_knowledge=["2.1", "6.3"],
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
    ]

    return topology
```

### 4.2 状态机初始化

```python
def _init_state_machine() -> StateMachine:
    """初始化EMS状态机"""

    sm = StateMachine()
    sm.states = list(EMSState)
    sm.initial_state = EMSState.STOPPED
    sm.current_state = EMSState.STOPPED

    sm.transitions = [
        # 停机 -> 初始化
        StateTransition(
            from_state=EMSState.STOPPED,
            to_state=EMSState.INITIALIZING,
            trigger="上电",
            action="系统自检",
            description="系统上电后进入初始化状态"
        ),
        # 初始化 -> 待机
        StateTransition(
            from_state=EMSState.INITIALIZING,
            to_state=EMSState.STANDBY,
            trigger="自检通过",
            action="进入待机",
            description="自检完成后进入待机状态"
        ),
        # 初始化 -> 故障
        StateTransition(
            from_state=EMSState.INITIALIZING,
            to_state=EMSState.FAULT,
            trigger="自检失败",
            action="报警",
            description="自检发现故障"
        ),
        # 待机 -> 运行
        StateTransition(
            from_state=EMSState.STANDBY,
            to_state=EMSState.RUNNING,
            trigger="启动指令",
            action="开始运行",
            description="收到启动指令后开始运行"
        ),
        # 运行 -> 待机
        StateTransition(
            from_state=EMSState.RUNNING,
            to_state=EMSState.STANDBY,
            trigger="停止指令",
            action="停止运行",
            description="收到停止指令后回到待机"
        ),
        # 运行 -> 故障
        StateTransition(
            from_state=EMSState.RUNNING,
            to_state=EMSState.FAULT,
            trigger="故障触发",
            action="紧急停机",
            description="运行中发生故障"
        ),
        # 待机 -> 故障
        StateTransition(
            from_state=EMSState.STANDBY,
            to_state=EMSState.FAULT,
            trigger="故障触发",
            action="报警",
            description="待机时发生故障"
        ),
        # 故障 -> 停机
        StateTransition(
            from_state=EMSState.FAULT,
            to_state=EMSState.STOPPED,
            trigger="故障复位",
            action="清除报警",
            description="故障处理后复位"
        ),
        # 任意状态 -> 停机（紧急停机）
        StateTransition(
            from_state=EMSState.RUNNING,
            to_state=EMSState.STOPPED,
            trigger="紧急停机",
            action="立即停机",
            description="紧急情况立即停机"
        ),
    ]

    return sm
```

### 4.3 Modbus协议初始化

```python
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
            related_knowledge=["2.1"],
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
            related_knowledge=["2.2"],
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
            related_knowledge=["1.2"],
        ),
        ModbusRegister(
            address=40004,
            name="电池电压",
            data_type=DataType.UINT16,
            access_mode=AccessMode.READ,
            unit="0.1V",
            scale=0.1,
            description="电池组总电压",
            importance="normal",
        ),
        ModbusRegister(
            address=40005,
            name="电池电流",
            data_type=DataType.INT16,
            access_mode=AccessMode.READ,
            unit="0.1A",
            scale=0.1,
            description="电池组电流，正值放电，负值充电",
            importance="normal",
        ),
        ModbusRegister(
            address=40006,
            name="电池温度",
            data_type=DataType.INT16,
            access_mode=AccessMode.READ,
            unit="0.1℃",
            scale=0.1,
            description="电池最高温度",
            importance="normal",
            related_knowledge=["1.4"],
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
            related_knowledge=["2.2"],
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
            related_knowledge=["4.1"],
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
            related_knowledge=["4.2"],
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
            related_knowledge=["4.2"],
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
            related_knowledge=["5.1"],
        ),
        ModbusRegister(
            address=40202,
            name="报警状态字2",
            data_type=DataType.UINT16,
            access_mode=AccessMode.READ,
            description="报警位状态，按位表示",
            importance="normal",
        ),
    ])

    return protocol
```

### 4.4 拓扑图渲染

```python
import plotly.graph_objects as go


def render_topology_diagram(
    highlight_component: Optional[str] = None,
    show_data_flow: bool = False,
    show_power_flow: bool = False,
    animation_mode: Optional[str] = None
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

        line_color = "#999999"
        line_dash = "solid"
        if conn.connection_type == "power":
            line_color = "#FF5722"
            line_width = 3
        elif conn.connection_type == "data":
            line_color = "#2196F3"
            line_width = 2
            line_dash = "dash"
        elif conn.connection_type == "control":
            line_color = "#4CAF50"
            line_width = 2

        # 动画效果
        if show_data_flow and conn.connection_type == "data":
            # 添加数据流动画（用散点模拟）
            pass

        fig.add_trace(go.Scatter(
            x=[from_comp.position_x, to_comp.position_x],
            y=[from_comp.position_y, to_comp.position_y],
            mode="lines",
            line=dict(color=line_color, width=line_width, dash=line_dash),
            hoverinfo="text",
            hovertext=f"{conn.description}<br>协议: {conn.protocol}",
            showlegend=False,
        ))

    # 绘制组件
    for comp_id, comp in topology.components.items():
        color = color_map.get(comp.component_type, "#999999")
        size = 40

        # 高亮组件
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
            text=[comp.name],
            textposition="bottom center",
            hoverinfo="text",
            hovertext=f"<b>{comp.name}</b><br>{comp.description}",
            customdata=[comp_id],
            showlegend=False,
        ))

    # 布局设置
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
        height=500,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="white",
    )

    return fig
```

---

## 5. UI组件设计

### 5.1 EMS架构主页面

```python
def create_ems_architecture_tab() -> gr.Tab:
    """创建EMS架构标签页"""

    with gr.Tab("EMS架构") as tab:

        # 系统拓扑图
        with gr.Group():
            gr.Markdown("### 系统拓扑图")
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
                animation_dropdown = gr.Dropdown(
                    label="动画演示",
                    choices=["无", "充电过程", "放电过程", "待机状态"],
                    value="无"
                )
                play_animation_btn = gr.Button("播放")

        # 组件详情
        with gr.Accordion("组件详情", open=False):
            component_select = gr.Dropdown(
                label="选择组件",
                choices=[
                    "电网", "储能变流器(PCS)", "电池组",
                    "电池管理系统(BMS)", "能量管理系统(EMS)"
                ],
                value="能量管理系统(EMS)"
            )
            component_detail = gr.Markdown("""
**能量管理系统 (EMS)**

Energy Management System，储能系统的"大脑"

**主要功能：**
- 数据采集汇总
- 策略计算优化
- 指令下发控制
- 报警管理

**关键参数：**
运行模式、功率设定、SOC范围、调度策略
            """)

        # 子模块标签
        with gr.Tabs():
            # 通信协议
            with gr.Tab("通信协议"):
                gr.Markdown("### Modbus寄存器表")
                with gr.Row():
                    register_category = gr.Dropdown(
                        label="类别筛选",
                        choices=["全部", "状态类", "控制类", "报警类"],
                        value="全部"
                    )
                    register_search = gr.Textbox(
                        label="搜索",
                        placeholder="输入寄存器名称或地址..."
                    )
                register_table = gr.Dataframe(
                    headers=["地址", "名称", "类型", "读写", "单位", "说明"],
                    value=[
                        ["40001", "系统状态", "UINT16", "R", "-", "0:停机 1:待机 2:运行 3:故障"],
                        ["40002", "实时功率", "INT16", "R", "kW", "正:放电 负:充电"],
                        ["40003", "当前SOC", "UINT16", "R", "0.1%", "范围0-1000"],
                        ["40102", "功率设定", "INT16", "RW", "kW", "目标功率"],
                        ["40103", "SOC下限", "UINT16", "RW", "%", "放电截止SOC"],
                    ],
                    interactive=False
                )

            # 状态机
            with gr.Tab("状态机"):
                gr.Markdown("### EMS状态机")
                state_machine_plot = gr.Plot(
                    value=_render_state_machine_figure()
                )
                with gr.Row():
                    current_state_display = gr.Textbox(
                        label="当前状态",
                        value="停机",
                        interactive=False
                    )
                    trigger_select = gr.Dropdown(
                        label="触发事件",
                        choices=["上电", "自检通过", "启动指令", "停止指令", "故障触发", "故障复位"],
                        value="上电"
                    )
                    trigger_btn = gr.Button("触发")
                transition_log = gr.Textbox(
                    label="转换日志",
                    lines=3,
                    interactive=False
                )

            # 数据流
            with gr.Tab("数据流"):
                gr.Markdown("### 数据流向图")
                data_flow_table = gr.Dataframe(
                    headers=["数据流", "方向", "内容", "频率", "协议"],
                    value=[
                        ["BMS → EMS", "上行", "SOC/电压/电流/温度/报警", "1s", "Modbus RTU"],
                        ["PCS → EMS", "上行", "实际功率/状态/故障", "1s", "Modbus TCP"],
                        ["电表 → EMS", "上行", "电网功率/电量", "1s", "Modbus RTU"],
                        ["EMS → PCS", "下行", "功率指令/启停", "1s", "Modbus TCP"],
                        ["EMS → 云平台", "上行", "运行数据/统计", "1-60s", "MQTT"],
                    ],
                    interactive=False
                )

    return tab, {
        "topology_plot": topology_plot,
        "component_detail": component_detail,
        "register_table": register_table,
        "state_machine_plot": state_machine_plot,
        "current_state": current_state_display,
    }


def _render_state_machine_figure() -> go.Figure:
    """渲染状态机图"""
    # 使用Plotly绘制状态机图
    # 简化实现，实际可使用更复杂的图形库
    fig = go.Figure()

    # 状态节点位置
    states = {
        "停机": (0.1, 0.5),
        "初始化": (0.3, 0.5),
        "待机": (0.5, 0.5),
        "运行": (0.7, 0.5),
        "故障": (0.5, 0.2),
    }

    # 绘制状态节点
    for state, (x, y) in states.items():
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode="markers+text",
            marker=dict(size=60, color="#2196F3", symbol="circle"),
            text=[state],
            textposition="middle center",
            textfont=dict(color="white", size=12),
            hoverinfo="none",
            showlegend=False,
        ))

    fig.update_layout(
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
    )

    return fig
```

---

## 6. 文件结构

```
modules/
├── __init__.py
├── ems_architecture.py          # 本模块主文件
└── _ext_modules/
    └── __init__.py

models/
├── __init__.py
├── ems_model.py                 # EMS相关数据模型
└── _ext_models/
    └── __init__.py

config/
├── __init__.py
├── ems_config.py                # EMS配置
├── modbus_registers.json        # 寄存器表配置
└── topology.json                # 拓扑配置

utils/
├── __init__.py
├── animation.py                 # 动画工具
└── _ext_utils/
    └── __init__.py
```

---

## 7. 扩展预留

### 7.1 其他通信协议（预留）

```python
# 🔲 CAN协议支持（预留）
@dataclass
class CANMessage:
    """CAN报文定义"""
    can_id: int
    name: str
    dlc: int = 8
    signals: List[Dict] = field(default_factory=list)
```

### 7.2 实时数据模拟（预留）

```python
# 🔲 实时数据模拟（预留）
class EMSSimulator:
    """EMS实时模拟器"""

    def start(self):
        """启动模拟"""
        raise NotImplementedError()

    def get_current_data(self) -> Dict[str, Any]:
        """获取当前模拟数据"""
        raise NotImplementedError()
```

---

## 修改记录

| 版本 | 日期 | 修改内容 | 修改人 |
|------|------|----------|--------|
| v0.1 | 2026-01-08 | 初稿 | Claude |
