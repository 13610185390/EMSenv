# -*- coding: utf-8 -*-
"""经济参数模块

对应技术设计文档：02_经济参数模块技术设计.md
负责电价、成本、财务参数的配置和计算
"""

from typing import Dict, Any, Optional, Tuple, List
from datetime import time

import gradio as gr

from models.economic import (
    EconomicParams, ElectricityPriceParams, CostParams, FinancialParams,
    TimePeriod, PricePeriodType, ECONOMIC_TEACHING_META
)
from config.default_params import (
    get_default_economic_params, create_default_economic_params
)
from utils.validators import validate_economic_params as _validate_economic_params


# =============================================================================
# 模块状态
# =============================================================================
_current_params: Optional[EconomicParams] = None


# =============================================================================
# 参数管理函数
# =============================================================================
def get_economic_params() -> EconomicParams:
    """获取当前经济参数配置

    Returns:
        EconomicParams: 经济参数数据类实例
    """
    global _current_params
    if _current_params is None:
        _current_params = create_default_economic_params()
    return _current_params


def set_economic_params(params: EconomicParams) -> Tuple[bool, List[str]]:
    """设置经济参数

    Args:
        params: 经济参数数据类实例

    Returns:
        Tuple[bool, List[str]]: (是否成功, 错误信息列表)
    """
    global _current_params

    # 校验参数
    ok, errors = validate_economic_params(params)
    if not ok:
        return False, errors

    _current_params = params
    return True, []


def validate_economic_params(params: EconomicParams) -> Tuple[bool, List[str]]:
    """校验经济参数

    Args:
        params: 待校验的参数

    Returns:
        Tuple[bool, List[str]]: (是否通过, 错误信息列表)
    """
    # 转换为字典进行校验
    params_dict = {
        "price_valley": params.price_params.price_valley,
        "price_flat": params.price_params.price_flat,
        "price_peak": params.price_params.price_peak,
        "price_critical": params.price_params.price_critical,
        "price_feed_in": params.price_params.price_feed_in,
        "cost_per_kwh": params.cost_params.cost_per_kwh,
        "cost_per_kw": params.cost_params.cost_per_kw,
        "cost_install_ratio": params.cost_params.cost_install_ratio,
        "cost_om_ratio": params.cost_params.cost_om_ratio,
        "discount_rate": params.financial_params.discount_rate,
        "project_years": params.financial_params.project_years,
        "residual_ratio": params.financial_params.residual_ratio,
    }
    return _validate_economic_params(params_dict)


def reset_to_default() -> EconomicParams:
    """重置为默认参数

    Returns:
        EconomicParams: 默认参数实例
    """
    global _current_params
    _current_params = create_default_economic_params()
    return _current_params


# =============================================================================
# 经济计算函数
# =============================================================================
def calculate_peak_valley_spread(params: EconomicParams) -> float:
    """计算峰谷价差

    Args:
        params: 经济参数

    Returns:
        float: 峰谷价差 (元/kWh)
    """
    return params.price_params.peak_valley_spread


def calculate_initial_investment(
    params: EconomicParams,
    capacity_kwh: float,
    power_kw: float
) -> float:
    """计算初始投资

    Args:
        params: 经济参数
        capacity_kwh: 容量 (kWh)
        power_kw: 功率 (kW)

    Returns:
        float: 初始投资 (元)
    """
    return params.cost_params.calculate_initial_investment(capacity_kwh, power_kw)


def calculate_annual_opex(params: EconomicParams, initial_investment: float) -> float:
    """计算年运营成本

    Args:
        params: 经济参数
        initial_investment: 初始投资

    Returns:
        float: 年运营成本 (元)
    """
    return params.cost_params.calculate_annual_opex(initial_investment)


def calculate_daily_revenue(
    params: EconomicParams,
    charge_kwh: float,
    discharge_kwh: float,
    charge_price: float = None,
    discharge_price: float = None
) -> Dict[str, float]:
    """计算日收益

    Args:
        params: 经济参数
        charge_kwh: 日充电量 (kWh)
        discharge_kwh: 日放电量 (kWh)
        charge_price: 充电电价（默认谷电价）
        discharge_price: 放电电价（默认峰电价）

    Returns:
        Dict: {
            'charge_cost': 充电成本,
            'discharge_revenue': 放电收益,
            'arbitrage_profit': 套利利润
        }
    """
    if charge_price is None:
        charge_price = params.price_params.price_valley
    if discharge_price is None:
        discharge_price = params.price_params.price_peak

    charge_cost = charge_kwh * charge_price
    discharge_revenue = discharge_kwh * discharge_price
    arbitrage_profit = discharge_revenue - charge_cost

    return {
        'charge_cost': charge_cost,
        'discharge_revenue': discharge_revenue,
        'arbitrage_profit': arbitrage_profit
    }


