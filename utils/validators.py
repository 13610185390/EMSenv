# -*- coding: utf-8 -*-
"""参数校验工具

对应开发规划文档：2.2节 utils/validators.py
提供参数范围校验、依赖校验、完整性校验等功能
"""

from typing import Any, Dict, List, Tuple, Optional, Union
from datetime import time


# =============================================================================
# 基础校验函数
# =============================================================================
def validate_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    param_name: str = "参数"
) -> Tuple[bool, str]:
    """范围校验

    Args:
        value: 待校验值
        min_value: 最小值（None表示无下限）
        max_value: 最大值（None表示无上限）
        param_name: 参数名称（用于错误信息）

    Returns:
        Tuple[bool, str]: (是否通过, 错误信息)
    """
    if value is None:
        return False, f"{param_name}不能为空"

    if min_value is not None and value < min_value:
        return False, f"{param_name}({value})不能小于{min_value}"

    if max_value is not None and value > max_value:
        return False, f"{param_name}({value})不能大于{max_value}"

    return True, ""


def validate_required(
    value: Any,
    param_name: str = "参数"
) -> Tuple[bool, str]:
    """必填校验

    Args:
        value: 待校验值
        param_name: 参数名称

    Returns:
        Tuple[bool, str]: (是否通过, 错误信息)
    """
    if value is None:
        return False, f"{param_name}为必填项"

    if isinstance(value, str) and value.strip() == "":
        return False, f"{param_name}不能为空字符串"

    return True, ""


def validate_positive(
    value: Union[int, float],
    param_name: str = "参数",
    allow_zero: bool = False
) -> Tuple[bool, str]:
    """正数校验

    Args:
        value: 待校验值
        param_name: 参数名称
        allow_zero: 是否允许为0

    Returns:
        Tuple[bool, str]: (是否通过, 错误信息)
    """
    if value is None:
        return False, f"{param_name}不能为空"

    if allow_zero:
        if value < 0:
            return False, f"{param_name}({value})不能为负数"
    else:
        if value <= 0:
            return False, f"{param_name}({value})必须为正数"

    return True, ""


def validate_percentage(
    value: Union[int, float],
    param_name: str = "参数"
) -> Tuple[bool, str]:
    """百分比校验 (0-100)

    Args:
        value: 待校验值
        param_name: 参数名称

    Returns:
        Tuple[bool, str]: (是否通过, 错误信息)
    """
    return validate_range(value, 0, 100, param_name)


def validate_dependency(
    params: Dict[str, Any],
    param_name: str,
    depends_on: str,
    condition: str = "less_than_or_equal"
) -> Tuple[bool, str]:
    """依赖校验

    Args:
        params: 参数字典
        param_name: 待校验参数名
        depends_on: 依赖的参数名
        condition: 条件类型 (less_than_or_equal, greater_than_or_equal, less_than, greater_than)

    Returns:
        Tuple[bool, str]: (是否通过, 错误信息)
    """
    value = params.get(param_name)
    dep_value = params.get(depends_on)

    if value is None or dep_value is None:
        return True, ""  # 如果任一为空，跳过依赖校验

    conditions = {
        "less_than_or_equal": (value <= dep_value, f"{param_name}({value})不能大于{depends_on}({dep_value})"),
        "greater_than_or_equal": (value >= dep_value, f"{param_name}({value})不能小于{depends_on}({dep_value})"),
        "less_than": (value < dep_value, f"{param_name}({value})必须小于{depends_on}({dep_value})"),
        "greater_than": (value > dep_value, f"{param_name}({value})必须大于{depends_on}({dep_value})"),
    }

    result, msg = conditions.get(condition, (True, ""))
    return (True, "") if result else (False, msg)


