# Trace Analyzer

从大量 agent trace 数据中主动感知有问题的数据。

## 功能

### 规则检测
基于预定义规则的检测，字段数据来源说明：

| 检查项 | 数据来源 | 说明 |
|--------|----------|------|
| high_latency | trace记录中 `role=tool` 的 `latency_ms` 字段 | 延迟超过阈值(默认10000ms) |
| excessive_tokens | 统计所有 `role=tool` 记录的 `content` 字段字符长度之和 | token消耗超过阈值(默认5000) |
| error_flag | 检查records中是否存在 `role=tool` 且 `has_error=true` 的记录 | 存在错误标志 |
| empty_response | 取最后一条 `role=assistant` 的 `content` 字段长度 | 响应长度为0 |
| excessive_tool_calls | 统计 `role=tool` 的记录数量 | 工具调用次数超过阈值(默认20) |

### 统计异常检测
使用统计方法检测数值型字段的异常值，基于所有trace的分布计算：

| 方法 | 检测字段 | 数据来源 | 说明 |
|------|----------|----------|------|
| Z-score | duration_ms, total_tokens, response_length | TraceData对象的对应属性 | 计算Z=(x-μ)/σ，超过阈值(默认3.0)判定为异常 |
| IQR | duration_ms, total_tokens | 同上 | 计算Q1/Q3/IQR，值超出 [Q1-1.5*IQR, Q3+1.5*IQR] 范围判定为异常 |

**统计异常检测原理**：
- **Z-score**：假设数据近似正态分布，|Z|>3 的值在正常分布中概率<0.3%，属于小概率事件
- **IQR**：基于四分位数，不受极端值影响，适合非正态分布数据

### 内容模式检测
分析trace记录内容中的特定模式：

| 检查项 | 数据来源 | 说明 |
|--------|----------|------|
| intent_mismatch | `role=tool` 且 `tool_name=query_rewriter` 的 `content` 字段 | 检查用户意图是否被错误改写 |
| skill_mismatch | `role=tool` 且 `tool_name=skill_orchestrator` 的 `content` 字段 | 检查加载的skill是否匹配用户问题 |
| empty_tool_calls | `role=assistant` 的 `tool_calls[].function.arguments` | 连续3次以上空参数调用 |
| repeated_tool_calls | 统计 `role=tool` 的 `tool_name` 序列 | 检测连续重复调用同一工具≥3次 |
| template_response | 最后一条 `role=assistant` 的 `content` 字段 | 包含固定模板话术≥3条 |
| tool_errors | `role=tool` 且 `has_error=true` 的记录 | 工具执行失败 |

### AI 检测
使用 LLM 判断输出质量：

| 检查项 | 评估内容 | 数据来源 |
|--------|----------|----------|
| hallucination | 幻觉信息(虚构事实) | `final_response` 内容 |
| logical_error | 逻辑错误 | `final_response` 内容 |
| safety_concern | 安全问题/违规内容 | `final_response` 内容 |
| incomplete_answer | 回答不完整/回避问题 | `final_response` 内容 |

## 使用

```bash
# 安装依赖
pip install -r requirements.txt

# 准备数据
mkdir -p data
# 将你的 trace JSON 文件放入 data/

# 运行分析
python -m run
```

## 配置

编辑 `config/default.yaml` 自定义检测规则和阈值。

## 输出

分析结果保存在 `output/results/` 目录。
