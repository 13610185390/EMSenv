# -*- coding: utf-8 -*-
"""基础参数模块

对应技术设计文档：01_基础参数模块技术设计.md
负责BESS参数配置、校验、UI展示
"""

import json
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import asdict

import gradio as gr

from models.bess import (
    BESSParams, BatteryType,
    BESS_TEACHING_META, BESS_CONSTRAINTS
)
from config.default_params import (
    get_default_bess_params, create_default_bess_params
)
from utils.validators import validate_bess_params as _validate_bess_params


# =============================================================================
# 模块状态
# =============================================================================
_current_params: Optional[BESSParams] = None


# =============================================================================
# 参数管理函数
# =============================================================================
def get_bess_params() -> BESSParams:
    """获取当前BESS参数配置

    Returns:
        BESSParams: BESS参数数据类实例
    """
    global _current_params
    if _current_params is None:
        _current_params = create_default_bess_params()
    return _current_params


def set_bess_params(params: BESSParams) -> Tuple[bool, List[str]]:
    """设置BESS参数

    Args:
        params: BESS参数数据类实例

    Returns:
        Tuple[bool, List[str]]: (是否成功, 错误信息列表)
    """
    global _current_params

    # 校验参数
    ok, errors = validate_bess_params(params)
    if not ok:
        return False, errors

    _current_params = params
    return True, []


def validate_bess_params(params: BESSParams) -> Tuple[bool, List[str]]:
    """校验BESS参数

    Args:
        params: 待校验的参数

    Returns:
        Tuple[bool, List[str]]: (是否通过, 错误信息列表)
    """
    # 转换为字典进行校验
    params_dict = params.to_dict()
    return _validate_bess_params(params_dict)


def reset_to_default() -> BESSParams:
    """重置为默认参数

    Returns:
        BESSParams: 默认参数实例
    """
    global _current_params
    _current_params = create_default_bess_params()
    return _current_params


def export_params(params: BESSParams, filepath: str) -> Tuple[bool, str]:
    """导出参数到JSON文件

    Args:
        params: 参数实例
        filepath: 导出路径

    Returns:
        Tuple[bool, str]: (是否成功, 消息)
    """
    try:
        data = params.to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True, f"参数已导出到 {filepath}"
    except Exception as e:
        return False, f"导出失败: {str(e)}"


