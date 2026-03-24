---
name: trace-diagnosis-advisor
description: 根据trace数据诊断结果，分析根因并重构优化IT客服skill。当需要优化it-customer-service skill时触发，输入原始skill代码、trace数据文件、trace-analyzer-skill分析报告，输出改进建议和优化后的skill代码。
---

# Trace Diagnosis Advisor Skill

根据trace数据分析结果，对IT客服skill进行根因分析和代码优化。

## 触发条件

- 需要优化 it-customer-service skill 时
- trace-analyzer-skill 分析发现问题后
- 用户要求改进skill配置

## 输入

1. **原始skill目录**: `it-customer-service-skill/`
2. **trace数据目录**: `data/it_support_traces/` (skill根目录)
3. **分析报告** (可选): trace-analyzer-skill 输出的JSON报告

## 工作流程

```
1. 加载原始skill代码
2. 分析trace数据统计
3. 读取trace-analyzer-skill报告
4. 根因分析
5. 生成改进建议
6. 输出优化后的skill
```

## 输出

- `diagnosis_report.json` - 诊断报告
- `improved_skill/` - 改进后的skill代码

## 使用方式

```bash
# 进入skill目录
cd trace-diagnosis-skill

# 完整分析并优化
python scripts/optimize.py <skill_dir> <trace_dir> <analysis_report_dir>

# 示例
python scripts/optimize.py ../it-customer-service-skill/ ../trace-analyzer-skill/data/it_support_traces/ ../trace-analyzer-skill/output/results/
```

或加载skill后：
```
使用trace-diagnosis-advisor优化skill，输入: it-customer-service-skill/
```

## 目录结构

```
trace-diagnosis-skill/
├── SKILL.md              # Skill定义(前置YAML元数据)
└── scripts/
    ├── optimize.py        # 诊断优化脚本
    └── diagnose.py       # 诊断脚本
```
