# 储能EMS教学仿真平台 - 项目说明

## 项目概述

这是一个面向储能EMS售后工程师和开发人员的**教学仿真平台**，使用 Python + Gradio 构建。

**核心目标**：通过交互式仿真帮助学员理解储能系统运行原理、EMS控制逻辑和经济性分析。

**技术栈**：Python 3.10+ / Gradio 4.x / Matplotlib / Plotly / Pandas

---

## 文档索引

### 需求与规划文档

| 文档                  | 说明                                               |
| --------------------- | -------------------------------------------------- |
| @docs/需求设计文档.md | 项目需求规格说明，包含功能列表、用户角色、教学目标 |
| @docs/开发规划文档.md | 代码开发计划，包含阶段划分、任务清单、验收标准     |

### 技术设计文档（按开发顺序）（每完成一次开发需要完善一次CLAUDE.md）

| 文档                                       | 模块             | 核心内容                                  |
| ------------------------------------------ | ---------------- | ----------------------------------------- |
| @docs/technical/01_基础参数模块技术设计.md | basic_params     | BESS参数数据类、参数校验、教学元数据      |
| @docs/technical/02_经济参数模块技术设计.md | economic_params  | 电价参数、成本参数、财务计算              |
| @docs/technical/03_控制策略模块技术设计.md | control_params   | 调度模式、充放电策略、保护参数            |
| @docs/technical/04_仿真计算模块技术设计.md | simulation       | **核心仿真引擎**、SOC计算、经济统计 |
| @docs/technical/05_可视化模块技术设计.md   | visualization    | 图表绑制、数据导出                        |
| @docs/technical/06_教学引导模块技术设计.md | learning_center  | 知识树、学习进度、引导气泡                |
| @docs/technical/07_EMS架构模块技术设计.md  | ems_architecture | 系统架构图、通信协议、状态机              |
| @docs/technical/08_故障诊断模块技术设计.md | fault_diagnosis  | 故障模拟、排查指南、案例库                |

---

## 目录结构（已创建）

```
储能虚拟环境/
├── CLAUDE.md               # 本文件 - 项目说明
├── app.py                  # 主入口文件 ✅
├── requirements.txt        # 依赖包 ✅
├── .gitignore              # Git忽略配置 ✅
│
├── config/                 # 配置模块 ✅
│   ├── __init__.py         # ✅
│   ├── default_params.py   # 默认参数 ✅
│   ├── constants.py        # 常量定义 ✅
│   └── settings.py         # 应用设置 ✅
│
├── models/                 # 数据模型 ✅
│   ├── __init__.py         # ✅ 导出所有模型
│   ├── bess.py             # BESS参数 → 对应01文档 ✅
│   ├── economic.py         # 经济参数 → 对应02文档 ✅
│   ├── control.py          # 控制参数 → 对应03文档 ✅
│   ├── simulation.py       # 仿真数据 → 对应04文档 ✅
│   └── fault.py            # 故障数据 → 对应08文档 ✅
│
├── modules/                # 功能模块 ✅
│   ├── __init__.py         # ✅ 统一导出
│   ├── basic_params.py     # 基础参数 → 对应01文档 ✅
│   ├── economic_params.py  # 经济参数 → 对应02文档 ✅
│   ├── control_params.py   # 控制策略 → 对应03文档 ✅
│   ├── simulation.py       # 仿真计算 → 对应04文档 ✅
│   ├── visualization.py    # 可视化   → 对应05文档 ✅
│   ├── learning_center.py  # 教学引导 → 对应06文档 (待实现)
│   ├── ems_architecture.py # EMS架构  → 对应07文档 (待实现)
│   └── fault_diagnosis.py  # 故障诊断 → 对应08文档 (待实现)
│
├── utils/                  # 工具函数 ✅
│   ├── __init__.py         # ✅ 导出校验函数
│   ├── validators.py       # 参数校验 ✅
│   ├── converters.py       # 数据转换 (待实现)
│   └── helpers.py          # 辅助函数 (待实现)
│
├── data/                   # 数据文件 ✅(目录已创建)
│   ├── load_profiles/      # 负荷曲线 ✅
│   ├── knowledge_base/     # 知识库 ✅
│   └── fault_cases/        # 故障案例 ✅
│
├── tests/                  # 测试代码 ✅(目录已创建)
│   ├── __init__.py         # ✅
│   ├── test_models/        # ✅
│   ├── test_modules/       # ✅
│   └── test_integration/   # ✅
│
└── docs/                   # 文档目录 ✅
    ├── 需求设计文档.md      # ✅
    ├── 开发规划文档.md      # ✅
    └── technical/          # 8个技术设计文档 ✅
```

---

## 开发规范

### 版本控制（Git）

**Git 配置参数（全部已确认）：**

| 配置项         | 说明       | 值                                                  |
| -------------- | ---------- | --------------------------------------------------- |
| `user.name`  | Git 用户名 | **TYY**                                       |
| `user.email` | Git 邮箱   | **supertyyds@168.com**                        |
| 远程仓库地址   | GitHub     | **https://github.com/13610185390/EMSenv.git** |

**提交规范**：

```
<type>(<scope>): <subject>

类型: feat / fix / docs / refactor / test / chore
范围: 模块名称，如 basic_params, simulation

示例:
feat(models): 添加BESSParams数据类
fix(simulation): 修复SOC计算逻辑
```

**分支策略**：

