#!/usr/bin/env python3
"""
Trace Diagnosis Advisor
分析trace数据诊断结果，提供根因分析和skill改进建议
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import random


@dataclass
class DiagnosisReport:
    total_traces: int
    traces_with_issues: int
    tool_stats: Dict[str, Any]
    intent_stats: Dict[str, Any]
    latency_stats: Dict[str, Any]
    error_patterns: List[Dict[str, Any]]
    root_causes: List[Dict[str, str]]
    improvements: List[Dict[str, str]]


class TraceAnalyzer:
    """分析trace数据"""
    
    def __init__(self, trace_dir: str):
        self.trace_dir = Path(trace_dir)
        self.traces: List[Dict] = []
    
    def load_traces(self) -> int:
        """加载trace数据"""
        count = 0
        for file_path in self.trace_dir.glob("*.jsonl"):
            with open(file_path, 'r', encoding='utf-8') as f:
                records = []
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
                self.traces.append({
                    'file': file_path.name,
                    'records': records
                })
                count += 1
        return count
    
    def analyze_tools(self) -> Dict[str, Any]:
        """分析工具调用"""
        tool_calls = Counter()
        tool_errors = Counter()
        tool_latencies = defaultdict(list)
        
        for trace in self.traces:
            for record in trace['records']:
                if record.get('role') == 'tool':
                    tool_name = record.get('tool_name', 'unknown')
                    tool_calls[tool_name] += 1
                    
                    if record.get('has_error') or 'error' in record.get('content', '').lower():
                        tool_errors[tool_name] += 1
                    
                    if record.get('latency_ms'):
                        tool_latencies[tool_name].append(record['latency_ms'])
        
        return {
            'total_calls': sum(tool_calls.values()),
            'by_tool': dict(tool_calls),
            'errors_by_tool': dict(tool_errors),
            'error_rates': {
                t: tool_errors[t] / max(tool_calls[t], 1) 
                for t in tool_calls
            },
            'latencies': {
                t: {
                    'avg': sum(v) / max(len(v), 1),
                    'max': max(v) if v else 0,
                    'min': min(v) if v else 0
                }
                for t, v in tool_latencies.items()
            }
        }
    
    def analyze_intents(self) -> Dict[str, Any]:
        """分析意图识别"""
        intents = Counter()
        
        for trace in self.traces:
            for record in trace['records']:
                if record.get('role') == 'tool' and record.get('tool_name') == 'intent_classifier':
                    content = record.get('content', '')
                    if 'Intent identified:' in content:
                        intent = content.split('Intent identified:')[1].strip()
                        intents[intent] += 1
        
        return {
            'total': sum(intents.values()),
            'distribution': dict(intents),
            'top_intents': intents.most_common(5)
        }
    
    def analyze_latency(self) -> Dict[str, Any]:
        """分析延迟"""
        latencies = []
        tool_latencies = defaultdict(list)
        
        for trace in self.traces:
            trace_latency = 0
            for record in trace['records']:
                if record.get('role') == 'tool' and record.get('latency_ms'):
                    lat = record['latency_ms']
                    tool_latencies[record.get('tool_name', 'unknown')].append(lat)
                    trace_latency += lat
            latencies.append(trace_latency)
        
        return {
            'avg_trace_latency': sum(latencies) / max(len(latencies), 1),
            'max_trace_latency': max(latencies) if latencies else 0,
            'by_tool': dict(tool_latencies)
        }
    
    def find_error_patterns(self) -> List[Dict[str, Any]]:
        """查找错误模式"""
        patterns = []
        
        for trace in self.traces:
            has_error = False
            error_type = None
            error_tool = None
            
            for record in trace['records']:
                if record.get('role') == 'tool':
                    content = record.get('content', '')
                    if record.get('has_error') or 'error' in content.lower()[:50]:
                        has_error = True
                        error_tool = record.get('tool_name')
                        if 'timeout' in content.lower():
                            error_type = 'timeout'
                        elif 'connection' in content.lower():
                            error_type = 'connection_error'
                        else:
                            error_type = 'unknown'
            
            if has_error:
                patterns.append({
                    'file': trace['file'],
                    'error_type': error_type,
                    'error_tool': error_tool
                })
        
        return patterns


class RootCauseAnalyzer:
    """根因分析"""
    
    @staticmethod
    def analyze(tool_stats: Dict, intent_stats: Dict, error_patterns: List) -> List[Dict[str, str]]:
        """分析根因"""
        root_causes = []
        
        # 检查工具错误率
        for tool, rate in tool_stats.get('error_rates', {}).items():
            if rate > 0.1:
                root_causes.append({
                    'issue': f"工具 {tool} 错误率过高 ({rate:.1%})",
                    'root_cause': f"{tool} 工具执行逻辑存在问题或超时设置不合理",
                    'impact': '高'
                })
        
        # 检查意图分布
        intents = intent_stats.get('distribution', {})
        if intents:
            total = sum(intents.values())
            for intent, count in intents.items():
                if count / max(total, 1) > 0.4:
                    root_causes.append({
                        'issue': f"意图 {intent} 占比过高 ({count/total:.1%})",
                        'root_cause': '意图分类器可能存在类别不平衡或用户问题类型集中',
                        'impact': '中'
                    })
        
        # 检查错误模式
        error_counter = Counter([p['error_type'] for p in error_patterns])
        for error_type, count in error_counter.items():
            if count > 0:
                root_causes.append({
                    'issue': f"发现 {count} 个 {error_type} 错误",
                    'root_cause': '网络不稳定或服务调用超时',
                    'impact': '高' if error_type == 'timeout' else '中'
                })
        
        if not root_causes:
            root_causes.append({
                'issue': '未发现明显根因',
                'root_cause': '系统运行正常',
                'impact': '低'
            })
        
        return root_causes


class ImprovementAdvisor:
    """改进建议"""
    
    @staticmethod
    def suggest(tool_stats: Dict, intent_stats: Dict, root_causes: List) -> List[Dict[str, str]]:
        """生成改进建议"""
        improvements = []
        
        # 基于工具统计
        for tool, rate in tool_stats.get('error_rates', {}).items():
            if rate > 0.1:
                improvements.append({
                    'category': '工具优化',
                    'target': tool,
                    'suggestion': f'优化 {tool} 工具的错误处理和超时配置',
                    'priority': 'high'
                })
        
        # 基于延迟
        latencies = tool_stats.get('latencies', {})
        for tool, stats in latencies.items():
            if stats.get('max', 0) > 10000:
                improvements.append({
                    'category': '性能优化',
                    'target': tool,
                    'suggestion': f'{tool} 最大延迟 {stats["max"]}ms，建议添加缓存或异步处理',
                    'priority': 'medium'
                })
        
        # 基于意图
        if intent_stats.get('total', 0) > 0:
            improvements.append({
                'category': '意图识别',
                'target': 'intent_classifier',
                'suggestion': '增加更多意图类别训练数据，改善分类准确率',
                'priority': 'medium'
            })
        
        # 基于根因
        for cause in root_causes:
            if cause.get('impact') == '高':
                improvements.append({
                    'category': '服务稳定性',
                    'target': 'infrastructure',
                    'suggestion': f'优先解决: {cause["issue"]}',
                    'priority': 'critical'
                })
        
        if not improvements:
            improvements.append({
                'category': '常规优化',
                'target': 'general',
                'suggestion': '系统运行良好，可考虑增加更多工具能力',
                'priority': 'low'
            })
        
        return improvements


def generate_diagnosis_report(trace_dir: str, analysis_report: Optional[Dict] = None) -> DiagnosisReport:
    """生成诊断报告"""
    analyzer = TraceAnalyzer(trace_dir)
    total_traces = analyzer.load_traces()
    
    tool_stats = analyzer.analyze_tools()
    intent_stats = analyzer.analyze_intents()
    latency_stats = analyzer.analyze_latency()
    error_patterns = analyzer.find_error_patterns()
    
    root_causes = RootCauseAnalyzer.analyze(tool_stats, intent_stats, error_patterns)
    improvements = ImprovementAdvisor.suggest(tool_stats, intent_stats, root_causes)
    
    traces_with_issues = len(error_patterns)
    
    return DiagnosisReport(
        total_traces=total_traces,
        traces_with_issues=traces_with_issues,
        tool_stats=tool_stats,
        intent_stats=intent_stats,
        latency_stats=latency_stats,
        error_patterns=error_patterns,
        root_causes=root_causes,
        improvements=improvements
    )


def print_report(report: DiagnosisReport):
    """打印诊断报告"""
    print("=" * 60)
    print("Trace Diagnosis Report")
    print("=" * 60)
    
    print(f"\n[概览]")
    print(f"  总trace数: {report.total_traces}")
    print(f"  有问题的trace: {report.traces_with_issues}")
    print(f"  问题率: {report.traces_with_issues/max(report.total_traces,1):.1%}")
    
    print(f"\n[工具调用统计]")
    print(f"  总调用次数: {report.tool_stats.get('total_calls', 0)}")
    print(f"  各工具调用次数:")
    for tool, count in report.tool_stats.get('by_tool', {}).items():
        error_rate = report.tool_stats.get('error_rates', {}).get(tool, 0)
        print(f"    - {tool}: {count} 次 (错误率: {error_rate:.1%})")
    
    print(f"\n[意图识别统计]")
    print(f"  总识别次数: {report.intent_stats.get('total', 0)}")
    for intent, count in report.intent_stats.get('top_intents', []):
        print(f"    - {intent}: {count}")
    
    print(f"\n[延迟统计]")
    print(f"  平均trace延迟: {report.latency_stats.get('avg_trace_latency', 0):.0f}ms")
    print(f"  最大trace延迟: {report.latency_stats.get('max_trace_latency', 0):.0f}ms")
    
    print(f"\n[错误模式]")
    for pattern in report.error_patterns[:5]:
        print(f"    - {pattern['file']}: {pattern['error_type']} at {pattern['error_tool']}")
    
    print(f"\n[根因分析]")
    for cause in report.root_causes:
        print(f"  [{cause.get('impact', 'N/A')}] {cause.get('issue', '')}")
        print(f"       根因: {cause.get('root_cause', '')}")
    
    print(f"\n[改进建议]")
    for imp in report.improvements:
        print(f"  [{imp.get('priority', '').upper()}] {imp.get('category', '')} - {imp.get('target', '')}")
        print(f"       {imp.get('suggestion', '')}")
    
    print("\n" + "=" * 60)


def main():
    trace_dir = sys.argv[1] if len(sys.argv) > 1 else "data/it_support_traces"
    
    print(f"Analyzing traces from: {trace_dir}")
    report = generate_diagnosis_report(trace_dir)
    print_report(report)
    
    output_file = Path(trace_dir).parent / "diagnosis_report.json"
    report_dict = {
        'total_traces': report.total_traces,
        'traces_with_issues': report.traces_with_issues,
        'tool_stats': report.tool_stats,
        'intent_stats': report.intent_stats,
        'latency_stats': report.latency_stats,
        'error_patterns': report.error_patterns,
        'root_causes': report.root_causes,
        'improvements': report.improvements
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report_dict, f, ensure_ascii=False, indent=2)
    
    print(f"\nReport saved to: {output_file}")


if __name__ == "__main__":
    main()