def calculate_full_economics(
    params: EconomicParams,
    capacity_kwh: float,
    power_kw: float,
    daily_cycles: float = 1.0,
    round_trip_efficiency: float = 0.9
) -> Dict[str, Any]:
    """计算完整经济指标

    Args:
        params: 经济参数
        capacity_kwh: 容量 (kWh)
        power_kw: 功率 (kW)
        daily_cycles: 日循环次数
        round_trip_efficiency: 往返效率

    Returns:
        Dict: 完整经济指标
    """
    # 初始投资
    initial_investment = calculate_initial_investment(params, capacity_kwh, power_kw)

    # 年运营成本
    annual_opex = calculate_annual_opex(params, initial_investment)

    # 日收益计算
    daily_discharge = capacity_kwh * 0.8 * daily_cycles  # 假设80%可用容量
    daily_charge = daily_discharge / round_trip_efficiency

    daily_result = calculate_daily_revenue(params, daily_charge, daily_discharge)
    daily_profit = daily_result['arbitrage_profit']

    # 年收益
    annual_revenue = daily_profit * 365 - annual_opex

    # 静态投资回收期
    if annual_revenue > 0:
        payback_period = initial_investment / annual_revenue
    else:
        payback_period = float('inf')

    # NPV计算
    annual_cash_flows = [annual_revenue] * params.financial_params.project_years
    npv = params.financial_params.calculate_npv(initial_investment, annual_cash_flows)

    return {
        'initial_investment': initial_investment,
        'annual_opex': annual_opex,
        'daily_profit': daily_profit,
        'annual_revenue': annual_revenue,
        'payback_period': payback_period,
        'npv': npv,
        'peak_valley_spread': calculate_peak_valley_spread(params),
    }


# =============================================================================
# 电价曲线生成
# =============================================================================
def get_price_curve(params: EconomicParams, timestep_minutes: int = 15) -> List[float]:
    """生成电价曲线

    Args:
        params: 经济参数
        timestep_minutes: 时间步长

    Returns:
        List[float]: 24小时电价曲线
    """
    return params.price_params.get_price_curve(timestep_minutes)


def plot_price_curve(params: EconomicParams):
    """绘制电价曲线图

    Args:
        params: 经济参数

    Returns:
        matplotlib Figure 或 plotly Figure
    """
    try:
        import plotly.graph_objects as go

        prices = get_price_curve(params, timestep_minutes=15)
        hours = [i * 15 / 60 for i in range(len(prices))]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hours,
            y=prices,
            mode='lines',
            name='电价',
            line=dict(shape='hv', color='#1f77b4', width=2),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.2)'
        ))

        # 添加价格水平线
        price_levels = [
            (params.price_params.price_valley, "谷电价", "green"),
            (params.price_params.price_flat, "平电价", "orange"),
            (params.price_params.price_peak, "峰电价", "red"),
        ]

        for price, name, color in price_levels:
            fig.add_hline(
                y=price,
                line_dash="dash",
                line_color=color,
                annotation_text=f"{name}: {price}元",
                annotation_position="right"
            )

        fig.update_layout(
            title="24小时电价曲线",
            xaxis_title="时间 (小时)",
            yaxis_title="电价 (元/kWh)",
            xaxis=dict(range=[0, 24], dtick=2),
            yaxis=dict(rangemode='tozero'),
            hovermode='x unified'
        )

        return fig

    except ImportError:
        # 使用matplotlib作为后备
        import matplotlib.pyplot as plt

        prices = get_price_curve(params, timestep_minutes=15)
        hours = [i * 15 / 60 for i in range(len(prices))]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.step(hours, prices, where='post', label='电价', color='#1f77b4')
        ax.fill_between(hours, prices, step='post', alpha=0.3)

        ax.axhline(y=params.price_params.price_valley, color='green',
                   linestyle='--', label=f'谷: {params.price_params.price_valley}元')
        ax.axhline(y=params.price_params.price_flat, color='orange',
                   linestyle='--', label=f'平: {params.price_params.price_flat}元')
        ax.axhline(y=params.price_params.price_peak, color='red',
                   linestyle='--', label=f'峰: {params.price_params.price_peak}元')

        ax.set_xlabel('时间 (小时)')
        ax.set_ylabel('电价 (元/kWh)')
        ax.set_title('24小时电价曲线')
        ax.set_xlim(0, 24)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig


