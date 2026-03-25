---
name: trace-optimize-skill
version: 0.1.0
description: >
  基于一个工作技能、该技能产生的 trace 数据以及 trace 分析结果，进行深度分析，结合传统方法与大模型策略，提出对工作技能的改进建议，输出改进后的技能包与改进报告。
entry_point: scripts/main.py
language: python
inputs:
  - work_skill_path
  - trace_data_path
  - analysis_results_path
outputs:
  - improved_skill_path
  - improvement_report_path
  - summary_json_path
dependencies:
  python: ">=3.10"
  pandas: ">=1.5"
  numpy: ">=1.21"
  requests: ">=2.28"
LLM_support: true
llm_api_env: TRACE_OPTIMIZE_USE_LLM
---
# trace-optimize-skill

概述
- 通过分析工作技能、该技能产生的 trace 数据以及 trace 分析结果，进行深度分析；在需要时调用大模型以获得更多洞察。
-  结合传统方法与大模型策略，给出对工作技能的改进建议，并输出改进后的技能包与改进报告。

用法（命令行）
- 在项目根目录执行：
  python scripts/main.py --work-skill-path <工作技能路径> --trace-data-path <trace 数据路径> --analysis-results-path <分析结果路径> --output-dir <输出路径>

输入
- work_skill_path：要优化的工作技能代码/目录路径
- trace_data_path：该技能执行过程中产生的 trace 数据
- analysis_results_path：trace 分析工具生成的分析结果

输出
- improved_skill_path：改进后的技能包，复制自原技能并附上 patch notes
- improvement_report_path：改进报告
- summary_json_path：分析与改进的结构化摘要

Claude Code 合规要点
-  skill.md 提供结构化元数据与中文说明，方便 Claude Code/OpenCLAW 自动加载与执行。
-  scripts/ 文件夹承载实现逻辑，入口点为 scripts/main.py。
-  技能设计为可被根目录技能加载器自动发现与执行。

注意
- 如启用大模型辅助，请通过环境变量 TRACE_OPTIMIZE_USE_LLM 以及 llm_config.yaml 进行配置。
