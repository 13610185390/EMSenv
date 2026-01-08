# -*- coding: utf-8 -*-
"""应用设置

对应设计文档：开发规划文档 0.4节
应用级配置项
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import os


@dataclass
class AppSettings:
    """应用设置类"""

    # ==========================================================================
    # 基础设置
    # ==========================================================================
    app_name: str = "储能EMS教学仿真平台"
    app_version: str = "0.1.0"
    debug_mode: bool = False

    # ==========================================================================
    # 路径设置
    # ==========================================================================
    base_dir: str = field(default_factory=lambda: os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ))

    @property
    def data_dir(self) -> str:
        """数据目录"""
        return os.path.join(self.base_dir, "data")

    @property
    def load_profiles_dir(self) -> str:
        """负荷曲线数据目录"""
        return os.path.join(self.data_dir, "load_profiles")

    @property
    def knowledge_base_dir(self) -> str:
        """知识库数据目录"""
        return os.path.join(self.data_dir, "knowledge_base")

    @property
    def fault_cases_dir(self) -> str:
        """故障案例数据目录"""
        return os.path.join(self.data_dir, "fault_cases")

    # ==========================================================================
    # Gradio设置
    # ==========================================================================
    gradio_server_name: str = "0.0.0.0"
    gradio_server_port: int = 7860
    gradio_share: bool = False
    gradio_auth: Optional[tuple] = None  # (username, password)

    # ==========================================================================
    # 可视化设置
    # ==========================================================================
    default_chart_library: str = "plotly"  # plotly 或 matplotlib
    chart_font_family: str = "SimHei"      # 支持中文的字体
    chart_show_grid: bool = True
    chart_grid_alpha: float = 0.3

    # ==========================================================================
    # 仿真设置
    # ==========================================================================
    default_simulation_duration: int = 24      # 小时
    default_simulation_timestep: int = 15      # 分钟
    max_simulation_duration: int = 168         # 小时 (一周)
    show_progress_bar: bool = True

    # ==========================================================================
    # 教学设置
    # ==========================================================================
    enable_teaching_hints: bool = True         # 启用教学提示
    enable_knowledge_links: bool = True        # 启用知识点链接
    default_learning_mode: str = "beginner"    # beginner, intermediate, advanced

    # ==========================================================================
    # 导出设置
    # ==========================================================================
    default_export_format: str = "csv"         # csv, xlsx, json
    export_decimal_places: int = 2
    export_include_charts: bool = False

    # ==========================================================================
    # 扩展预留
    # ==========================================================================
    ext_settings: Dict[str, Any] = field(default_factory=dict)


# 全局设置实例
settings = AppSettings()


def get_settings() -> AppSettings:
    """获取全局设置"""
    return settings


def update_settings(**kwargs) -> AppSettings:
    """更新全局设置"""
    global settings
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    return settings