# =============================================================================
# Gradio UI组件
# =============================================================================
def create_economic_params_tab():
    """创建经济参数标签页

    Returns:
        Tuple[gr.Tab, Dict]: (标签页, 组件字典)
    """
    with gr.Tab("经济参数") as tab:

        gr.Markdown("### 经济参数配置")
        gr.Markdown("配置电价、成本和财务参数，用于经济性分析。")

        with gr.Row():
            # 左侧：参数配置
            with gr.Column(scale=1):

                # 电价参数
                with gr.Group():
                    gr.Markdown("#### 电价参数 (元/kWh)")
                    with gr.Row():
                        price_valley = gr.Number(
                            label="谷时电价",
                            value=0.4,
                            minimum=0.1,
                            maximum=2.0,
                            step=0.01,
                            info=ECONOMIC_TEACHING_META.get("price_valley", {}).get(
                                "help_text", "低谷时段电价")
                        )
                        price_flat = gr.Number(
                            label="平时电价",
                            value=0.8,
                            minimum=0.1,
                            maximum=3.0,
                            step=0.01,
                            info=ECONOMIC_TEACHING_META.get("price_flat", {}).get(
                                "help_text", "平时段电价")
                        )
                    with gr.Row():
                        price_peak = gr.Number(
                            label="峰时电价",
                            value=1.2,
                            minimum=0.1,
                            maximum=5.0,
                            step=0.01,
                            info=ECONOMIC_TEACHING_META.get("price_peak", {}).get(
                                "help_text", "高峰时段电价")
                        )
                        price_critical = gr.Number(
                            label="尖峰电价 (可选)",
                            value=None,
                            minimum=0.1,
                            maximum=10.0,
                            step=0.01,
                            info="尖峰时段电价（部分地区适用）"
                        )

                    price_feed_in = gr.Number(
                        label="上网电价",
                        value=0.5,
                        minimum=0,
                        maximum=2.0,
                        step=0.01,
                        info="余电上网的结算电价"
                    )

                    # 峰谷价差显示
                    spread_display = gr.Textbox(
                        label="峰谷价差",
                        value="0.80 元/kWh",
                        interactive=False,
                        info="峰谷价差 = 峰时电价 - 谷时电价"
                    )

                # 成本参数
                with gr.Group():
                    gr.Markdown("#### 成本参数")
                    with gr.Row():
                        cost_per_kwh = gr.Number(
                            label="单位容量成本 (元/kWh)",
                            value=1500.0,
                            minimum=500,
                            maximum=5000,
                            step=50,
                            info=ECONOMIC_TEACHING_META.get("cost_per_kwh", {}).get(
                                "help_text", "储能系统单位容量成本")
                        )
                        cost_per_kw = gr.Number(
                            label="单位功率成本 (元/kW)",
                            value=500.0,
                            minimum=100,
                            maximum=2000,
                            step=50,
                            info=ECONOMIC_TEACHING_META.get("cost_per_kw", {}).get(
                                "help_text", "PCS变流器单位功率成本")
                        )
                    with gr.Row():
                        cost_install_ratio = gr.Slider(
                            label="安装成本比例 (%)",
                            minimum=5,
                            maximum=30,
                            value=10.0,
                            step=1,
                            info="安装及配套成本占设备成本的比例"
                        )
                        cost_om_ratio = gr.Slider(
                            label="年运维成本比例 (%)",
                            minimum=0.5,
                            maximum=5,
                            value=2.0,
                            step=0.1,
                            info="年运维成本占初始投资的比例"
                        )

                # 财务参数
                with gr.Group():
                    gr.Markdown("#### 财务参数")
                    with gr.Row():
                        discount_rate = gr.Slider(
                            label="贴现率 (%)",
                            minimum=3,
                            maximum=20,
                            value=8.0,
                            step=0.5,
                            info=ECONOMIC_TEACHING_META.get("discount_rate", {}).get(
                                "help_text", "用于计算NPV的贴现率")
                        )
                        project_years = gr.Slider(
                            label="项目周期 (年)",
                            minimum=5,
                            maximum=25,
                            value=15,
                            step=1,
                            info="经济分析的项目周期"
                        )
                    residual_ratio = gr.Slider(
                        label="残值率 (%)",
                        minimum=0,
                        maximum=20,
                        value=5.0,
                        step=1,
                        info="项目结束时设备残值占初始投资的比例"
                    )

            # 右侧：电价曲线图
            with gr.Column(scale=1):
                gr.Markdown("#### 电价曲线")
                price_curve_plot = gr.Plot(label="24小时电价曲线")

                # 经济计算结果
                gr.Markdown("#### 快速估算")
                gr.Markdown("基于100kWh/50kW系统，日循环1次")

                with gr.Row():
                    investment_display = gr.Textbox(
                        label="初始投资 (万元)",
                        value="",
                        interactive=False
                    )
                    payback_display = gr.Textbox(
                        label="静态回收期 (年)",
                        value="",
                        interactive=False
                    )
                with gr.Row():
                    daily_profit_display = gr.Textbox(
                        label="日套利利润 (元)",
                        value="",
                        interactive=False
                    )
                    annual_revenue_display = gr.Textbox(
                        label="年净收益 (万元)",
                        value="",
                        interactive=False
                    )

        # 操作按钮
        with gr.Row():
            reset_btn = gr.Button("重置为默认值")
            validate_btn = gr.Button("校验参数", variant="primary")
            calc_btn = gr.Button("重新计算", variant="secondary")

        # 校验结果
        validation_output = gr.Textbox(
            label="校验结果",
            value="",
            interactive=False,
            lines=2
        )

    # 返回组件字典
    components = {
        "price_valley": price_valley,
        "price_flat": price_flat,
        "price_peak": price_peak,
        "price_critical": price_critical,
        "price_feed_in": price_feed_in,
        "spread_display": spread_display,
        "cost_per_kwh": cost_per_kwh,
        "cost_per_kw": cost_per_kw,
        "cost_install_ratio": cost_install_ratio,
        "cost_om_ratio": cost_om_ratio,
        "discount_rate": discount_rate,
        "project_years": project_years,
        "residual_ratio": residual_ratio,
        "price_curve_plot": price_curve_plot,
        "investment_display": investment_display,
        "payback_display": payback_display,
        "daily_profit_display": daily_profit_display,
        "annual_revenue_display": annual_revenue_display,
        "reset_btn": reset_btn,
        "validate_btn": validate_btn,
        "calc_btn": calc_btn,
        "validation_output": validation_output,
    }

    return tab, components


