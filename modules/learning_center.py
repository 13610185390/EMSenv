# -*- coding: utf-8 -*-
"""教学引导模块

对应技术设计文档：06_教学引导模块技术设计.md
提供知识地图、学习进度、术语查询、案例库等教学功能
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

import gradio as gr


# =============================================================================
# 数据类定义
# =============================================================================
class KnowledgeLevel(Enum):
    """知识点难度等级"""
    BEGINNER = "入门"
    INTERMEDIATE = "进阶"
    ADVANCED = "高级"


@dataclass
class KnowledgePoint:
    """知识点数据类"""
    id: str
    title: str
    parent_id: Optional[str] = None
    level: KnowledgeLevel = KnowledgeLevel.BEGINNER
    summary: str = ""
    content: str = ""
    related_params: List[str] = field(default_factory=list)
    related_modules: List[str] = field(default_factory=list)
    learning_time_minutes: int = 5
    keywords: List[str] = field(default_factory=list)


@dataclass
class Terminology:
    """术语数据类"""
    term: str
    english: str = ""
    abbreviation: str = ""
    definition: str = ""
    explanation: str = ""
    related_terms: List[str] = field(default_factory=list)
    example: str = ""


# =============================================================================
# 知识库初始化
# =============================================================================
def _init_knowledge_tree() -> Dict[str, KnowledgePoint]:
    """初始化知识树"""
    nodes = {}

    # 1. 储能基础
    nodes["1"] = KnowledgePoint(
        id="1",
        title="储能基础",
        level=KnowledgeLevel.BEGINNER,
        summary="储能系统的基本概念和组成",
    )

    nodes["1.1"] = KnowledgePoint(
        id="1.1",
        parent_id="1",
        title="储能系统组成",
        summary="了解BMS、PCS、EMS的功能和关系",
        content="""
# 储能系统组成

储能系统主要由以下三大核心部件组成：

## 1. BMS (电池管理系统)
- **功能**: 监测电池状态、保护电池安全
- **采集数据**: 电压、电流、温度、SOC、SOH
- **保护功能**: 过充、过放、过流、过温保护

## 2. PCS (储能变流器)
- **功能**: 实现交直流转换
- **工作模式**: 充电模式（AC→DC）、放电模式（DC→AC）
- **控制方式**: 接收EMS指令，执行功率控制

## 3. EMS (能量管理系统)
- **功能**: 统筹调度，优化运行
- **主要任务**: 数据采集、策略计算、指令下发
- **优化目标**: 经济性、安全性、效率
        """,
        related_params=["capacity", "power_rated"],
        related_modules=["ems_architecture"],
        learning_time_minutes=10,
        keywords=["BMS", "PCS", "EMS", "储能系统"],
    )

    nodes["1.2"] = KnowledgePoint(
        id="1.2",
        parent_id="1",
        title="电池基础知识",
        summary="SOC、SOH、DOD等核心概念",
        content="""
# 电池基础知识

## SOC (State of Charge) - 荷电状态
- **定义**: 电池剩余电量占总容量的百分比
- **范围**: 0% - 100%
- **计算方法**: 安时积分法、OCV法、卡尔曼滤波
- **实际应用**: 决定可充/可放电量

## SOH (State of Health) - 健康状态
- **定义**: 电池当前容量与初始容量的比值
- **衰减原因**: 循环老化、日历老化
- **典型值**: 新电池100%，寿命终止通常为80%

## DOD (Depth of Discharge) - 放电深度
- **定义**: 单次放电量占总容量的百分比
- **与SOC关系**: DOD = 100% - SOC（放电结束时）
- **影响**: DOD越大，循环寿命越短
        """,
        related_params=["soc_min", "soc_max", "soc_init", "cycle_life"],
        learning_time_minutes=15,
        keywords=["SOC", "SOH", "DOD", "荷电状态"],
    )

    nodes["1.3"] = KnowledgePoint(
        id="1.3",
        parent_id="1",
        title="电池类型对比",
        summary="磷酸铁锂vs三元锂电池特性",
        content="""
