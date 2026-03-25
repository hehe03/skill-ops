---
name: trace-optimize-skill
version: 0.1.0
description: >
  Analyzes a working skill's traces and the output from a trace analyzer to identify anomalies and generate actionable improvements. Combines traditional methods with large-model reasoning to produce an improved skill and a comprehensive improvement report.
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

Overview
- A Claude Code compliant skill that analyzes a working skill's trace data and the output from a trace analyzer to identify anomalies, and generates actionable improvements blending traditional methods with large-model reasoning.
- Produces an improved version of the working skill and a comprehensive improvement report.

Usage (command-line)
- Run in project root:
  python scripts/main.py --work-skill-path <path-to-working-skill> --trace-data-path <path-to-trace-data> --analysis-results-path <path-to-analysis-results> --output-dir <path-to-output>

Inputs
- work_skill_path: Path to the existing skill to optimize
- trace_data_path: Path where trace data generated during skill execution is stored
- analysis_results_path: Path to analysis results produced by the trace analyzer

Outputs
- improved_skill_path: Directory containing the improved skill (copied from the original skill with patch notes)
- improvement_report_path: Markdown report describing the improvements
- summary_json_path: Structured summary of the analysis and improvements

Claude Code compliance notes
- skill.md documents the intent, inputs/outputs, and usage so automated tooling (Claude Code/OpenCLAW) can load and execute the skill.
- A scripts/ folder is used to host executable logic (main.py) and helper modules; the CLI entry point is main.py at the project root (as requested).
- The tool is designed to be auto-loadable by Claude Code/OpenCLAW in typical scans of root-level skills.

Notes
- There is an optional LL model augmentation path controlled by environment variable TRACE_OPTIMIZE_USE_LLM.
- If you want to enable the LLM-based deep-dive, set TRACE_OPTIMIZE_USE_LLM=1 and provide TRACE_OPTIMIZE_USE_LLM_API with the endpoint.
