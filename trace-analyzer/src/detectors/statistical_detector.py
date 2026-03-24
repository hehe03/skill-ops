import statistics
from src.models import TraceData, Issue, IssueType, Severity
from src.detectors import BaseDetector


class StatisticalDetector(BaseDetector):
    def __init__(self, methods: list[dict]):
        self.methods = methods
    
    @property
    def name(self) -> str:
        return "statistical_detector"
    
    def detect(self, traces: list[TraceData]) -> list[Issue]:
        issues = []
        field_values = self._collect_field_values(traces)
        
        for method in self.methods:
            method_name = method.get('name')
            fields = method.get('fields', [])
            
            if method_name == 'zscore':
                issues.extend(self._detect_zscore(field_values, method))
            elif method_name == 'iqr':
                issues.extend(self._detect_iqr(field_values, method))
        
        return issues
    
    def _collect_field_values(self, traces: list[TraceData]) -> dict[str, list[tuple[str, float]]]:
        field_values: dict[str, list[tuple[str, float]]] = {}
        for trace in traces:
            for field in ['duration_ms', 'total_tokens', 'response_length']:
                value = getattr(trace, field, None)
                if value is not None:
                    if field not in field_values:
                        field_values[field] = []
                    field_values[field].append((trace.trace_id, float(value)))
        return field_values
    
    def _detect_zscore(self, field_values: dict, method: dict) -> list[Issue]:
        issues = []
        threshold = method.get('threshold', 3.0)
        target_fields = method.get('fields', list(field_values.keys()))
        
        for field in target_fields:
            if field not in field_values:
                continue
            
            values = [v[1] for v in field_values[field]]
            if len(values) < 3:
                continue
            
            mean = statistics.mean(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 0
            
            if stdev == 0:
                continue
            
            for trace_id, value in field_values[field]:
                zscore = abs((value - mean) / stdev)
                if zscore > threshold:
                    issues.append(Issue(
                        trace_id=trace_id,
                        issue_type=IssueType.STATISTICAL_ANOMALY,
                        severity=Severity.WARNING,
                        detector_name=self.name,
                        message=f"Statistical anomaly detected: {field} value {value:.2f} has z-score {zscore:.2f}",
                        details={'field': field, 'zscore': zscore, 'mean': mean, 'stdev': stdev}
                    ))
        return issues
    
    def _detect_iqr(self, field_values: dict, method: dict) -> list[Issue]:
        issues = []
        multiplier = method.get('multiplier', 1.5)
        target_fields = method.get('fields', list(field_values.keys()))
        
        for field in target_fields:
            if field not in field_values:
                continue
            
            values = sorted([v[1] for v in field_values[field]])
            if len(values) < 4:
                continue
            
            q1 = statistics.quantiles(values, n=4)[0]
            q3 = statistics.quantiles(values, n=4)[2]
            iqr = q3 - q1
            lower_bound = q1 - multiplier * iqr
            upper_bound = q3 + multiplier * iqr
            
            for trace_id, value in field_values[field]:
                if value < lower_bound or value > upper_bound:
                    issues.append(Issue(
                        trace_id=trace_id,
                        issue_type=IssueType.STATISTICAL_ANOMALY,
                        severity=Severity.WARNING,
                        detector_name=self.name,
                        message=f"IQR anomaly detected: {field} value {value:.2f} outside [{lower_bound:.2f}, {upper_bound:.2f}]",
                        details={'field': field, 'q1': q1, 'q3': q3, 'iqr': iqr}
                    ))
        return issues