# 电池类型对比

## 磷酸铁锂 (LFP)
- **优点**: 安全性高、循环寿命长、成本较低
- **缺点**: 能量密度较低、低温性能一般
- **典型应用**: 储能电站、电动大巴

## 三元锂 (NCM/NCA)
- **优点**: 能量密度高、低温性能好
- **缺点**: 安全性相对较低、成本高
- **典型应用**: 电动乘用车、便携设备

## 对比表
| 指标 | 磷酸铁锂 | 三元锂 |
|------|----------|--------|
| 循环寿命 | 4000-6000次 | 1500-2000次 |
| 能量密度 | 120-160Wh/kg | 200-300Wh/kg |
| 安全性 | 高 | 中 |
        """,
        related_params=["battery_type"],
        learning_time_minutes=10,
        keywords=["磷酸铁锂", "三元锂", "LFP", "NCM"],
    )

    # 2. EMS功能
    nodes["2"] = KnowledgePoint(
        id="2",
        title="EMS功能",
        level=KnowledgeLevel.INTERMEDIATE,
        summary="能量管理系统的核心功能",
    )

    nodes["2.1"] = KnowledgePoint(
        id="2.1",
        parent_id="2",
        title="数据采集与监控",
        summary="EMS如何采集和处理系统数据",
        content="""
# 数据采集与监控

## 采集数据类型
1. **电池数据** (来自BMS)
   - SOC、SOH
   - 电压、电流、温度
   - 报警状态

2. **变流器数据** (来自PCS)
   - 实际功率
   - 运行状态
   - 故障信息

3. **电网数据** (来自电表)
   - 电网功率
   - 电量统计

## 通信协议
- Modbus RTU/TCP
- CAN总线
- IEC 61850
        """,
        related_modules=["ems_architecture"],
        learning_time_minutes=15,
        keywords=["数据采集", "Modbus", "通信"],
    )

    nodes["2.2"] = KnowledgePoint(
        id="2.2",
        parent_id="2",
        title="调度策略",
        summary="峰谷套利、负荷跟踪等策略",
        content="""
# 调度策略

## 峰谷套利
- **原理**: 谷时低价充电，峰时高价放电
- **收益来源**: 峰谷电价差
- **适用场景**: 峰谷价差大的地区

## 负荷跟踪
- **原理**: 削峰填谷，平滑负荷曲线
- **目标**: 降低最大需量
- **适用场景**: 两部制电价用户

## 新能源消纳
- **原理**: 储存光伏/风电余电
- **目标**: 提高自发自用率
- **适用场景**: 光储/风储系统
        """,
        related_params=["dispatch_mode"],
        related_modules=["control_params"],
        learning_time_minutes=20,
        keywords=["峰谷套利", "负荷跟踪", "调度"],
    )

    # 3. 经济分析
    nodes["3"] = KnowledgePoint(
        id="3",
        title="经济分析",
        level=KnowledgeLevel.INTERMEDIATE,
        summary="储能项目经济性评估",
    )

    nodes["3.1"] = KnowledgePoint(
        id="3.1",
        parent_id="3",
        title="投资成本构成",
        summary="储能系统的成本组成",
        content="""
# 投资成本构成

## 初始投资
1. **电池成本** (约60-70%)
   - 单价: 1000-1500元/kWh
   - 总成本 = 容量 × 单价

2. **PCS成本** (约15-20%)
   - 单价: 300-500元/kW
   - 总成本 = 功率 × 单价

3. **其他成本** (约10-20%)
   - 安装调试
   - 土建配套
   - 管理系统

## 运营成本
- 运维成本: 初始投资的1-2%/年
- 电损成本: 往返效率损耗
        """,
        related_params=["cost_per_kwh", "cost_per_kw"],
        learning_time_minutes=15,
        keywords=["投资成本", "CAPEX", "OPEX"],
    )

    nodes["3.2"] = KnowledgePoint(
        id="3.2",
        parent_id="3",
        title="收益计算",
        summary="套利收益与回收期计算",
        content="""