def import_params(filepath: str) -> Tuple[Optional[BESSParams], str]:
    """从JSON文件导入参数

    Args:
        filepath: 文件路径

    Returns:
        Tuple[Optional[BESSParams], str]: (参数实例或None, 消息)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        params = BESSParams.from_dict(data)

        # 校验导入的参数
        ok, errors = validate_bess_params(params)
        if not ok:
            return None, f"参数校验失败: {'; '.join(errors)}"

        return params, "参数导入成功"
    except Exception as e:
        return None, f"导入失败: {str(e)}"


# =============================================================================
# 教学提示函数
# =============================================================================
def get_param_help(param_name: str) -> str:
    """获取参数帮助文本

    Args:
        param_name: 参数名称

    Returns:
        str: 帮助文本（Markdown格式）
    """
    meta = BESS_TEACHING_META.get(param_name)
    if not meta:
        return ""

    help_text = f"**{meta.help_text}**\n\n"

    if meta.impact_desc:
        help_text += f"影响: {meta.impact_desc}\n\n"

    if meta.typical_range:
        help_text += f"典型范围: {meta.typical_range}\n\n"

    if meta.warning_conditions:
        help_text += "注意:\n"
        for warning in meta.warning_conditions:
            help_text += f"- {warning}\n"

    if meta.learning_points:
        help_text += f"\n关联知识点: {', '.join(meta.learning_points)}"

    return help_text


def get_param_impact_info(param_name: str, old_value: Any, new_value: Any) -> str:
    """获取参数变化影响提示

    Args:
        param_name: 参数名称
        old_value: 原值
        new_value: 新值

    Returns:
        str: 影响提示文本
    """
    meta = BESS_TEACHING_META.get(param_name)
    if not meta:
        return ""

    change = "增加" if new_value > old_value else "减少"

    # 特定参数的影响提示
    impact_hints = {
        "capacity": f"容量{change}后，可调度能量将{change}",
        "power_rated": f"功率{change}后，充放电速率将{change}",
        "efficiency_charge": f"充电效率{change}后，充电损耗将{'减少' if change == '增加' else '增加'}",
        "efficiency_discharge": f"放电效率{change}后，放电损耗将{'减少' if change == '增加' else '增加'}",
        "soc_min": f"SOC下限{change}后，可用容量将{'减少' if change == '增加' else '增加'}",
        "soc_max": f"SOC上限{change}后，可用容量将{change}",
        "cycle_life": f"循环寿命{change}后，预计使用年限将{change}",
    }

    return impact_hints.get(param_name, meta.impact_desc)


# =============================================================================
# 参数联动逻辑
# =============================================================================
def _on_param_change(
    param_name: str,
    value: Any,
    current_params: Dict[str, Any]
) -> Dict[str, Any]:
    """参数变更回调处理

    处理参数间的联动关系

    Args:
        param_name: 变更的参数名
        value: 新值
        current_params: 当前所有参数

    Returns:
        Dict[str, Any]: 需要联动更新的参数
    """
    updates = {}

    # 额定功率变更时，更新充放电功率上限
    if param_name == "power_rated":
        # 如果充电功率超过新的额定功率，调整
        if current_params.get("power_charge_max", 0) > value:
            updates["power_charge_max"] = value
        # 如果放电功率超过新的额定功率，调整
        if current_params.get("power_discharge_max", 0) > value:
            updates["power_discharge_max"] = value

    # SOC下限变更时，检查初始SOC
    if param_name == "soc_min":
        if current_params.get("soc_init", 50) < value:
            updates["soc_init"] = value

    # SOC上限变更时，检查初始SOC
    if param_name == "soc_max":
        if current_params.get("soc_init", 50) > value:
            updates["soc_init"] = value

    return updates


# =============================================================================
# Gradio UI组件
# =============================================================================
def create_basic_params_tab():
    """创建基础参数标签页

    Returns:
        Tuple[gr.Tab, Dict]: (标签页, 组件字典)
    """
    with gr.Tab("基础参数") as tab:

        gr.Markdown("### BESS储能系统参数配置")
        gr.Markdown("配置电池储能系统的基本物理参数。悬停参数名称可查看帮助信息。")

        # 设备基本信息
        with gr.Group():
            gr.Markdown("#### 设备信息")
            with gr.Row():
                name_input = gr.Textbox(
                    label="设备名称",
                    value="BESS_01",
                    info="储能系统的标识名称"
                )
                battery_type = gr.Dropdown(
                    label="电池类型",
                    choices=[
                        ("磷酸铁锂", "LFP"),
                        ("三元锂电池", "NMC"),
                        ("锂电池", "LITHIUM_ION"),
                        ("铅酸电池", "LEAD_ACID"),
                    ],
                    value="LFP",
                    info="选择电池的化学类型"
                )
                enabled_checkbox = gr.Checkbox(
                    label="启用",
                    value=True,
                    info="是否启用该储能设备"
                )

        # 容量与功率参数
        with gr.Group():
            gr.Markdown("#### 容量与功率")
            with gr.Row():
                capacity_input = gr.Number(
                    label="额定容量 (kWh)",
                    value=100.0,
                    minimum=10,
                    maximum=10000,
                    info=BESS_TEACHING_META.get("capacity").help_text
                )
                power_rated_input = gr.Number(
                    label="额定功率 (kW)",
                    value=50.0,
                    minimum=5,
                    maximum=5000,
                    info=BESS_TEACHING_META.get("power_rated").help_text
                )

            with gr.Row():
                power_charge_max_input = gr.Number(
                    label="充电功率上限 (kW)",
                    value=50.0,
                    minimum=0,
                    info=BESS_TEACHING_META.get("power_charge_max").help_text
                )
                power_discharge_max_input = gr.Number(
                    label="放电功率上限 (kW)",
                    value=50.0,
                    minimum=0,
                    info=BESS_TEACHING_META.get("power_discharge_max").help_text
                )

            # 储能时长显示
            duration_display = gr.Textbox(
                label="储能时长",
                value="2.0 小时",
                interactive=False,
                info="储能时长 = 容量 / 功率"
            )

        # 效率参数
        with gr.Group():
            gr.Markdown("#### 效率参数")
            with gr.Row():
                efficiency_charge_input = gr.Slider(
                    label="充电效率 (%)",
                    minimum=80,
                    maximum=99,
                    value=95.0,
                    step=0.5,
                    info=BESS_TEACHING_META.get("efficiency_charge").help_text
                )
                efficiency_discharge_input = gr.Slider(
                    label="放电效率 (%)",
                    minimum=80,
                    maximum=99,
                    value=95.0,
                    step=0.5,
                    info=BESS_TEACHING_META.get("efficiency_discharge").help_text
                )

            with gr.Row():
                self_discharge_input = gr.Number(
                    label="自放电率 (%/天)",
                    value=0.1,
                    minimum=0,
                    maximum=5,
                    step=0.01,
                    info=BESS_TEACHING_META.get("self_discharge_rate").help_text
                )
                round_trip_eff_display = gr.Textbox(
                    label="往返效率",
                    value="90.25%",
                    interactive=False,
                    info="往返效率 = 充电效率 × 放电效率"
                )

        # SOC参数
        with gr.Group():
            gr.Markdown("#### SOC参数")
            with gr.Row():
                soc_min_input = gr.Slider(
                    label="SOC下限 (%)",
                    minimum=0,
                    maximum=50,
                    value=10.0,
                    step=1,
                    info=BESS_TEACHING_META.get("soc_min").help_text
                )
                soc_max_input = gr.Slider(
                    label="SOC上限 (%)",
                    minimum=50,
                    maximum=100,
                    value=90.0,
                    step=1,
                    info=BESS_TEACHING_META.get("soc_max").help_text
                )

            with gr.Row():
                soc_init_input = gr.Slider(
                    label="初始SOC (%)",
                    minimum=0,
                    maximum=100,
                    value=50.0,
                    step=1,
                    info=BESS_TEACHING_META.get("soc_init").help_text
                )
                usable_capacity_display = gr.Textbox(
                    label="可用容量",
                    value="80.0 kWh (80%)",
                    interactive=False,
                    info="可用容量 = 额定容量 × (SOC上限 - SOC下限)"
                )

        # 寿命参数
        with gr.Group():
            gr.Markdown("#### 寿命参数")
            with gr.Row():
                cycle_life_input = gr.Number(
                    label="循环寿命 (次)",
                    value=6000,
                    minimum=1000,
                    maximum=15000,
                    step=100,
                    info=BESS_TEACHING_META.get("cycle_life").help_text
                )
                calendar_life_input = gr.Number(
                    label="日历寿命 (年)",
                    value=15,
                    minimum=5,
                    maximum=25,
                    step=1,
                    info=BESS_TEACHING_META.get("calendar_life").help_text
                )
                degradation_input = gr.Number(
                    label="容量衰减率 (%/年)",
                    value=2.0,
                    minimum=0,
                    maximum=10,
                    step=0.1,
                    info=BESS_TEACHING_META.get("degradation_rate").help_text
                )

        # 操作按钮
        with gr.Row():
            reset_btn = gr.Button("重置为默认值")
            validate_btn = gr.Button("校验参数", variant="primary")

        # 校验结果显示
        validation_output = gr.Textbox(
            label="校验结果",
            value="",
            interactive=False,
            lines=3
        )

        # 导入导出
        with gr.Accordion("导入/导出", open=False):
            with gr.Row():
                export_btn = gr.Button("导出参数")
                import_file = gr.File(
                    label="导入参数文件",
                    file_types=[".json"]
                )

            export_output = gr.File(label="下载", visible=False)

    # 返回组件字典
    components = {
        "name": name_input,
        "battery_type": battery_type,
        "enabled": enabled_checkbox,
        "capacity": capacity_input,
        "power_rated": power_rated_input,
        "power_charge_max": power_charge_max_input,
        "power_discharge_max": power_discharge_max_input,
        "duration_display": duration_display,
        "efficiency_charge": efficiency_charge_input,
        "efficiency_discharge": efficiency_discharge_input,
        "self_discharge_rate": self_discharge_input,
        "round_trip_eff_display": round_trip_eff_display,
        "soc_min": soc_min_input,
        "soc_max": soc_max_input,
        "soc_init": soc_init_input,
        "usable_capacity_display": usable_capacity_display,
        "cycle_life": cycle_life_input,
        "calendar_life": calendar_life_input,
        "degradation_rate": degradation_input,
        "reset_btn": reset_btn,
        "validate_btn": validate_btn,
        "validation_output": validation_output,
        "export_btn": export_btn,
        "import_file": import_file,
        "export_output": export_output,
    }

    return tab, components


def setup_basic_params_events(components: Dict[str, Any]):
    """设置基础参数事件绑定

    Args:
        components: 组件字典
    """

    def update_derived_values(capacity, power_rated, eff_charge, eff_discharge,
                               soc_min, soc_max):
        """更新派生显示值"""
        # 储能时长
        duration = capacity / power_rated if power_rated > 0 else 0
        duration_text = f"{duration:.2f} 小时"

        # 往返效率
        round_trip = eff_charge * eff_discharge / 100
        round_trip_text = f"{round_trip:.2f}%"

        # 可用容量
        usable = capacity * (soc_max - soc_min) / 100
        usable_pct = soc_max - soc_min
        usable_text = f"{usable:.1f} kWh ({usable_pct:.0f}%)"

        return duration_text, round_trip_text, usable_text

    def on_validate_click(name, battery_type, capacity, power_rated,
                          power_charge_max, power_discharge_max,
                          eff_charge, eff_discharge, self_discharge,
                          soc_min, soc_max, soc_init,
                          cycle_life, calendar_life, degradation):
        """校验按钮点击"""
        params_dict = {
            "name": name,
            "battery_type": battery_type,
            "capacity": capacity,
            "power_rated": power_rated,
            "power_charge_max": power_charge_max,
            "power_discharge_max": power_discharge_max,
            "efficiency_charge": eff_charge,
            "efficiency_discharge": eff_discharge,
            "self_discharge_rate": self_discharge,
            "soc_min": soc_min,
            "soc_max": soc_max,
            "soc_init": soc_init,
            "cycle_life": cycle_life,
            "calendar_life": calendar_life,
            "degradation_rate": degradation,
        }

        ok, errors = _validate_bess_params(params_dict)

        if ok:
            return "✅ 参数校验通过！所有参数配置正确。"
        else:
            return "❌ 参数校验失败:\n" + "\n".join(f"• {e}" for e in errors)

    def on_reset_click():
        """重置按钮点击"""
        defaults = get_default_bess_params()
        return (
            "BESS_01",  # name
            "LFP",      # battery_type
            defaults["capacity"],
            defaults["power_rated"],
            defaults["power_charge_max"] or defaults["power_rated"],
            defaults["power_discharge_max"] or defaults["power_rated"],
            defaults["efficiency_charge"],
            defaults["efficiency_discharge"],
            defaults["self_discharge_rate"] if "self_discharge_rate" in defaults else 0.1,
            defaults["soc_min"],
            defaults["soc_max"],
            defaults["soc_init"],
            defaults["cycle_life"],
            defaults["calendar_life"],
            defaults["degradation_rate"],
            "✅ 已重置为默认参数"
        )

    # 绑定更新派生值
    update_inputs = [
        components["capacity"],
        components["power_rated"],
        components["efficiency_charge"],
        components["efficiency_discharge"],
        components["soc_min"],
        components["soc_max"],
    ]
    update_outputs = [
        components["duration_display"],
        components["round_trip_eff_display"],
        components["usable_capacity_display"],
    ]

    for inp in update_inputs:
        inp.change(
            fn=update_derived_values,
            inputs=update_inputs,
            outputs=update_outputs
        )

    # 绑定校验按钮
    validate_inputs = [
        components["name"],
        components["battery_type"],
        components["capacity"],
        components["power_rated"],
        components["power_charge_max"],
        components["power_discharge_max"],
        components["efficiency_charge"],
        components["efficiency_discharge"],
        components["self_discharge_rate"],
        components["soc_min"],
        components["soc_max"],
        components["soc_init"],
        components["cycle_life"],
        components["calendar_life"],
        components["degradation_rate"],
    ]

    components["validate_btn"].click(
        fn=on_validate_click,
        inputs=validate_inputs,
        outputs=components["validation_output"]
    )

    # 绑定重置按钮
    reset_outputs = [
        components["name"],
        components["battery_type"],
        components["capacity"],
        components["power_rated"],
        components["power_charge_max"],
        components["power_discharge_max"],
        components["efficiency_charge"],
        components["efficiency_discharge"],
        components["self_discharge_rate"],
        components["soc_min"],
        components["soc_max"],
        components["soc_init"],
        components["cycle_life"],
        components["calendar_life"],
        components["degradation_rate"],
        components["validation_output"],
    ]

    components["reset_btn"].click(
        fn=on_reset_click,
        inputs=[],
        outputs=reset_outputs
    )


def get_params_from_ui(components: Dict[str, Any]) -> BESSParams:
    """从UI组件获取参数值并创建BESSParams实例

    Args:
        components: 组件字典（包含值）

    Returns:
        BESSParams: 参数实例
    """
    # 解析电池类型
    battery_type_str = components.get("battery_type", "LFP")
    battery_type = BatteryType.LFP
    for bt in BatteryType:
        if bt.name == battery_type_str or bt.value == battery_type_str:
            battery_type = bt
            break

    return BESSParams(
        name=components.get("name", "BESS_01"),
        battery_type=battery_type,
        enabled=components.get("enabled", True),
        capacity=components.get("capacity", 100.0),
        power_rated=components.get("power_rated", 50.0),
        power_charge_max=components.get("power_charge_max"),
        power_discharge_max=components.get("power_discharge_max"),
        efficiency_charge=components.get("efficiency_charge", 95.0),
        efficiency_discharge=components.get("efficiency_discharge", 95.0),
        self_discharge_rate=components.get("self_discharge_rate", 0.1),
        soc_min=components.get("soc_min", 10.0),
        soc_max=components.get("soc_max", 90.0),
        soc_init=components.get("soc_init", 50.0),
        cycle_life=int(components.get("cycle_life", 6000)),
        calendar_life=int(components.get("calendar_life", 15)),
        degradation_rate=components.get("degradation_rate", 2.0),
    )
