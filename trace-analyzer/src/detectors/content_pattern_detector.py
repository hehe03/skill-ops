from src.models import TraceData, Issue, IssueType, Severity
from src.detectors import BaseDetector


class ContentPatternDetector(BaseDetector):
    def __init__(self, config: dict = None):
        self.config = config or {}
    
    @property
    def name(self) -> str:
        return "content_pattern_detector"
    
    def detect(self, traces: list[TraceData]) -> list[Issue]:
        issues = []
        for trace in traces:
            issues.extend(self._detect_patterns(trace))
        return issues
    
    def _detect_patterns(self, trace: TraceData) -> list[Issue]:
        issues = []
        records = trace.data.get('records', [])
        
        if not records:
            return issues
        
        user_query = self._get_user_query(records)
        
        issues.extend(self._check_intent_mismatch(records, user_query))
        issues.extend(self._check_skill_mismatch(records, user_query))
        issues.extend(self._check_empty_tool_calls(records))
        issues.extend(self._check_repeated_tool_calls(records))
        issues.extend(self._check_template_response(records, trace.trace_id))
        issues.extend(self._check_tool_errors(records))
        
        return issues
    
    def _get_user_query(self, records: list) -> str:
        for record in records:
            if record.get('role') == 'user':
                return record.get('content', '')
        return ''
    
    def _check_intent_mismatch(self, records: list, user_query: str) -> list[Issue]:
        issues = []
        for i, record in enumerate(records):
            if record.get('role') == 'tool' and record.get('tool_name') == 'query_rewriter':
                rewrite_result = record.get('content', '')
                if '->' in rewrite_result:
                    original = user_query
                    rewritten = rewrite_result.split('->')[-1].strip()
                    
                    if self._is_semantic_mismatch(original, rewritten):
                        issues.append(Issue(
                            trace_id=self._get_trace_id(records),
                            issue_type=IssueType.CONTENT_PATTERN,
                            severity=Severity.WARNING,
                            detector_name=self.name,
                            message=f"Intent mismatch: query rewritten to unrelated topic",
                            details={'original': original, 'rewritten': rewritten}
                        ))
        return issues
    
    def _is_semantic_mismatch(self, original: str, rewritten: str) -> bool:
        original_keywords = self._extract_keywords(original)
        rewritten_keywords = self._extract_keywords(rewritten)
        
        if not original_keywords or not rewritten_keywords:
            return False
        
        overlap = len(set(original_keywords) & set(rewritten_keywords))
        return overlap == 0
    
    def _extract_keywords(self, text: str) -> list[str]:
        import re
        text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
        return [w for w in text if len(w) > 1]
    
    def _check_skill_mismatch(self, records: list, user_query: str) -> list[Issue]:
        issues = []
        for record in records:
            if record.get('role') == 'tool' and record.get('tool_name') == 'skill_orchestrator':
                content = record.get('content', '')
                if "Loading skill" in content:
                    import re
                    match = re.search(r"skill '([^']+)'", content)
                    if match:
                        skill_name = match.group(1)
                        loaded = record.get('skill_loaded', skill_name)
                        
                        if self._is_skill_mismatch(user_query, loaded):
                            issues.append(Issue(
                                trace_id=self._get_trace_id(records),
                                issue_type=IssueType.CONTENT_PATTERN,
                                severity=Severity.WARNING,
                                detector_name=self.name,
                                message=f"Skill mismatch: loaded '{loaded}' may not fit the issue",
                                details={'query': user_query, 'skill': loaded}
                            ))
        return issues
    
    def _is_skill_mismatch(self, query: str, skill: str) -> bool:
        query_lower = query.lower()
        
        if '邮件' in query or 'email' in query_lower:
            return skill not in ['email_fixer', 'email_installer', 'mail']
        if '软件' in query or '软件' in query:
            return skill not in ['software_installer', 'software_fixer']
        if '网络' in query or 'network' in query_lower:
            return skill not in ['network_fixer', 'network_installer']
        
        return False
    
    def _check_empty_tool_calls(self, records: list) -> list[Issue]:
        issues = []
        empty_count = 0
        
        for record in records:
            if record.get('role') == 'assistant' and record.get('tool_calls'):
                for tc in record.get('tool_calls', []):
                    args = tc.get('function', {}).get('arguments', '{}')
                    if args == '{}' or args == '':
                        empty_count += 1
        
        if empty_count >= 3:
            issues.append(Issue(
                trace_id=self._get_trace_id(records),
                issue_type=IssueType.CONTENT_PATTERN,
                severity=Severity.WARNING,
                detector_name=self.name,
                message=f"Excessive empty argument tool calls: {empty_count} calls with empty arguments",
                details={'empty_calls': empty_count}
            ))
        
        return issues
    
    def _check_repeated_tool_calls(self, records: list) -> list[Issue]:
        issues = []
        
        tool_sequence = []
        for record in records:
            if record.get('role') == 'tool':
                tool_sequence.append(record.get('tool_name', 'unknown'))
        
        repeated = self._find_consecutive_repeats(tool_sequence)
        if repeated:
            issues.append(Issue(
                trace_id=self._get_trace_id(records),
                issue_type=IssueType.CONTENT_PATTERN,
                severity=Severity.WARNING,
                detector_name=self.name,
                message=f"Repeated tool calls detected: {repeated['tool']} called {repeated['count']} times consecutively",
                details={'tool': repeated['tool'], 'count': repeated['count']}
            ))
        
        return issues
    
    def _find_consecutive_repeats(self, tool_sequence: list) -> dict | None:
        if len(tool_sequence) < 3:
            return None
        
        max_count = 1
        max_tool = None
        current_tool = tool_sequence[0]
        current_count = 1
        
        for i in range(1, len(tool_sequence)):
            if tool_sequence[i] == current_tool:
                current_count += 1
                if current_count > max_count:
                    max_count = current_count
                    max_tool = current_tool
            else:
                current_tool = tool_sequence[i]
                current_count = 1
        
        if max_count >= 3:
            return {'tool': max_tool, 'count': max_count}
        return None
    
    def _check_template_response(self, records: list, trace_id: str) -> list[Issue]:
        issues = []
        
        final_response = None
        for record in records:
            if record.get('role') == 'assistant' and record.get('content'):
                final_response = record.get('content', '')
        
        if final_response:
            template_indicators = [
                '首先请确认', '如需进一步帮助', '请点击「转人工服务」',
                '尝试清除', '检查本地网络'
            ]
            
            match_count = sum(1 for indicator in template_indicators if indicator in final_response)
            
            if match_count >= 5:
                issues.append(Issue(
                    trace_id=trace_id,
                    issue_type=IssueType.CONTENT_PATTERN,
                    severity=Severity.WARNING,
                    detector_name=self.name,
                    message=f"Template response detected: response uses generic template",
                    details={'template_matches': match_count, 'indicators': [i for i in template_indicators if i in final_response]}
                ))
        
        return issues
    
    def _check_tool_errors(self, records: list) -> list[Issue]:
        issues = []
        error_count = 0
        error_tools = []
        
        for record in records:
            if record.get('role') == 'tool' and record.get('has_error'):
                error_count += 1
                error_tools.append({
                    'tool': record.get('tool_name', 'unknown'),
                    'error': record.get('content', '')[:50]
                })
        
        if error_count >= 1:
            issues.append(Issue(
                trace_id=self._get_trace_id(records),
                issue_type=IssueType.CONTENT_PATTERN,
                severity=Severity.CRITICAL if error_count >= 2 else Severity.WARNING,
                detector_name=self.name,
                message=f"Tool execution errors: {error_count} tools failed",
                details={'error_count': error_count, 'errors': error_tools}
            ))
        
        return issues
    
    def _get_trace_id(self, records: list) -> str:
        return records[0].get('trace_id', 'unknown') if records else 'unknown'