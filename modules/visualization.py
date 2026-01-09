# -*- coding: utf-8 -*-
"""可视化模块

对应技术设计文档：05_可视化模块技术设计.md
负责仿真结果图表展示、数据导出、统计表格生成
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
from datetime import datetime, timedelta

from models.simulation import SimulationResult, SIMULATION_TEACHING_META


# =============================================================================
# 可视化配置数据类
# =============================================================================
class ChartType(Enum):
    """图表类型"""
    LINE = "折线图"
    AREA = "面积图"
    BAR = "柱状图"
    STEP = "阶梯图"
    SCATTER = "散点图"


class ChartLibrary(Enum):
    """图表库选择"""
    MATPLOTLIB = "matplotlib"
    PLOTLY = "plotly"


@dataclass
class ChartStyle:
    """图表样式配置"""

    # 颜色方案
    colors: Dict[str, str] = field(default_factory=lambda: {
        'load': '#FF6B6B',          # 负荷 - 红色
        'bess_charge': '#4ECDC4',   # 充电 - 青色
        'bess_discharge': '#45B7D1', # 放电 - 蓝色
        'soc': '#96CEB4',           # SOC - 绿色
        'grid': '#FFEAA7',          # 电网 - 黄色
        'price': '#DDA0DD',         # 电价 - 紫色
        'peak': '#FF6B6B',          # 峰时 - 红色
        'flat': '#FFE66D',          # 平时 - 黄色
        'valley': '#4ECDC4',        # 谷时 - 青色
    })

    # 图表尺寸
    figure_size: Tuple[int, int] = (12, 6)
    subplot_height: int = 4

    # 字体设置
    font_family: str = "SimHei"     # 支持中文
    title_size: int = 14
    label_size: int = 12
    tick_size: int = 10
    legend_size: int = 10

    # 网格
    show_grid: bool = True
    grid_alpha: float = 0.3


@dataclass
class ExportConfig:
    """导出配置"""

    format: str = "csv"             # csv, xlsx, json
    include_timestep_data: bool = True
    include_summary: bool = True
    include_charts: bool = False
    time_format: str = "hours"      # hours, datetime
    decimal_places: int = 2


# =============================================================================
# 可视化教学元数据
# =============================================================================
VISUALIZATION_TEACHING_META: Dict[str, Dict[str, Any]] = {
    "power_curve": {
        "title": "功率曲线图",
        "help_text": "展示负荷、储能充放电、电网功率随时间的变化",
        "key_observations": [
            "负荷曲线（蓝色）：用户的实际用电需求",
            "充电功率（绿色向下）：储能从电网吸收电能",
            "放电功率（红色向上）：储能向负荷供电",
            "电网功率（橙色虚线）：实际从电网购电的功率"
        ],
        "learning_focus": "观察储能如何在峰谷时段进行充放电，理解削峰填谷原理",
    },
    "soc_curve": {
        "title": "SOC变化曲线",
        "help_text": "展示电池荷电状态(SOC)随时间的变化",
        "key_observations": [
            "SOC曲线（绿色）：电池剩余电量百分比",
            "运行范围：正常运行的SOC区间",
            "保护边界（红色虚线）：触发保护的SOC阈值"
        ],
        "learning_focus": "理解SOC变化与充放电的关系，观察保护逻辑的触发时机",
    },
    "price_curve": {
        "title": "电价曲线",
        "help_text": "展示24小时分时电价变化",
        "key_observations": [
            "谷时段（低价）：适合充电储能",
            "峰时段（高价）：适合放电获利",
            "平时段：根据SOC状态决定是否运行"
        ],
        "learning_focus": "理解峰谷电价套利的基本原理",
    },
    "energy_summary": {
        "title": "能量统计图",
        "help_text": "柱状图展示充电量、放电量及损耗",
        "key_observations": [
            "充电量 > 放电量：因为存在效率损失",
            "损耗 = 充电量 - 放电量",
            "往返效率 = 放电量/充电量 × 100%"
        ],
        "learning_focus": "理解储能系统的能量转换效率",
    },
}


# =============================================================================
# 功率曲线绘制
# =============================================================================
def plot_power_curve(
    result: SimulationResult,
    style: Optional[ChartStyle] = None,
    library: ChartLibrary = ChartLibrary.PLOTLY
):
    """绘制功率曲线图

    Args:
        result: 仿真结果
        style: 图表样式
        library: 图表库

    Returns:
        Figure: 图表对象
    """
    if style is None:
        style = ChartStyle()

    time = result.get_time_array()
    load = result.get_load_array()
    bess_power = result.get_power_array()
    grid_power = result.get_grid_power_array()
    price = result.get_price_array()

    # 分离充放电功率
    charge_power = [-p if p < 0 else 0 for p in bess_power]
    discharge_power = [p if p > 0 else 0 for p in bess_power]

    if library == ChartLibrary.PLOTLY:
        return _plot_power_curve_plotly(
            time, load, charge_power, discharge_power, grid_power, price, style
        )
    else:
        return _plot_power_curve_matplotlib(
            time, load, charge_power, discharge_power, grid_power, price, style
        )


def _plot_power_curve_plotly(
    time, load, charge_power, discharge_power, grid_power, price, style
):
    """使用Plotly绘制功率曲线"""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=('功率曲线', '电价曲线'),
            row_heights=[0.7, 0.3]
        )

        # 负荷曲线
        fig.add_trace(
            go.Scatter(
                x=time, y=load,
                name='负荷',
                line=dict(color=style.colors['load'], width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 107, 107, 0.1)'
            ),
            row=1, col=1
        )

        # 放电功率
        fig.add_trace(
            go.Bar(
                x=time, y=discharge_power,
                name='放电功率',
                marker_color='rgba(255, 99, 71, 0.7)'
            ),
            row=1, col=1
        )

        # 充电功率
        fig.add_trace(
            go.Bar(
                x=time, y=charge_power,
                name='充电功率',
                marker_color='rgba(50, 205, 50, 0.7)'
            ),
            row=1, col=1
        )

        # 电网功率
        fig.add_trace(
            go.Scatter(
                x=time, y=grid_power,
                name='电网功率',
                line=dict(color=style.colors['grid'], width=1.5, dash='dash')
            ),
            row=1, col=1
        )

        # 电价曲线
        fig.add_trace(
            go.Scatter(
                x=time, y=price,
                name='电价',
                line=dict(color=style.colors['price'], width=2, shape='hv'),
                fill='tozeroy',
                fillcolor='rgba(221, 160, 221, 0.2)'
            ),
            row=2, col=1
        )

        fig.update_layout(
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            hovermode='x unified'
        )

        fig.update_xaxes(title_text="时间 (h)", row=2, col=1)
        fig.update_yaxes(title_text="功率 (kW)", row=1, col=1)
        fig.update_yaxes(title_text="电价 (元/kWh)", row=2, col=1)

        return fig

    except ImportError:
        return _plot_power_curve_matplotlib(
            time, load, charge_power, discharge_power, grid_power, price, style
        )


def _plot_power_curve_matplotlib(
    time, load, charge_power, discharge_power, grid_power, price, style
):
    """使用Matplotlib绘制功率曲线"""
    import matplotlib.pyplot as plt

    plt.rcParams['font.sans-serif'] = [style.font_family, 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    fig, (ax1, ax2) = plt.subplots(
        2, 1,
        figsize=style.figure_size,
        sharex=True,
        gridspec_kw={'height_ratios': [3, 1]}
    )

    # 功率曲线
    ax1.plot(time, load, label='负荷', color=style.colors['load'], linewidth=2)
    ax1.bar(time, charge_power, label='充电', color=style.colors['bess_charge'], alpha=0.7, width=0.2)
    ax1.bar(time, discharge_power, label='放电', color=style.colors['bess_discharge'], alpha=0.7, width=0.2)
    ax1.plot(time, grid_power, label='电网', color='orange', linewidth=1.5, linestyle='--')

    ax1.axhline(y=0, color='gray', linewidth=0.5)
    ax1.set_ylabel('功率 (kW)', fontsize=style.label_size)
    ax1.legend(loc='upper right', fontsize=style.legend_size)
    ax1.grid(style.show_grid, alpha=style.grid_alpha)
    ax1.set_title('功率曲线', fontsize=style.title_size)

    # 电价曲线
    ax2.step(time, price, where='post', label='电价', color=style.colors['price'], linewidth=2)
    ax2.fill_between(time, price, step='post', color=style.colors['price'], alpha=0.2)
    ax2.set_xlabel('时间 (h)', fontsize=style.label_size)
    ax2.set_ylabel('电价 (元/kWh)', fontsize=style.label_size)
    ax2.grid(style.show_grid, alpha=style.grid_alpha)

    plt.tight_layout()
    return fig


# =============================================================================
# SOC曲线绘制
# =============================================================================
def plot_soc_curve(
    result: SimulationResult,
    style: Optional[ChartStyle] = None,
    library: ChartLibrary = ChartLibrary.PLOTLY
):
    """绘制SOC曲线

    Args:
        result: 仿真结果
        style: 图表样式
        library: 图表库

    Returns:
        Figure: 图表对象
    """
    if style is None:
        style = ChartStyle()

    time = result.get_time_array()
    soc = result.get_soc_array()

    # 获取SOC限制
    bess_params = result.bess_params
    control_params = result.control_params

    soc_min = bess_params.soc_min
    soc_max = bess_params.soc_max
    protect_low = control_params.protection.protect_soc_low
    protect_high = control_params.protection.protect_soc_high

    if library == ChartLibrary.PLOTLY:
        return _plot_soc_curve_plotly(
            time, soc, soc_min, soc_max, protect_low, protect_high, style
        )
    else:
        return _plot_soc_curve_matplotlib(
            time, soc, soc_min, soc_max, protect_low, protect_high, style
        )


def _plot_soc_curve_plotly(
    time, soc, soc_min, soc_max, protect_low, protect_high, style
):
    """使用Plotly绘制SOC曲线"""
    try:
        import plotly.graph_objects as go

        fig = go.Figure()

        # SOC曲线
        fig.add_trace(
            go.Scatter(
                x=time, y=soc,
                name='SOC',
                line=dict(color=style.colors['soc'], width=2.5),
                fill='tozeroy',
                fillcolor='rgba(150, 206, 180, 0.3)'
            )
        )

        # SOC运行范围区域
        fig.add_hrect(
            y0=soc_min, y1=soc_max,
            fillcolor="rgba(150, 206, 180, 0.1)",
            line_width=0,
        )

        # 参考线
        fig.add_hline(
            y=soc_max, line_dash="dash",
            line_color="green",
            annotation_text=f"SOC上限 {soc_max}%",
            annotation_position="right"
        )
        fig.add_hline(
            y=soc_min, line_dash="dash",
            line_color="green",
            annotation_text=f"SOC下限 {soc_min}%",
            annotation_position="right"
        )
        fig.add_hline(
            y=protect_high, line_dash="dot",
            line_color="red",
            annotation_text=f"过充保护 {protect_high}%",
            annotation_position="right"
        )
        fig.add_hline(
            y=protect_low, line_dash="dot",
            line_color="orange",
            annotation_text=f"过放保护 {protect_low}%",
            annotation_position="right"
        )

        fig.update_layout(
            title='SOC变化曲线',
            xaxis_title='时间 (h)',
            yaxis_title='SOC (%)',
            yaxis_range=[0, 100],
            height=400,
            showlegend=True,
            hovermode='x unified'
        )

        return fig

    except ImportError:
        return _plot_soc_curve_matplotlib(
            time, soc, soc_min, soc_max, protect_low, protect_high, style
        )


def _plot_soc_curve_matplotlib(
    time, soc, soc_min, soc_max, protect_low, protect_high, style
):
    """使用Matplotlib绘制SOC曲线"""
    import matplotlib.pyplot as plt

    plt.rcParams['font.sans-serif'] = [style.font_family, 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(style.figure_size[0], style.subplot_height))

    # SOC曲线
    ax.plot(time, soc, color=style.colors['soc'], linewidth=2.5, label='SOC')
    ax.fill_between(time, soc, alpha=0.3, color=style.colors['soc'])

    # 运行范围区域
    ax.axhspan(soc_min, soc_max, alpha=0.1, color='green', label='运行范围')

    # 参考线
    ax.axhline(y=soc_max, color='green', linestyle='--', linewidth=1, label=f'SOC上限 {soc_max}%')
    ax.axhline(y=soc_min, color='green', linestyle='--', linewidth=1, label=f'SOC下限 {soc_min}%')
    ax.axhline(y=protect_high, color='red', linestyle=':', linewidth=1, label=f'过充保护 {protect_high}%')
    ax.axhline(y=protect_low, color='orange', linestyle=':', linewidth=1, label=f'过放保护 {protect_low}%')

    ax.set_xlabel('时间 (h)', fontsize=style.label_size)
    ax.set_ylabel('SOC (%)', fontsize=style.label_size)
    ax.set_ylim(0, 100)
    ax.set_title('SOC变化曲线', fontsize=style.title_size)
    ax.legend(loc='upper right', fontsize=style.legend_size)
    ax.grid(style.show_grid, alpha=style.grid_alpha)

    plt.tight_layout()
    return fig


# =============================================================================
# 能量统计图
# =============================================================================
def plot_energy_summary(
    result: SimulationResult,
    style: Optional[ChartStyle] = None,
    library: ChartLibrary = ChartLibrary.PLOTLY
):
    """绘制能量统计柱状图

    Args:
        result: 仿真结果
        style: 图表样式
        library: 图表库

    Returns:
        Figure: 图表对象
    """
    if style is None:
        style = ChartStyle()

    charge = result.total_charge_kwh
    discharge = result.total_discharge_kwh
    loss = charge - discharge

    if library == ChartLibrary.PLOTLY:
        try:
            import plotly.graph_objects as go

            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=['充电量', '放电量', '损耗'],
                y=[charge, discharge, loss],
                marker_color=['#4ECDC4', '#45B7D1', '#FF6B6B'],
                text=[f'{v:.1f} kWh' for v in [charge, discharge, loss]],
                textposition='outside'
            ))

            fig.update_layout(
                title='能量统计',
                yaxis_title='电量 (kWh)',
                height=350,
                showlegend=False
            )

            return fig

        except ImportError:
            pass

    # Matplotlib 后备
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4))

    bars = ax.bar(
        ['充电量', '放电量', '损耗'],
        [charge, discharge, loss],
        color=['#4ECDC4', '#45B7D1', '#FF6B6B']
    )

    for bar, val in zip(bars, [charge, discharge, loss]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{val:.1f}', ha='center', fontsize=10)

    ax.set_ylabel('电量 (kWh)')
    ax.set_title('能量统计')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    return fig


# =============================================================================
# 统计表格生成
# =============================================================================
def generate_statistics_table(
    result: SimulationResult,
    table_type: str = "economic"
) -> List[List[str]]:
    """生成统计表格数据

    Args:
        result: 仿真结果
        table_type: 表格类型 (economic, operation)

    Returns:
        List[List[str]]: 表格数据 [[指标, 数值, 单位], ...]
    """
    if table_type == "economic":
        return _generate_economic_table(result)
    elif table_type == "operation":
        return _generate_operation_table(result)
    else:
        return []


def _generate_economic_table(result: SimulationResult) -> List[List[str]]:
    """生成经济统计表格"""
    return [
        ["充电成本", f"{result.total_charge_cost:.2f}", "元"],
        ["放电收益", f"{result.total_discharge_revenue:.2f}", "元"],
        ["套利利润", f"{result.arbitrage_profit:.2f}", "元"],
        ["基准电费", f"{result.baseline_cost:.2f}", "元"],
        ["节约电费", f"{result.cost_saving:.2f}", "元"],
    ]


def _generate_operation_table(result: SimulationResult) -> List[List[str]]:
    """生成运行统计表格"""
    return [
        ["总充电量", f"{result.total_charge_kwh:.2f}", "kWh"],
        ["总放电量", f"{result.total_discharge_kwh:.2f}", "kWh"],
        ["系统效率", f"{result.system_efficiency:.1f}", "%"],
        ["等效循环", f"{result.equivalent_cycles:.3f}", "次"],
        ["容量利用率", f"{result.capacity_utilization:.1f}", "%"],
        ["功率利用率", f"{result.power_utilization:.1f}", "%"],
        ["最低SOC", f"{result.soc_min_actual:.1f}", "%"],
        ["最高SOC", f"{result.soc_max_actual:.1f}", "%"],
        ["最终SOC", f"{result.soc_final:.1f}", "%"],
    ]


def generate_annual_table(annual_data: Dict[str, float]) -> List[List[str]]:
    """生成年度预测表格

    Args:
        annual_data: 年度预测数据

    Returns:
        List[List[str]]: 表格数据
    """
    payback_text = (
        f"{annual_data['static_payback']:.1f}"
        if annual_data['static_payback'] < 100
        else "无法回收"
    )

    return [
        ["日套利利润", f"{annual_data['daily_profit']:.2f}", "元"],
        ["年套利收益", f"{annual_data['annual_revenue'] / 10000:.2f}", "万元"],
        ["年运维成本", f"{annual_data['annual_opex'] / 10000:.2f}", "万元"],
        ["年净收益", f"{annual_data['net_annual_revenue'] / 10000:.2f}", "万元"],
        ["初始投资", f"{annual_data['initial_investment'] / 10000:.2f}", "万元"],
        ["静态回收期", payback_text, "年"],
        ["年等效循环", f"{annual_data['annual_cycles']:.1f}", "次"],
        ["预计寿命", f"{annual_data['expected_life_years']:.1f}", "年"],
    ]


# =============================================================================
# 数据导出
# =============================================================================
def export_results(
    result: SimulationResult,
    filepath: str,
    config: Optional[ExportConfig] = None
) -> Tuple[bool, str]:
    """导出仿真结果

    Args:
        result: 仿真结果
        filepath: 导出文件路径
        config: 导出配置

    Returns:
        Tuple[bool, str]: (是否成功, 消息)
    """
    if config is None:
        config = ExportConfig()

    try:
        if config.format == "csv":
            return _export_csv(result, filepath, config)
        elif config.format == "xlsx":
            return _export_excel(result, filepath, config)
        elif config.format == "json":
            return _export_json(result, filepath, config)
        else:
            return False, f"不支持的导出格式: {config.format}"
    except Exception as e:
        return False, f"导出失败: {str(e)}"


def _export_csv(result: SimulationResult, filepath: str, config: ExportConfig) -> Tuple[bool, str]:
    """导出为CSV"""
    try:
        import pandas as pd

        df = result.to_dataframe()

        # 格式化时间
        if config.time_format == "datetime":
            base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            df['datetime'] = df['time_hours'].apply(
                lambda h: base_time + timedelta(hours=h)
            )

        # 四舍五入
        numeric_cols = df.select_dtypes(include=['float64', 'float32']).columns
        df[numeric_cols] = df[numeric_cols].round(config.decimal_places)

        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        return True, f"已导出到 {filepath}"

    except ImportError:
        return False, "需要安装pandas库"


def _export_excel(result: SimulationResult, filepath: str, config: ExportConfig) -> Tuple[bool, str]:
    """导出为Excel"""
    try:
        import pandas as pd

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # 时序数据
            if config.include_timestep_data:
                df = result.to_dataframe()
                df.to_excel(writer, sheet_name='时序数据', index=False)

            # 汇总统计
            if config.include_summary:
                summary_df = pd.DataFrame({
                    '类别': ['运行统计'] * 9 + ['经济统计'] * 5,
                    '指标': [
                        '总充电量', '总放电量', '系统效率', '等效循环',
                        '容量利用率', '功率利用率', '最低SOC', '最高SOC', '最终SOC',
                        '充电成本', '放电收益', '套利利润', '基准电费', '节约电费'
                    ],
                    '数值': [
                        result.total_charge_kwh, result.total_discharge_kwh,
                        result.system_efficiency, result.equivalent_cycles,
                        result.capacity_utilization, result.power_utilization,
                        result.soc_min_actual, result.soc_max_actual, result.soc_final,
                        result.total_charge_cost, result.total_discharge_revenue,
                        result.arbitrage_profit, result.baseline_cost, result.cost_saving
                    ],
                    '单位': [
                        'kWh', 'kWh', '%', '次', '%', '%', '%', '%', '%',
                        '元', '元', '元', '元', '元'
                    ]
                })
                summary_df.to_excel(writer, sheet_name='统计汇总', index=False)

        return True, f"已导出到 {filepath}"

    except ImportError:
        return False, "需要安装pandas和openpyxl库"


def _export_json(result: SimulationResult, filepath: str, config: ExportConfig) -> Tuple[bool, str]:
    """导出为JSON"""
    import json

    data = {
        'config': result.config.to_dict(),
        'summary': result.get_summary_dict()
    }

    if config.include_timestep_data:
        data['timestep_data'] = [r.to_dict() for r in result.timestep_results]

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True, f"已导出到 {filepath}"


# =============================================================================
# 综合仪表板
# =============================================================================
def plot_combined_dashboard(result: SimulationResult, style: Optional[ChartStyle] = None):
    """绘制综合仪表板

    Args:
        result: 仿真结果
        style: 图表样式

    Returns:
        Figure: plotly Figure
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        if style is None:
            style = ChartStyle()

        time = result.get_time_array()
        soc = result.get_soc_array()
        load = result.get_load_array()
        power = result.get_power_array()
        price = result.get_price_array()

        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                '功率曲线', '电价曲线',
                'SOC变化', '能量统计',
                '经济分析', '运行统计'
            ),
            row_heights=[0.4, 0.3, 0.3],
            specs=[
                [{"type": "scatter"}, {"type": "scatter"}],
                [{"type": "scatter"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "table"}]
            ]
        )

        # 功率曲线
        fig.add_trace(
            go.Scatter(x=time, y=load, name='负荷', line=dict(color='#1f77b4')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=time, y=power, name='BESS功率', line=dict(color='#2ca02c')),
            row=1, col=1
        )

        # 电价曲线
        fig.add_trace(
            go.Scatter(x=time, y=price, name='电价', line=dict(shape='hv', color='purple')),
            row=1, col=2
        )

        # SOC曲线
        fig.add_trace(
            go.Scatter(x=time, y=soc, name='SOC', fill='tozeroy', line=dict(color='#2ca02c')),
            row=2, col=1
        )

        # 能量统计
        fig.add_trace(
            go.Bar(
                x=['充电量', '放电量'],
                y=[result.total_charge_kwh, result.total_discharge_kwh],
                marker_color=['#4ECDC4', '#45B7D1']
            ),
            row=2, col=2
        )

        # 经济分析
        fig.add_trace(
            go.Bar(
                x=['充电成本', '放电收益', '套利利润'],
                y=[result.total_charge_cost, result.total_discharge_revenue, result.arbitrage_profit],
                marker_color=['#FF6B6B', '#4ECDC4', '#FFE66D']
            ),
            row=3, col=1
        )

        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="储能系统仿真综合仪表板"
        )

        return fig

    except ImportError:
        return None
