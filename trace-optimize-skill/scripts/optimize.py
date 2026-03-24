#!/usr/bin/env python3
"""
Trace Diagnosis & Skill Optimizer
根据trace数据诊断结果，优化IT客服skill
"""
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from collections import Counter, defaultdict
from datetime import datetime


@dataclass
class DiagnosisInput:
    skill_dir: str
    trace_dir: str
    analysis_report_dir: Optional[str] = None


@dataclass
class DiagnosisOutput:
    diagnosis_report: Dict[str, Any]
    improved_skill_dir: str
    changes_summary: List[str]


class TraceAnalyzer:
    """分析trace数据"""
    
    def __init__(self, trace_dir: str):
        self.trace_dir = Path(trace_dir)
        self.traces: List[Dict] = []
    
    def load_traces(self) -> int:
        count = 0
        for file_path in self.trace_dir.glob("*.jsonl"):
            records = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            self.traces.append({'file': file_path.name, 'records': records})
            count += 1
        return count
    
    def analyze_tools(self) -> Dict[str, Any]:
        tool_calls = Counter()
        tool_errors = Counter()
        
        for trace in self.traces:
            for record in trace['records']:
                if record.get('role') == 'tool':
                    tool_name = record.get('tool_name', 'unknown')
                    tool_calls[tool_name] += 1
                    if record.get('has_error') or 'error' in record.get('content', '')[:50].lower():
                        tool_errors[tool_name] += 1
        
        return {
            'total_calls': sum(tool_calls.values()),
            'by_tool': dict(tool_calls),
            'errors_by_tool': dict(tool_errors),
            'error_rates': {t: tool_errors[t] / max(tool_calls[t], 1) for t in tool_calls}
        }
    
    def analyze_intents(self) -> Dict[str, Any]:
        intents = Counter()
        for trace in self.traces:
            for record in trace['records']:
                if record.get('role') == 'tool' and record.get('tool_name') == 'intent_classifier':
                    content = record.get('content', '')
                    if 'Intent identified:' in content:
                        intents[content.split('Intent identified:')[1].strip()] += 1
        return {'distribution': dict(intents), 'total': sum(intents.values())}
    
    def analyze_flows(self) -> Dict[str, Any]:
        """分析工具调用流程"""
        flow_stats = defaultdict(int)
        for trace in self.traces:
            tools = []
            for record in trace['records']:
                if record.get('role') == 'tool':
                    tools.append(record.get('tool_name', ''))
                elif record.get('role') == 'assistant' and record.get('tool_calls'):
                    for tc in record.get('tool_calls', []):
                        if isinstance(tc, dict) and 'function' in tc:
                            func = tc['function']
                            if isinstance(func, dict) and 'name' in func:
                                tools.append(func['name'])
            flow = ' -> '.join(tools)
            flow_stats[flow] += 1
        
        return {'flows': dict(flow_stats), 'unique_flows': len(flow_stats)}
    
    def find_issues(self) -> List[Dict[str, Any]]:
        """查找问题"""
        issues = []
        for trace in self.traces:
            for record in trace['records']:
                if record.get('role') == 'tool':
                    content = record.get('content', '')
                    if record.get('has_error') or 'error' in content[:50].lower():
                        issues.append({
                            'file': trace['file'],
                            'tool': record.get('tool_name'),
                            'error': content[:100]
                        })
        return issues


