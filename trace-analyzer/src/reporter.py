import json
from pathlib import Path
from datetime import datetime
from src.models import AnalysisResult


class Reporter:
    def __init__(self, config: dict):
        self.config = config
        self.output_dir = Path(config['databases']['output_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, result: AnalysisResult):
        output_file = self.output_dir / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'timestamp': result.timestamp.isoformat(),
            'total_traces': result.total_traces,
            'processing_time_seconds': result.processing_time,
            'stats': result.stats,
            'issues': [
                {
                    'trace_id': issue.trace_id,
                    'issue_type': issue.issue_type.value,
                    'severity': issue.severity.value,
                    'detector': issue.detector_name,
                    'message': issue.message,
                    'details': issue.details
                }
                for issue in result.issues
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nReport saved to: {output_file}")
        return output_file
