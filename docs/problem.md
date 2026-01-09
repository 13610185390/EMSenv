# 开发问题记录

> 记录开发过程中遇到的问题及解决方案。已解决的问题用 ~~删除线~~ 标记。

---

## 阶段3：展示层集成

### ~~P001: Windows 控制台 Unicode 编码问题~~

**问题描述**：测试脚本中使用 emoji (✅) 在 Windows GBK 编码控制台输出时报错 `UnicodeEncodeError`

**解决方案**：将 emoji 替换为 ASCII 文本 `[OK]`

**相关文件**：`tests/test_simulation_core.py`

---

### ~~P002: modules/__init__.py 导出缺失~~

**问题描述**：`format_statistics_table` 和 `format_annual_table` 函数未在 `modules/__init__.py` 中导出，导致 `app.py` 导入失败

**解决方案**：在 `modules/__init__.py` 中添加这两个函数的导出

**相关文件**：`modules/__init__.py`

---

## 阶段4：教学增强层

*本阶段开发顺利，未遇到问题。*

---

## 待解决问题

*暂无*

---

## 问题模板

```markdown
### P00X: 问题标题

**问题描述**：简述问题现象

**错误信息**：（如有）
```
错误日志
```

**解决方案**：描述解决方法

**相关文件**：涉及的文件路径
```