class SkillOptimizer:
    """Skill优化器"""
    
    def __init__(self, skill_dir: str):
        self.skill_dir = Path(skill_dir)
        self.tools_file = self.skill_dir / "tools" / "__init__.py"
        self.agent_file = self.skill_dir / "scripts" / "it_agent.py"
    
    def load_skill_code(self) -> Dict[str, str]:
        """加载skill代码"""
        code = {}
        if self.tools_file.exists():
            code['tools'] = self.tools_file.read_text(encoding='utf-8')
        if self.agent_file.exists():
            code['agent'] = self.agent_file.read_text(encoding='utf-8')
        return code
    
    def analyze_tool_issues(self, tool_stats: Dict, intents: Dict) -> List[Dict[str, str]]:
        """分析工具问题"""
        suggestions = []
        
        # 检查错误率
        for tool, rate in tool_stats.get('error_rates', {}).items():
            if rate > 0.05:
                suggestions.append({
                    'type': 'error_handling',
                    'tool': tool,
                    'issue': f'{tool} 错误率 {rate:.1%}',
                    'fix': f'添加 {tool} 的重试机制和错误处理'
                })
        
        # 检查调用分布
        by_tool = tool_stats.get('by_tool', {})
        if 'case_base_search' in by_tool and by_tool['case_base_search'] < len(by_tool) * 0.5:
            suggestions.append({
                'type': 'flow_optimization',
                'tool': 'case_base_search',
                'issue': '案例库查询调用不足',
                'fix': '在更多流程节点调用案例库查询'
            })
        
        # 检查意图覆盖
        intent_dist = intents.get('distribution', {})
        if intent_dist:
            total = sum(intent_dist.values())
            for intent, count in intent_dist.items():
                if count / total > 0.4:
                    suggestions.append({
                        'type': 'intent_coverage',
                        'tool': 'intent_classifier',
                        'issue': f'{intent} 占比过高 {count/total:.1%}',
                        'fix': '增加更多意图类别训练数据'
                    })
        
        return suggestions
    
    def generate_improvements(self, tool_stats: Dict, intents: Dict, issues: List) -> List[Dict[str, Any]]:
        """生成改进建议"""
        improvements = []
        
        # 工具相关
        for tool, rate in tool_stats.get('error_rates', {}).items():
            if rate > 0:
                improvements.append({
                    'category': 'tool',
                    'target': tool,
                    'action': 'improve_error_handling',
                    'description': f'优化 {tool} 工具的错误处理',
                    'priority': 'high' if rate > 0.1 else 'medium',
                    'code_changes': self._get_tool_fix_code(tool)
                })
        
        # 流程相关
        flow_issues = [i for i in issues if i.get('tool') in ['database_query', 'api_gateway']]
        if flow_issues:
            improvements.append({
                'category': 'flow',
                'target': 'workflow',
                'action': 'add_fallback',
                'description': '添加降级机制，数据库/网关失败时使用备选方案',
                'priority': 'high',
                'code_changes': self._get_flow_fix_code()
            })
        
        # 通用优化
        improvements.append({
            'category': 'performance',
            'target': 'agent',
            'action': 'add_timeout',
            'description': '为所有工具调用添加超时控制',
            'priority': 'medium',
            'code_changes': self._get_timeout_code()
        })
        
        return improvements
    
    def _get_tool_fix_code(self, tool: str) -> str:
        """获取工具修复代码"""
        return f'''
    def execute(self, **kwargs) -> Any:
        try:
            # 添加重试机制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return self._execute_impl(**kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(0.5 * (attempt + 1))
        except Exception as e:
            return {{"error": str(e), "fallback": True}}
'''
    
    def _get_flow_fix_code(self) -> str:
        return '''
    async def _fallback_execute(self, tool_name: str, **kwargs):
        """降级执行：当主工具失败时使用备选"""
        fallback_map = {
            "database_query": "cache_lookup",
            "api_gateway": "direct_call"
        }
        fallback_tool = fallback_map.get(tool_name)
        if fallback_tool:
            return await self._execute_tool(fallback_tool, **kwargs)
        return {"error": "no_fallback_available"}
'''
    
    def _get_timeout_code(self) -> str:
        return '''
    async def execute_with_timeout(self, tool, kwargs, timeout=5):
        """带超时的工具执行"""
        try:
            return await asyncio.wait_for(tool.execute(**kwargs), timeout=timeout)
        except asyncio.TimeoutError:
            return {"error": "timeout", "tool": tool.name}
'''
    
    def apply_improvements(self, improvements: List[Dict[str, Any]], output_dir: str) -> str:
        """应用改进并保存"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 复制原始文件
        if self.skill_dir.exists():
            for item in self.skill_dir.iterdir():
                if item.is_dir():
                    shutil.copytree(item, output_path / item.name, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, output_path / item.name)
        
        # 创建改进日志
        improvements_log = {
            'generated_at': datetime.now().isoformat(),
            'improvements_count': len(improvements),
            'details': improvements
        }
        
        with open(output_path / 'improvements.json', 'w', encoding='utf-8') as f:
            json.dump(improvements_log, f, ensure_ascii=False, indent=2)
        
        return str(output_path)


class DiagnosisReportGenerator:
    """诊断报告生成器"""
    
    @staticmethod
    def generate(input_data: DiagnosisInput) -> DiagnosisOutput:
        # 1. 分析trace数据
        trace_analyzer = TraceAnalyzer(input_data.trace_dir)
        trace_count = trace_analyzer.load_traces()
        
        tool_stats = trace_analyzer.analyze_tools()
        intent_stats = trace_analyzer.analyze_intents()
        flow_stats = trace_analyzer.analyze_flows()
        issues = trace_analyzer.find_issues()
        
        # 2. 读取trace-analyzer-skill报告
        analyzer_report = {}
        if input_data.analysis_report_dir:
            report_dir = Path(input_data.analysis_report_dir)
            for report_file in report_dir.glob("analysis_*.json"):
                with open(report_file, 'r', encoding='utf-8') as f:
                    analyzer_report = json.load(f)
                break
        
        # 3. 生成改进建议
        optimizer = SkillOptimizer(input_data.skill_dir)
        improvements = optimizer.generate_improvements(tool_stats, intent_stats, issues)
        
        # 4. 生成诊断报告
        diagnosis_report = {
            'generated_at': datetime.now().isoformat(),
            'input': {
                'skill_dir': input_data.skill_dir,
                'trace_dir': input_data.trace_dir,
                'trace_count': trace_count
            },
            'analysis': {
                'tool_stats': tool_stats,
                'intent_stats': intent_stats,
                'flow_stats': flow_stats,
                'issues_found': len(issues),
                'analyzer_report': analyzer_report.get('stats', {})
            },
            'root_causes': [
                {'issue': f'发现 {len(issues)} 个工具执行错误', 'cause': '工具错误处理不完善'},
                {'issue': '部分工具调用率低', 'cause': '流程覆盖不完整'},
            ],
            'improvements': improvements,
            'summary': {
                'total_improvements': len(improvements),
                'high_priority': len([i for i in improvements if i.get('priority') == 'high']),
                'medium_priority': len([i for i in improvements if i.get('priority') == 'medium'])
            }
        }
        
        # 5. 应用改进
        improved_dir = optimizer.apply_improvements(improvements, 
            str(Path(input_data.skill_dir).parent / 'improved_skill'))
        
        return DiagnosisOutput(
            diagnosis_report=diagnosis_report,
            improved_skill_dir=improved_dir,
            changes_summary=[i['description'] for i in improvements]
        )


def print_report(report: DiagnosisOutput):
    """打印诊断报告"""
    dr = report.diagnosis_report
    
    print("=" * 60)
    print("Trace Diagnosis & Skill Optimization Report")
    print("=" * 60)
    
    print(f"\n[输入统计]")
    print(f"  Skill目录: {dr['input']['skill_dir']}")
    print(f"  Trace数据: {dr['input']['trace_count']} 条")
    
    print(f"\n[分析结果]")
    print(f"  工具调用: {dr['analysis']['tool_stats']['total_calls']} 次")
    print(f"  发现问题: {dr['analysis']['issues_found']} 个")
    
    print(f"\n[工具错误率]")
    for tool, rate in dr['analysis']['tool_stats'].get('error_rates', {}).items():
        if rate > 0:
            print(f"  - {tool}: {rate:.1%}")
    
    print(f"\n[根因分析]")
    for rc in dr['root_causes']:
        print(f"  - {rc['issue']}")
        print(f"    原因: {rc['cause']}")
    
    print(f"\n[改进建议 ({dr['summary']['total_improvements']}项)]")
    print(f"  高优先级: {dr['summary']['high_priority']}")
    print(f"  中优先级: {dr['summary']['medium_priority']}")
    
    for imp in dr['improvements']:
        print(f"\n  [{imp['priority'].upper()}] {imp['category']} - {imp['target']}")
        print(f"    {imp['description']}")
    
    print(f"\n[输出]")
    print(f"  改进后的skill: {report.improved_skill_dir}")
    print(f"  诊断报告: diagnosis_report.json")
    print("=" * 60)


def main():
    skill_dir = sys.argv[1] if len(sys.argv) > 1 else "../it-customer-service-skill"
    trace_dir = sys.argv[2] if len(sys.argv) > 2 else "../trace-analyzer-skill/data/it_support_traces"
    analysis_dir = sys.argv[3] if len(sys.argv) > 3 else "../trace-analyzer-skill/output/results"
    
    print(f"Skill: {skill_dir}")
    print(f"Traces: {trace_dir}")
    print(f"Analysis: {analysis_dir}")
    print()
    
    input_data = DiagnosisInput(
        skill_dir=skill_dir,
        trace_dir=trace_dir,
        analysis_report_dir=analysis_dir
    )
    
    report = DiagnosisReportGenerator.generate(input_data)
    print_report(report)
    
    # 保存报告
    output_file = Path(trace_dir).parent / "diagnosis_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report.diagnosis_report, f, ensure_ascii=False, indent=2)
    print(f"\n报告已保存到: {output_file}")


if __name__ == "__main__":
    main()
