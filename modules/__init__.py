# -*- coding: utf-8 -*-
"""功能模块

包含基础参数、经济参数、控制策略、仿真计算、可视化等核心功能模块
"""

from .basic_params import (
    get_bess_params,
    set_bess_params,
    validate_bess_params,
    reset_to_default as reset_bess_to_default,
    create_basic_params_tab,
    setup_basic_params_events,
)

from .economic_params import (
    get_economic_params,
    set_economic_params,
    validate_economic_params,
    reset_to_default as reset_economic_to_default,
    calculate_peak_valley_spread,
    calculate_initial_investment,
    calculate_full_economics,
    create_economic_params_tab,
    setup_economic_params_events,
)

from .control_params import (
    get_control_params,
    set_control_params,
    validate_control_params,
    reset_to_default as reset_control_to_default,
    generate_dispatch_schedule,
    create_control_params_tab,
    setup_control_params_events,
)

from .simulation import (
    run_simulation,
    get_load_profile,
    load_custom_profile,
    calculate_statistics,
    calculate_annual_projection,
    plot_simulation_results,
    create_simulation_tab,
    setup_simulation_events,
)

from .visualization import (
    ChartStyle,
    ChartLibrary,
    ExportConfig,
    plot_power_curve,
    plot_soc_curve,
    plot_energy_summary,
    generate_statistics_table,
    generate_annual_table,
    export_results,
    plot_combined_dashboard,
    VISUALIZATION_TEACHING_META,
)

__all__ = [
    # Basic params
    'get_bess_params',
    'set_bess_params',
    'validate_bess_params',
    'reset_bess_to_default',
    'create_basic_params_tab',
    'setup_basic_params_events',
    # Economic params
    'get_economic_params',
    'set_economic_params',
    'validate_economic_params',
    'reset_economic_to_default',
    'calculate_peak_valley_spread',
    'calculate_initial_investment',
    'calculate_full_economics',
    'create_economic_params_tab',
    'setup_economic_params_events',
    # Control params
    'get_control_params',
    'set_control_params',
    'validate_control_params',
    'reset_control_to_default',
    'generate_dispatch_schedule',
    'create_control_params_tab',
    'setup_control_params_events',
    # Simulation
    'run_simulation',
    'get_load_profile',
    'load_custom_profile',
    'calculate_statistics',
    'calculate_annual_projection',
    'plot_simulation_results',
    'create_simulation_tab',
    'setup_simulation_events',
    # Visualization
    'ChartStyle',
    'ChartLibrary',
    'ExportConfig',
    'plot_power_curve',
    'plot_soc_curve',
    'plot_energy_summary',
    'generate_statistics_table',
    'generate_annual_table',
    'export_results',
    'plot_combined_dashboard',
    'VISUALIZATION_TEACHING_META',
]