def setup_economic_params_events(components: Dict[str, Any]):
    """设置经济参数事件绑定

    Args:
        components: 组件字典
    """

    def update_spread(price_valley, price_peak):
        """更新峰谷价差"""
        spread = price_peak - price_valley
        return f"{spread:.2f} 元/kWh"

    def update_price_curve(price_valley, price_flat, price_peak, price_critical):
        """更新电价曲线图"""
        params = create_default_economic_params()
        params.price_params.price_valley = price_valley
        params.price_params.price_flat = price_flat
        params.price_params.price_peak = price_peak
        params.price_params.price_critical = price_critical

        return plot_price_curve(params)

    def calculate_economics(price_valley, price_flat, price_peak, price_critical,
                            price_feed_in, cost_per_kwh, cost_per_kw,
                            cost_install_ratio, cost_om_ratio,
                            discount_rate, project_years, residual_ratio):
        """计算经济指标"""
        # 创建参数对象
        price_params = ElectricityPriceParams(
            price_valley=price_valley,
            price_flat=price_flat,
            price_peak=price_peak,
            price_critical=price_critical,
            price_feed_in=price_feed_in,
        )
        cost_params = CostParams(
            cost_per_kwh=cost_per_kwh,
            cost_per_kw=cost_per_kw,
            cost_install_ratio=cost_install_ratio,
            cost_om_ratio=cost_om_ratio,
        )
        financial_params = FinancialParams(
            discount_rate=discount_rate,
            project_years=int(project_years),
            residual_ratio=residual_ratio,
        )
        params = EconomicParams(
            price_params=price_params,
            cost_params=cost_params,
            financial_params=financial_params,
        )

        # 计算经济指标 (假设100kWh/50kW系统)
        result = calculate_full_economics(params, 100, 50, daily_cycles=1.0)

        investment = f"{result['initial_investment'] / 10000:.2f}"
        payback = f"{result['payback_period']:.1f}" if result['payback_period'] < 100 else "无法回收"
        daily_profit = f"{result['daily_profit']:.2f}"
        annual_revenue = f"{result['annual_revenue'] / 10000:.2f}"

        # 峰谷价差
        spread = f"{price_peak - price_valley:.2f} 元/kWh"

        # 电价曲线
        fig = plot_price_curve(params)

        return investment, payback, daily_profit, annual_revenue, spread, fig

    def on_validate(price_valley, price_flat, price_peak, price_critical,
                    cost_per_kwh, cost_per_kw, cost_install_ratio, cost_om_ratio,
                    discount_rate, project_years, residual_ratio):
        """校验参数"""
        params_dict = {
            "price_valley": price_valley,
            "price_flat": price_flat,
            "price_peak": price_peak,
            "price_critical": price_critical,
            "cost_per_kwh": cost_per_kwh,
            "cost_per_kw": cost_per_kw,
            "cost_install_ratio": cost_install_ratio,
            "cost_om_ratio": cost_om_ratio,
            "discount_rate": discount_rate,
            "project_years": project_years,
            "residual_ratio": residual_ratio,
        }

        ok, errors = _validate_economic_params(params_dict)
        if ok:
            return "✅ 参数校验通过！"
        else:
            return "❌ 校验失败:\n" + "\n".join(f"• {e}" for e in errors)

    def on_reset():
        """重置参数"""
        defaults = get_default_economic_params()
        return (
            defaults["price_valley"],
            defaults["price_flat"],
            defaults["price_peak"],
            None,  # price_critical
            defaults["price_feed_in"],
            defaults["cost_per_kwh"],
            defaults["cost_per_kw"],
            defaults["cost_install_ratio"],
            defaults["cost_om_ratio"],
            defaults["discount_rate"],
            defaults["project_years"],
            defaults["residual_ratio"],
            "✅ 已重置为默认参数"
        )

    # 计算输入
    calc_inputs = [
        components["price_valley"],
        components["price_flat"],
        components["price_peak"],
        components["price_critical"],
        components["price_feed_in"],
        components["cost_per_kwh"],
        components["cost_per_kw"],
        components["cost_install_ratio"],
        components["cost_om_ratio"],
        components["discount_rate"],
        components["project_years"],
        components["residual_ratio"],
    ]

    calc_outputs = [
        components["investment_display"],
        components["payback_display"],
        components["daily_profit_display"],
        components["annual_revenue_display"],
        components["spread_display"],
        components["price_curve_plot"],
    ]

    # 绑定计算按钮
    components["calc_btn"].click(
        fn=calculate_economics,
        inputs=calc_inputs,
        outputs=calc_outputs
    )

    # 绑定价格变化自动更新峰谷价差
    for price_input in [components["price_valley"], components["price_peak"]]:
        price_input.change(
            fn=update_spread,
            inputs=[components["price_valley"], components["price_peak"]],
            outputs=components["spread_display"]
        )

    # 绑定校验按钮
    validate_inputs = [
        components["price_valley"],
        components["price_flat"],
        components["price_peak"],
        components["price_critical"],
        components["cost_per_kwh"],
        components["cost_per_kw"],
        components["cost_install_ratio"],
        components["cost_om_ratio"],
        components["discount_rate"],
        components["project_years"],
        components["residual_ratio"],
    ]

    components["validate_btn"].click(
        fn=on_validate,
        inputs=validate_inputs,
        outputs=components["validation_output"]
    )

    # 绑定重置按钮
    reset_outputs = [
        components["price_valley"],
        components["price_flat"],
        components["price_peak"],
        components["price_critical"],
        components["price_feed_in"],
        components["cost_per_kwh"],
        components["cost_per_kw"],
        components["cost_install_ratio"],
        components["cost_om_ratio"],
        components["discount_rate"],
        components["project_years"],
        components["residual_ratio"],
        components["validation_output"],
    ]

    components["reset_btn"].click(
        fn=on_reset,
        inputs=[],
        outputs=reset_outputs
    )
