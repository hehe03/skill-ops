---
name: trace-analyzer
description: 分析agent trace数据，检测异常(延迟过高、token异常、错误标志、统计异常、AI质量问题等)。当需要分析agent trace数据、检测数据异常、评估agent输出质量时自动触发。
version: 1.0.0
author: trace-analyzer
tags: [trace, anomaly-detection, agent-quality, monitoring]
trigger_keywords: [trace分析, 异常检测, agent质量, trace异常, 数据感知]
---

# Trace Analyzer Skill

从大量 agent trace 数据中主动感知有问题的数据。

## 触发条件

当用户提到以下内容时自动触发：
- 分析 agent trace 数据异常
- 检测 trace 中的延迟、token、错误等问题
- 统计异常检测或 AI 质量评估
- "trace分析"、"异常检测"、"agent质量评估"

## 输入

1. **trace数据目录**: 包含 `.json` 或 `.jsonl` 格式的trace文件，默认 `data/it_support_traces/`
2. **配置文件** (可选): `config/default.yaml`

## 工作流程

```
1. 确认trace数据目录位置
2. 检查/配置 config/default.yaml 中的检测规则
3. 运行分析: python scripts/run.py
4. 读取 output/results/ 下的分析报告
5. 汇总问题并向用户报告
```

## 检测能力

### 规则检测
| 检查项 | 数据来源 | 说明 |
|--------|----------|------|
| high_latency | trace记录中 `role=tool` 的 `latency_ms` 字段 | 延迟超过阈值(默认10000ms) |
| excessive_tokens | 统计所有 `role=tool` 记录的 `content` 字段字符长度之和 | token消耗超过阈值(默认5000) |
| error_flag | 检查records中是否存在 `role=tool` 且 `has_error=true` 的记录 | 存在错误标志 |
| empty_response | 取最后一条 `role=assistant` 的 `content` 字段长度 | 响应长度为0 |
| excessive_tool_calls | 统计 `role=tool` 的记录数量 | 工具调用次数超过阈值(默认20) |

### 统计异常检测
| 方法 | 检测字段 | 说明 |
|------|----------|------|
| Z-score | duration_ms, total_tokens, response_length | 计算Z=(x-μ)/σ，超过阈值(默认3.0)判定为异常 |
| IQR | duration_ms, total_tokens | 计算Q1/Q3/IQR，超出范围判定为异常 |

### 内容模式检测
- intent_mismatch: 意图改写错误
- skill_mismatch: skill不匹配
- repeated_tool_calls: 重复工具调用(≥3次)
- template_response: 模板回复(≥3条模板话术)
- tool_errors: 工具执行错误

### AI检测 (可选)
- hallucination: 幻觉信息
- logical_error: 逻辑错误
- safety_concern: 安全问题
- incomplete_answer: 回答不完整

## 使用方式

```bash
# 进入skill目录
cd trace-analyzer-skill

# 安装依赖
pip install -r requirements.txt

# 确保trace数据放在 data/ 目录下(skill根目录)

# 运行分析
python scripts/run.py

# 查看结果
ls output/results/
```

## 输出

- 分析报告: `output/results/analysis_<timestamp>.json`
- 包含: 总trace数、问题数、按严重程度/类型统计

## 目录结构

```
trace-analyzer-skill/
├── SKILL.md              # Skill定义(前置YAML元数据)
├── requirements.txt      # 依赖
├── data/                 # trace数据目录(需用户放置)
│   └── it_support_traces/
└── scripts/
    ├── run.py            # 入口脚本
    ├── config/
    │   └── default.yaml  # 配置文件
    └── src/
        ├── __init__.py
        ├── analyzer.py   # 分析器
        ├── loader.py     # 数据加载器
        ├── models.py     # 数据模型
        ├── reporter.py   # 报告生成
        └── detectors/
            ├── __init__.py
            ├── rule_detector.py         # 规则检测
            ├── statistical_detector.py  # 统计异常检测
            ├── content_pattern_detector.py  # 内容模式检测
            └── ai_detector.py           # AI质量检测
```