- `main` - 主分支（稳定版本）
- `dev` - 开发分支（日常开发）
- `feature/xxx` - 功能分支

详细规范见 @docs/开发规划文档.md 1.4节

### 代码与文档对应

- 每个代码文件在 docstring 中标注对应的设计文档
- 示例：`"""对应设计文档：01_基础参数模块技术设计.md 2.1节"""`

### 教学元数据命名

- `BESS_TEACHING_META` - 基础参数教学元数据
- `ECONOMIC_TEACHING_META` - 经济参数教学元数据
- `CONTROL_TEACHING_META` - 控制策略教学元数据
- `SIMULATION_TEACHING_META` - 仿真计算教学元数据
- `VISUALIZATION_TEACHING_META` - 可视化教学元数据

### 扩展预留标记

- 所有预留扩展点使用 `🔲` 标记
- 扩展字段以 `ext_` 前缀命名

---

## 开发顺序

```
阶段1: models/ (数据模型)
   ↓
阶段2: modules/ (核心功能：basic_params → economic_params → control_params → simulation)
   ↓
阶段3: modules/visualization.py + app.py (展示层集成)
   ↓
阶段4: modules/ (教学增强：learning_center → ems_architecture → fault_diagnosis)
   ↓
阶段5: 集成测试与优化
```

---

## 当前状态

### 开发进度

| 阶段 | 状态 | 版本标签 |
|------|------|----------|
| 阶段0: 项目初始化 | ✅ 已完成 | v0.1.0 |
| 阶段1: 基础架构层 | ✅ 已完成 | v0.2.0 |
| 阶段2: 核心功能层 | ✅ 已完成 | v0.3.0 |
| 阶段3: 展示层集成 | ⏳ 待开始 | - |
| 阶段4: 教学增强层 | ⏳ 待开始 | - |
| 阶段5: 集成测试 | ⏳ 待开始 | - |

### 已完成工作

- [x] 需求设计文档
- [x] 8个技术设计文档
- [x] 开发规划文档
- [x] Git 配置并推送到远程
- [x] **阶段0：项目初始化**
  - [x] 项目目录结构
  - [x] requirements.txt
  - [x] 基础配置文件 (constants.py, settings.py, default_params.py)
  - [x] .gitignore
  - [x] app.py 主入口占位
  - [x] Git 初始化 + main/dev 分支 + v0.1.0 标签
- [x] **阶段1：基础架构层** - 数据模型
  - [x] models/bess.py - BESS参数数据类 (BESSParams, BatteryType, ParamTeachingMeta, ParamConstraint)
  - [x] models/economic.py - 经济参数数据类 (EconomicParams, ElectricityPriceParams, CostParams, FinancialParams)
  - [x] models/control.py - 控制策略数据类 (ControlParams, DispatchMode, ProtectionParams, SchedulePoint)
  - [x] models/simulation.py - 仿真数据类 (SimulationConfig, BESSState, TimeStepResult, SimulationResult)
  - [x] models/fault.py - 故障诊断数据类 (FaultType, FaultInstance, DiagnosisGuide, FaultCase)
  - [x] models/__init__.py - 统一导出所有模型
  - [x] config/default_params.py - 增加数据类实例创建函数
- [x] **阶段2：核心功能层** - 功能模块开发
  - [x] utils/validators.py - 参数校验工具 (validate_range, validate_bess_params, validate_economic_params, validate_control_params)
  - [x] modules/basic_params.py - 基础参数模块 (参数管理 + Gradio UI + 事件绑定)
  - [x] modules/economic_params.py - 经济参数模块 (电价曲线、经济计算、UI)
  - [x] modules/control_params.py - 控制策略模块 (调度计划生成、峰谷套利/负荷跟踪策略)
  - [x] modules/simulation.py - **核心仿真引擎** (run_simulation, 负荷曲线生成, SOC计算, 统计)
  - [x] modules/visualization.py - 可视化模块 (plot_power_curve, plot_soc_curve, 数据导出)
  - [x] modules/__init__.py - 统一导出所有模块函数
  - [x] utils/__init__.py - 导出校验函数

### 下一步工作

**阶段3：展示层集成** - 应用整合

1. `app.py` - 主应用集成
   - 整合所有模块标签页
   - 配置事件绑定
   - 实现模块间数据传递
2. 运行测试与调试

**后续阶段：**
- 阶段4: 教学增强 (learning_center, ems_architecture, fault_diagnosis)
- 阶段5: 集成测试与优化

---

## 快速开始开发

### Git 信息

| 配置项 | 值 |
|--------|-----|
| 用户名 | TYY |
| 邮箱 | supertyyds@168.com |
| 远程仓库 | https://github.com/13610185390/EMSenv.git |
| 当前分支 | dev |
| 最新标签 | v0.3.0 |

### 开发步骤

1. ~~用户提供 Git 配置参数~~ ✅ 已完成
2. ~~执行阶段0：项目初始化 + Git 初始化~~ ✅ 已完成
3. 阅读 @docs/开发规划文档.md 了解开发计划
4. 按阶段顺序开发，每个任务对照对应的技术设计文档
5. 每完成一个任务提交一次 Git
6. **每完成一个阶段更新 CLAUDE.md**
7. 核心模块测试覆盖率要求 ≥ 90%

### 常用命令

```bash
# 查看状态
git status

# 提交代码
git add .
git commit -m "feat(模块名): 描述"
git push

# 创建标签
git tag -a v0.x.0 -m "描述"
git push origin v0.x.0
```