# 收益计算

## 日收益计算
```
日收益 = 放电收入 - 充电成本
       = 放电量 × 峰时电价 - 充电量 × 谷时电价
```

## 年收益估算
```
年收益 = 日收益 × 运营天数 - 年运维成本
```

## 投资回收期
```
静态回收期 = 初始投资 / 年净收益
```

## 影响因素
- 峰谷价差
- 系统效率
- 运营天数
- 容量利用率
        """,
        related_modules=["economic_params"],
        learning_time_minutes=20,
        keywords=["收益", "回收期", "峰谷价差"],
    )

    return nodes


def _init_terminology_dict() -> Dict[str, Terminology]:
    """初始化术语表"""
    terms = {}

    terms["SOC"] = Terminology(
        term="SOC",
        english="State of Charge",
        abbreviation="SOC",
        definition="荷电状态，表示电池剩余电量百分比",
        explanation="SOC是衡量电池剩余电量的关键指标，范围0-100%。",
        related_terms=["SOH", "DOD"],
        example="当SOC=50%时，100kWh电池还剩50kWh可用电量"
    )

    terms["SOH"] = Terminology(
        term="SOH",
        english="State of Health",
        abbreviation="SOH",
        definition="健康状态，表示电池容量衰减程度",
        explanation="电池当前最大容量与初始容量的比值。",
        related_terms=["SOC", "循环寿命"],
        example="SOH=90%意味着电池容量衰减了10%"
    )

    terms["DOD"] = Terminology(
        term="DOD",
        english="Depth of Discharge",
        abbreviation="DOD",
        definition="放电深度，表示单次放电量占总容量的百分比",
        explanation="DOD越大，对电池损耗越大。",
        related_terms=["SOC", "循环寿命"],
        example="从100%放到20%，DOD=80%"
    )

    terms["BMS"] = Terminology(
        term="BMS",
        english="Battery Management System",
        abbreviation="BMS",
        definition="电池管理系统，负责监测和保护电池",
        explanation="采集电池电压、电流、温度，估算SOC/SOH，执行保护。",
        related_terms=["PCS", "EMS"],
    )

    terms["PCS"] = Terminology(
        term="PCS",
        english="Power Conversion System",
        abbreviation="PCS",
        definition="储能变流器，实现交直流转换",
        explanation="充电时将交流电转为直流电，放电时将直流电转为交流电。",
        related_terms=["BMS", "EMS"],
    )

    terms["EMS"] = Terminology(
        term="EMS",
        english="Energy Management System",
        abbreviation="EMS",
        definition="能量管理系统，统筹调度优化",
        explanation="储能系统的'大脑'，负责策略计算和指令下发。",
        related_terms=["BMS", "PCS"],
    )

    terms["峰谷电价"] = Terminology(
        term="峰谷电价",
        english="Time-of-Use Pricing",
        definition="分时电价，不同时段电价不同",
        explanation="峰时电价高，谷时电价低，是储能套利的基础。",
        example="峰时1.2元/kWh，谷时0.4元/kWh，价差0.8元/kWh"
    )

    terms["往返效率"] = Terminology(
        term="往返效率",
        english="Round-Trip Efficiency",
        definition="储能系统充放电一次的能量转换效率",
        explanation="往返效率 = 放电量/充电量 × 100%",
        example="充入100kWh，放出90kWh，往返效率=90%"
    )

    return terms


# =============================================================================
# 模块状态
# =============================================================================
_knowledge_tree: Optional[Dict[str, KnowledgePoint]] = None
_terminology_dict: Optional[Dict[str, Terminology]] = None


def get_knowledge_tree() -> Dict[str, KnowledgePoint]:
    """获取知识树"""
    global _knowledge_tree
    if _knowledge_tree is None:
        _knowledge_tree = _init_knowledge_tree()
    return _knowledge_tree


def get_terminology_dict() -> Dict[str, Terminology]:
    """获取术语表"""
    global _terminology_dict
    if _terminology_dict is None:
        _terminology_dict = _init_terminology_dict()
    return _terminology_dict


def get_knowledge_point(point_id: str) -> Optional[KnowledgePoint]:
    """获取指定知识点"""
    tree = get_knowledge_tree()
    return tree.get(point_id)


def search_knowledge(query: str) -> List[KnowledgePoint]:
    """搜索知识点"""
    tree = get_knowledge_tree()
    query_lower = query.lower()
    results = []

    for point in tree.values():
        if (query_lower in point.title.lower() or
            query_lower in point.summary.lower() or
            any(query_lower in kw.lower() for kw in point.keywords)):
            results.append(point)

    return results


def search_terminology(query: str) -> List[Terminology]:
    """搜索术语"""
    terms = get_terminology_dict()
    query_lower = query.lower()
    results = []

    for term in terms.values():
        if (query_lower in term.term.lower() or
            query_lower in term.english.lower() or
            query_lower in term.abbreviation.lower()):
            results.append(term)

    return results


def get_param_help(param_name: str) -> str:
    """获取参数帮助文本"""
    param_help = {
        "capacity": "储能系统可存储的总电量，类似于'油箱大小'。容量越大，可调度能量越多。",
        "power_rated": "最大充放电速率，类似于'加油/放油速度'。功率越大，响应能力越强。",
        "soc_min": "允许放电的最低SOC，保护电池避免深放。设置过低会加速电池老化。",
        "soc_max": "允许充电的最高SOC，保护电池避免过充。通常设置90-95%。",
        "soc_init": "仿真开始时的初始SOC。影响首次充放电的能量。",
        "efficiency_charge": "充电效率，能量从电网到电池的转换效率。",
        "efficiency_discharge": "放电效率，能量从电池到电网的转换效率。",
        "cycle_life": "电池循环寿命，可充放电的总次数。",
    }
    return param_help.get(param_name, "暂无帮助信息")


# =============================================================================
# Gradio UI组件
# =============================================================================
def create_learning_center_tab() -> Tuple[gr.Tab, Dict[str, Any]]:
    """创建教学引导标签页

    Returns:
        Tuple[gr.Tab, Dict]: (标签页, 组件字典)
    """
    with gr.Tab("教学引导") as tab:

        gr.Markdown("### 学习中心")
        gr.Markdown("系统化学习储能EMS知识，掌握核心概念和操作技能。")

        with gr.Row():
            # 左侧：知识地图
            with gr.Column(scale=1):
                gr.Markdown("#### 知识地图")

                knowledge_tree_display = gr.Markdown(
                    value=_render_knowledge_tree_markdown()
                )

                selected_point_id = gr.State(value="1.1")

            # 右侧：知识详情
            with gr.Column(scale=2):
                gr.Markdown("#### 知识点详情")

                point_selector = gr.Dropdown(
                    label="选择知识点",
                    choices=_get_knowledge_choices(),
                    value="1.1 储能系统组成"
                )

                point_content = gr.Markdown(
                    value=_get_point_content("1.1")
                )

        # 术语速查
        with gr.Accordion("术语速查", open=True):
            with gr.Row():
                term_search = gr.Textbox(
                    label="搜索术语",
                    placeholder="输入术语、缩写或关键词...",
                    scale=2
                )
                search_btn = gr.Button("搜索", scale=1)

            term_result = gr.Markdown(
                value=_render_common_terms()
            )

        # 学习建议
        with gr.Accordion("学习建议", open=False):
            gr.Markdown("""