# =============================================================================
# BESS参数校验
# =============================================================================
def validate_bess_params(params: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """校验BESS参数

    Args:
        params: BESS参数字典

    Returns:
        Tuple[bool, List[str]]: (是否通过, 错误信息列表)
    """
    errors = []

    # 容量校验
    ok, msg = validate_range(params.get("capacity"), 10, 10000, "容量")
    if not ok:
        errors.append(msg)

    # 额定功率校验
    ok, msg = validate_range(params.get("power_rated"), 5, 5000, "额定功率")
    if not ok:
        errors.append(msg)

    # 充电功率上限校验
    power_charge_max = params.get("power_charge_max")
    if power_charge_max is not None:
        ok, msg = validate_positive(power_charge_max, "充电功率上限", allow_zero=False)
        if not ok:
            errors.append(msg)
        else:
            power_rated = params.get("power_rated", 0)
            if power_charge_max > power_rated * 1.5:
                errors.append(f"充电功率上限({power_charge_max})不宜超过额定功率的1.5倍({power_rated * 1.5})")

    # 放电功率上限校验
    power_discharge_max = params.get("power_discharge_max")
    if power_discharge_max is not None:
        ok, msg = validate_positive(power_discharge_max, "放电功率上限", allow_zero=False)
        if not ok:
            errors.append(msg)
        else:
            power_rated = params.get("power_rated", 0)
            if power_discharge_max > power_rated * 1.5:
                errors.append(f"放电功率上限({power_discharge_max})不宜超过额定功率的1.5倍({power_rated * 1.5})")

    # 效率校验
    ok, msg = validate_range(params.get("efficiency_charge"), 80, 99, "充电效率")
    if not ok:
        errors.append(msg)

    ok, msg = validate_range(params.get("efficiency_discharge"), 80, 99, "放电效率")
    if not ok:
        errors.append(msg)

    # SOC参数校验
    soc_min = params.get("soc_min", 0)
    soc_max = params.get("soc_max", 100)
    soc_init = params.get("soc_init", 50)

    ok, msg = validate_range(soc_min, 0, 50, "SOC下限")
    if not ok:
        errors.append(msg)

    ok, msg = validate_range(soc_max, 50, 100, "SOC上限")
    if not ok:
        errors.append(msg)

    # SOC依赖校验
    if soc_min >= soc_max:
        errors.append(f"SOC下限({soc_min})必须小于SOC上限({soc_max})")

    if soc_init < soc_min or soc_init > soc_max:
        errors.append(f"初始SOC({soc_init})必须在SOC下限({soc_min})和上限({soc_max})之间")

    # 寿命参数校验
    ok, msg = validate_range(params.get("cycle_life"), 1000, 15000, "循环寿命")
    if not ok:
        errors.append(msg)

    ok, msg = validate_range(params.get("calendar_life"), 5, 25, "日历寿命")
    if not ok:
        errors.append(msg)

    # 容量功率比校验（储能时长）
    capacity = params.get("capacity", 100)
    power_rated = params.get("power_rated", 50)
    if power_rated > 0:
        duration = capacity / power_rated
        if duration < 0.5:
            errors.append(f"储能时长({duration:.2f}h)过短，建议不小于0.5小时")
        elif duration > 4:
            errors.append(f"储能时长({duration:.2f}h)较长，请确认配置是否合理")

    return len(errors) == 0, errors


# =============================================================================
# 经济参数校验
# =============================================================================
def validate_economic_params(params: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """校验经济参数

    Args:
        params: 经济参数字典

    Returns:
        Tuple[bool, List[str]]: (是否通过, 错误信息列表)
    """
    errors = []

    # 电价校验
    price_valley = params.get("price_valley", 0)
    price_flat = params.get("price_flat", 0)
    price_peak = params.get("price_peak", 0)

    ok, msg = validate_positive(price_valley, "谷时电价", allow_zero=False)
    if not ok:
        errors.append(msg)

    ok, msg = validate_positive(price_flat, "平时电价", allow_zero=False)
    if not ok:
        errors.append(msg)

    ok, msg = validate_positive(price_peak, "峰时电价", allow_zero=False)
    if not ok:
        errors.append(msg)

    # 电价逻辑校验
    if price_valley > price_flat:
        errors.append(f"谷时电价({price_valley})不应高于平时电价({price_flat})")

    if price_flat > price_peak:
        errors.append(f"平时电价({price_flat})不应高于峰时电价({price_peak})")

    # 尖峰电价校验（可选）
    price_critical = params.get("price_critical")
    if price_critical is not None:
        ok, msg = validate_positive(price_critical, "尖峰电价", allow_zero=False)
        if not ok:
            errors.append(msg)
        elif price_critical < price_peak:
            errors.append(f"尖峰电价({price_critical})不应低于峰时电价({price_peak})")

    # 上网电价校验（可选）
    price_feed_in = params.get("price_feed_in")
    if price_feed_in is not None:
        ok, msg = validate_positive(price_feed_in, "上网电价", allow_zero=True)
        if not ok:
            errors.append(msg)

    # 成本参数校验
    ok, msg = validate_range(params.get("cost_per_kwh"), 500, 5000, "单位容量成本")
    if not ok:
        errors.append(msg)

    ok, msg = validate_range(params.get("cost_per_kw"), 100, 2000, "单位功率成本")
    if not ok:
        errors.append(msg)

    ok, msg = validate_range(params.get("cost_install_ratio"), 5, 30, "安装成本比例")
    if not ok:
        errors.append(msg)

    ok, msg = validate_range(params.get("cost_om_ratio"), 0.5, 5, "运维成本比例")
    if not ok:
        errors.append(msg)

    # 财务参数校验
    ok, msg = validate_range(params.get("discount_rate"), 3, 20, "贴现率")
    if not ok:
        errors.append(msg)

    ok, msg = validate_range(params.get("project_years"), 5, 25, "项目周期")
    if not ok:
        errors.append(msg)

    ok, msg = validate_range(params.get("residual_ratio"), 0, 20, "残值率")
    if not ok:
        errors.append(msg)

    return len(errors) == 0, errors


# =============================================================================
# 控制参数校验
# =============================================================================
def validate_control_params(params: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """校验控制参数

    Args:
        params: 控制参数字典

    Returns:
        Tuple[bool, List[str]]: (是否通过, 错误信息列表)
    """
    errors = []

    # 保护参数校验
    protect_soc_high = params.get("protect_soc_high", 95)
    protect_soc_low = params.get("protect_soc_low", 5)

    ok, msg = validate_range(protect_soc_high, 80, 100, "过充保护阈值")
    if not ok:
        errors.append(msg)

    ok, msg = validate_range(protect_soc_low, 0, 20, "过放保护阈值")
    if not ok:
        errors.append(msg)

    if protect_soc_low >= protect_soc_high:
        errors.append(f"过放保护阈值({protect_soc_low})必须小于过充保护阈值({protect_soc_high})")

    # 功率限制系数校验
    ok, msg = validate_range(params.get("power_limit_factor"), 0.5, 1.0, "功率限制系数")
    if not ok:
        errors.append(msg)

    # 温度保护校验
    protect_temp_high = params.get("protect_temp_high", 45)
    protect_temp_low = params.get("protect_temp_low", 0)

    ok, msg = validate_range(protect_temp_high, 35, 60, "高温保护阈值")
    if not ok:
        errors.append(msg)

    ok, msg = validate_range(protect_temp_low, -20, 15, "低温保护阈值")
    if not ok:
        errors.append(msg)

    if protect_temp_low >= protect_temp_high:
        errors.append(f"低温保护阈值({protect_temp_low})必须小于高温保护阈值({protect_temp_high})")

    # 响应参数校验
    ok, msg = validate_range(params.get("response_time"), 10, 1000, "响应时间")
    if not ok:
        errors.append(msg)

    ok, msg = validate_range(params.get("ramp_rate"), 1, 100, "爬坡速率")
    if not ok:
        errors.append(msg)

    return len(errors) == 0, errors


# =============================================================================
# 时段校验
# =============================================================================
def validate_time_periods(
    periods: List[Dict[str, Any]]
) -> Tuple[bool, List[str]]:
    """校验时段配置

    检查：
    1. 时段格式正确
    2. 时段无重叠
    3. 覆盖完整24小时

    Args:
        periods: 时段列表，每个时段包含 start, end, period_type

    Returns:
        Tuple[bool, List[str]]: (是否通过, 错误信息列表)
    """
    errors = []

    if not periods:
        errors.append("时段配置不能为空")
        return False, errors

    # 转换为分钟进行处理
    time_slots = []  # [(start_minutes, end_minutes, period_type)]

    for i, period in enumerate(periods):
        try:
            start = period.get("start")
            end = period.get("end")
            period_type = period.get("period_type", "unknown")

            # 解析时间
            if isinstance(start, time):
                start_min = start.hour * 60 + start.minute
            elif isinstance(start, str):
                h, m = map(int, start.split(":"))
                start_min = h * 60 + m
            else:
                errors.append(f"时段{i + 1}的开始时间格式错误")
                continue

            if isinstance(end, time):
                end_min = end.hour * 60 + end.minute
            elif isinstance(end, str):
                h, m = map(int, end.split(":"))
                end_min = h * 60 + m
            else:
                errors.append(f"时段{i + 1}的结束时间格式错误")
                continue

            # 处理跨日情况
            if end_min == 0:
                end_min = 24 * 60  # 24:00 = 1440分钟

            time_slots.append((start_min, end_min, period_type))

        except Exception as e:
            errors.append(f"时段{i + 1}解析错误: {str(e)}")

    if errors:
        return False, errors

    # 按开始时间排序
    time_slots.sort(key=lambda x: x[0])

    # 检查重叠和间隙
    covered_minutes = set()
    for start_min, end_min, period_type in time_slots:
        # 检查重叠
        for m in range(start_min, end_min):
            if m in covered_minutes:
                h, mi = divmod(m, 60)
                errors.append(f"时段在{h:02d}:{mi:02d}存在重叠")
                break
            covered_minutes.add(m)

    # 检查24小时覆盖
    total_minutes = 24 * 60
    if len(covered_minutes) < total_minutes:
        missing_count = total_minutes - len(covered_minutes)
        errors.append(f"时段配置不完整，缺少{missing_count}分钟的覆盖")

    return len(errors) == 0, errors


# =============================================================================
# 仿真配置校验
# =============================================================================
def validate_simulation_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """校验仿真配置

    Args:
        config: 仿真配置字典

    Returns:
        Tuple[bool, List[str]]: (是否通过, 错误信息列表)
    """
    errors = []

    # 时长校验
    duration_hours = config.get("duration_hours", 24)
    ok, msg = validate_range(duration_hours, 1, 168 * 4, "仿真时长")  # 最多4周
    if not ok:
        errors.append(msg)

    # 时间步长校验
    timestep_minutes = config.get("timestep_minutes", 15)
    valid_timesteps = [1, 5, 10, 15, 30, 60]
    if timestep_minutes not in valid_timesteps:
        errors.append(f"时间步长({timestep_minutes})必须是{valid_timesteps}中的一个")

    # 负荷缩放系数校验
    ok, msg = validate_range(config.get("load_scale_factor"), 0.1, 10, "负荷缩放系数")
    if not ok:
        errors.append(msg)

    return len(errors) == 0, errors


# =============================================================================
# 综合校验
# =============================================================================
def validate_all_params(
    bess_params: Dict[str, Any],
    economic_params: Dict[str, Any],
    control_params: Dict[str, Any],
    simulation_config: Optional[Dict[str, Any]] = None
) -> Tuple[bool, Dict[str, List[str]]]:
    """综合校验所有参数

    Args:
        bess_params: BESS参数
        economic_params: 经济参数
        control_params: 控制参数
        simulation_config: 仿真配置（可选）

    Returns:
        Tuple[bool, Dict[str, List[str]]]: (是否全部通过, 各模块错误信息)
    """
    all_errors = {}

    ok, errors = validate_bess_params(bess_params)
    if not ok:
        all_errors["bess"] = errors

    ok, errors = validate_economic_params(economic_params)
    if not ok:
        all_errors["economic"] = errors

    ok, errors = validate_control_params(control_params)
    if not ok:
        all_errors["control"] = errors

    if simulation_config:
        ok, errors = validate_simulation_config(simulation_config)
        if not ok:
            all_errors["simulation"] = errors

    # 跨模块校验
    cross_errors = _validate_cross_module(bess_params, control_params)
    if cross_errors:
        all_errors["cross_module"] = cross_errors

    return len(all_errors) == 0, all_errors


def _validate_cross_module(
    bess_params: Dict[str, Any],
    control_params: Dict[str, Any]
) -> List[str]:
    """跨模块校验

    检查BESS参数和控制参数之间的逻辑一致性
    """
    errors = []

    # SOC保护阈值与SOC限制的关系
    soc_max = bess_params.get("soc_max", 90)
    soc_min = bess_params.get("soc_min", 10)
    protect_soc_high = control_params.get("protect_soc_high", 95)
    protect_soc_low = control_params.get("protect_soc_low", 5)

    if protect_soc_high < soc_max:
        errors.append(f"过充保护阈值({protect_soc_high})低于SOC上限({soc_max})，可能导致无法充满")

    if protect_soc_low > soc_min:
        errors.append(f"过放保护阈值({protect_soc_low})高于SOC下限({soc_min})，可能导致无法放完")

    return errors
