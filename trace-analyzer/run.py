#!/usr/bin/env python3
import asyncio
import yaml
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.analyzer import TraceAnalyzer


async def main():
    config_path = project_root / 'config' / 'default.yaml'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    config['databases']['trace_dir'] = str(project_root / config['databases']['trace_dir'])
    config['databases']['output_dir'] = str(project_root / config['databases']['output_dir'])
    
    analyzer = TraceAnalyzer(config)
    result = await analyzer.analyze()
    
    print(f"\n{'='*50}")
    print(f"Trace Analysis Complete")
    print(f"{'='*50}")
    print(f"Total traces: {result.total_traces}")
    print(f"Traces with issues: {result.stats['traces_with_issues']}")
    print(f"Total issues: {result.stats['total_issues']}")
    print(f"Processing time: {result.processing_time:.2f}s")
    
    print(f"\nIssues by severity:")
    for severity, count in result.stats['by_severity'].items():
        print(f"  {severity}: {count}")
    
    print(f"\nIssues by type:")
    for issue_type, count in result.stats['by_type'].items():
        print(f"  {issue_type}: {count}")


if __name__ == '__main__':
    asyncio.run(main())