**新手入门路径：**
1. 储能基础 → 了解系统组成
2. 电池知识 → 理解SOC/SOH
3. EMS功能 → 掌握调度策略
4. 经济分析 → 学会收益计算

**推荐学习顺序：**
- 1.1 储能系统组成 (10分钟)
- 1.2 电池基础知识 (15分钟)
- 2.2 调度策略 (20分钟)
- 3.2 收益计算 (20分钟)
            """)

    components = {
        "knowledge_tree": knowledge_tree_display,
        "point_selector": point_selector,
        "point_content": point_content,
        "term_search": term_search,
        "search_btn": search_btn,
        "term_result": term_result,
    }

    return tab, components


def setup_learning_center_events(components: Dict[str, Any]):
    """设置教学引导事件绑定"""

    def on_point_select(selection):
        """知识点选择"""
        if not selection:
            return ""
        point_id = selection.split(" ")[0]
        return _get_point_content(point_id)

    def on_term_search(query):
        """术语搜索"""
        if not query:
            return _render_common_terms()

        results = search_terminology(query)
        if not results:
            return f"未找到与 '{query}' 相关的术语"

        md = ""
        for term in results:
            md += f"### {term.term}"
            if term.english:
                md += f" ({term.english})"
            md += "\n\n"
            md += f"**定义**: {term.definition}\n\n"
            if term.explanation:
                md += f"{term.explanation}\n\n"
            if term.example:
                md += f"**示例**: {term.example}\n\n"
            md += "---\n\n"

        return md

    # 绑定知识点选择
    components["point_selector"].change(
        fn=on_point_select,
        inputs=[components["point_selector"]],
        outputs=[components["point_content"]]
    )

    # 绑定术语搜索
    components["search_btn"].click(
        fn=on_term_search,
        inputs=[components["term_search"]],
        outputs=[components["term_result"]]
    )

    components["term_search"].submit(
        fn=on_term_search,
        inputs=[components["term_search"]],
        outputs=[components["term_result"]]
    )


def _render_knowledge_tree_markdown() -> str:
    """渲染知识树Markdown"""
    tree = get_knowledge_tree()

    md = ""
    # 找出根节点
    root_nodes = [p for p in tree.values() if p.parent_id is None]

    for root in sorted(root_nodes, key=lambda x: x.id):
        md += f"**{root.id}. {root.title}**\n"

        # 找出子节点
        children = [p for p in tree.values() if p.parent_id == root.id]
        for child in sorted(children, key=lambda x: x.id):
            level_icon = "🟢" if child.level == KnowledgeLevel.BEGINNER else "🟡"
            md += f"  - {level_icon} {child.id} {child.title}\n"

        md += "\n"

    return md


def _get_knowledge_choices() -> List[str]:
    """获取知识点选项列表"""
    tree = get_knowledge_tree()
    choices = []

    for point in sorted(tree.values(), key=lambda x: x.id):
        if point.parent_id is not None:  # 只显示子节点
            choices.append(f"{point.id} {point.title}")

    return choices


def _get_point_content(point_id: str) -> str:
    """获取知识点内容"""
    point = get_knowledge_point(point_id)
    if not point:
        return "请选择知识点"

    md = f"## {point.title}\n\n"
    md += f"**难度**: {point.level.value} | "
    md += f"**预计时间**: {point.learning_time_minutes}分钟\n\n"

    if point.summary:
        md += f"*{point.summary}*\n\n"

    if point.content:
        md += point.content

    if point.keywords:
        md += f"\n\n**关键词**: {', '.join(point.keywords)}"

    return md


def _render_common_terms() -> str:
    """渲染常用术语"""
    return """
**常用术语快速查询：**

| 术语 | 全称 | 说明 |
|------|------|------|
| SOC | State of Charge | 荷电状态，电池剩余电量百分比 |
| SOH | State of Health | 健康状态，电池容量衰减程度 |
| DOD | Depth of Discharge | 放电深度 |
| BMS | Battery Management System | 电池管理系统 |
| PCS | Power Conversion System | 储能变流器 |
| EMS | Energy Management System | 能量管理系统 |

*输入术语进行详细查询*
"""


# =============================================================================
# 教学元数据
# =============================================================================
LEARNING_TEACHING_META: Dict[str, Dict[str, Any]] = {
    "knowledge_tree": {
        "title": "知识地图",
        "help_text": "展示储能知识体系结构，点击查看详情",
    },
    "terminology": {
        "title": "术语速查",
        "help_text": "快速查询储能相关术语和缩写",
    },
}
