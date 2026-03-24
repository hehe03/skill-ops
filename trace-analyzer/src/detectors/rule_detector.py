from src.models import TraceData, Issue, IssueType, Severity
from src.detectors import BaseDetector


class RuleDetector(BaseDetector):
    def __init__(self, rules: list[dict]):
        self.rules = rules
    
    @property
    def name(self) -> str:
        return "rule_detector"
    
    def detect(self, traces: list[TraceData]) -> list[Issue]:
        issues = []
        for trace in traces:
            for rule in self.rules:
                issue = self._check_rule(trace, rule)
                if issue:
                    issues.append(issue)
        return issues
    
    def _check_rule(self, trace: TraceData, rule: dict) -> Issue | None:
        field = rule.get('field')
        operator = rule.get('operator')
        threshold = rule.get('threshold')
        value = rule.get('value')
        
        trace_value = getattr(trace, field, None)
        if trace_value is None:
            return None
        
        violated = False
        if operator == 'gt':
            violated = trace_value > threshold
        elif operator == 'gte':
            violated = trace_value >= threshold
        elif operator == 'lt':
            violated = trace_value < threshold
        elif operator == 'lte':
            violated = trace_value <= threshold
        elif operator == 'eq':
            violated = trace_value == value
        elif operator == 'neq':
            violated = trace_value != value
        
        if violated:
            severity = Severity(rule.get('severity', 'warning'))
            return Issue(
                trace_id=trace.trace_id,
                issue_type=IssueType.RULE_VIOLATION,
                severity=severity,
                detector_name=self.name,
                message=f"Rule '{rule.get('name')}' violated: {field} {operator} {threshold or value}",
                details={'rule': rule, 'actual_value': trace_value}
            )
        return None
