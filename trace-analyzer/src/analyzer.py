import asyncio
import time
from typing import Optional
from src.loader import TraceLoader
from src.detectors.rule_detector import RuleDetector
from src.detectors.statistical_detector import StatisticalDetector
from src.detectors.ai_detector import AIDetector
from src.detectors.content_pattern_detector import ContentPatternDetector
from src.models import AnalysisResult, Issue
from src.reporter import Reporter


class TraceAnalyzer:
    def __init__(self, config: dict):
        self.config = config
        self.loader = TraceLoader(config['databases']['trace_dir'])
        self.reporter = Reporter(config)
        
        self.detectors = []
        if config['detectors']['rule']['enabled']:
            self.detectors.append(RuleDetector(config['detectors']['rule']['rules']))
        
        if config['detectors']['statistical']['enabled']:
            self.detectors.append(StatisticalDetector(config['detectors']['statistical']['methods']))
        
        if config['detectors'].get('content_pattern', {}).get('enabled', False):
            self.detectors.append(ContentPatternDetector(config['detectors'].get('content_pattern', {})))
        
        self.ai_detector: Optional[AIDetector] = None
        if config['detectors']['ai']['enabled']:
            self.ai_detector = AIDetector(config['detectors']['ai'])
            self.ai_detector.set_progress_callback(self._print_ai_progress)
        
        self.parallel_workers = config['analyzer']['parallel_workers']
        self.batch_size = config['analyzer']['batch_size']
    
    def _print_ai_progress(self, processed: int, total: int):
        print(f"\rAI Detection Progress: {processed}/{total} samples evaluated...", end='', flush=True)
    
    async def analyze(self) -> AnalysisResult:
        start_time = time.time()
        traces = self.loader.load_all()
        
        all_issues = []
        
        for detector in self.detectors:
            issues = detector.detect(traces)
            all_issues.extend(issues)
        
        if self.ai_detector:
            print("Starting AI detection...")
            ai_issues = await self.ai_detector.detect(traces)
            all_issues.extend(ai_issues)
            print("")  # newline after progress
        
        processing_time = time.time() - start_time
        
        result = AnalysisResult(
            total_traces=len(traces),
            issues=all_issues,
            stats=self._compute_stats(traces, all_issues),
            processing_time=processing_time
        )
        
        self.reporter.save(result)
        return result
    
    def _compute_stats(self, traces: list, issues: list[Issue]) -> dict:
        stats = {
            'total_traces': len(traces),
            'traces_with_issues': len(set(i.trace_id for i in issues)),
            'total_issues': len(issues),
            'by_severity': {},
            'by_type': {}
        }
        
        for issue in issues:
            severity = issue.severity.value
            issue_type = issue.issue_type.value
            
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
            stats['by_type'][issue_type] = stats['by_type'].get(issue_type, 0) + 1
        
        return stats


async def main():
    import yaml
    
    with open('../config/default.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    analyzer = TraceAnalyzer(config)
    result = await analyzer.analyze()
    
    print(f"\nAnalysis Complete!")
    print(f"Total traces: {result.total_traces}")
    print(f"Total issues: {result.stats['total_issues']}")
    print(f"Traces with issues: {result.stats['traces_with_issues']}")
    print(f"Processing time: {result.processing_time:.2f}s")
    
    print(f"\nIssues by severity:")
    for severity, count in result.stats['by_severity'].items():
        print(f"  {severity}: {count}")
    
    print(f"\nIssues by type:")
    for issue_type, count in result.stats['by_type'].items():
        print(f"  {issue_type}: {count}")


if __name__ == '__main__':
    asyncio.run(main())
