import os
import asyncio
from typing import Optional
from src.models import TraceData, Issue, IssueType, Severity
from src.detectors import BaseDetector


def _get_api_key(config: dict) -> str:
    """获取 API key，优先从配置读取，其次从环境变量"""
    api_key = config.get('api_key')
    if api_key:
        return api_key
    
    env_var = config.get('api_key_env', 'OPENAI_API_KEY')
    return os.getenv(env_var, '')


class AIDetector(BaseDetector):
    def __init__(self, config: dict):
        self.config = config
        self.provider = config.get('provider', 'openai')
        self.model = config.get('model', 'gpt-4')
        self.criteria = config.get('criteria', [])
        self.batch_size = config.get('batch_size', 10)
        self.client: Optional[object] = None
        self.base_url: Optional[str] = None
        self.progress_callback = None
    
    @property
    def name(self) -> str:
        return "ai_detector"
    
    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback
    
    async def _init_client(self):
        api_key = _get_api_key(self.config)
        
        if not api_key:
            raise ValueError(f"API key not found. Set api_key in config or {self.config.get('api_key_env')} environment variable")
        
        if self.provider == 'openai':
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=api_key)
                if self.config.get('base_url'):
                    self.client.base_url = self.config.get('base_url')
            except ImportError:
                raise RuntimeError("openai package not installed. Run: pip install openai")
        
        elif self.provider == 'glm':
            try:
                from openai import AsyncOpenAI
                self.base_url = self.config.get('base_url', 'https://open.bigmodel.cn/api/paas/v4')
                self.client = AsyncOpenAI(api_key=api_key, base_url=self.base_url)
            except ImportError:
                raise RuntimeError("openai package not installed. Run: pip install openai")
        
        elif self.provider == 'openrouter':
            try:
                from openai import AsyncOpenAI
                self.base_url = self.config.get('base_url', 'https://openrouter.ai/api/v1')
                self.client = AsyncOpenAI(api_key=api_key, base_url=self.base_url)
            except ImportError:
                raise RuntimeError("openai package not installed. Run: pip install openai")
    
    async def detect(self, traces: list[TraceData]) -> list[Issue]:
        if not self.criteria:
            return []
        
        if self.client is None:
            await self._init_client()
        
        issues = []
        total = len(traces) * len(self.criteria)
        processed = 0
        
        for i in range(0, len(traces), self.batch_size):
            batch = traces[i:i + self.batch_size]
            batch_issues = await self._analyze_batch(batch)
            issues.extend(batch_issues)
            processed += len(batch) * len(self.criteria)
            
            if self.progress_callback:
                self.progress_callback(processed, total)
        
        return issues
    
    async def _analyze_batch(self, traces: list[TraceData]) -> list[Issue]:
        tasks = []
        for trace in traces:
            for criterion in self.criteria:
                tasks.append(self._check_criterion(trace, criterion))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        issues = []
        for result in results:
            if isinstance(result, Issue):
                issues.append(result)
        return issues
    
    async def _check_criterion(self, trace: TraceData, criterion: dict) -> Issue | None:
        response = self._extract_response(trace)
        if not response:
            return None
        
        prompt_template = criterion.get('prompt_template', '')
        prompt = prompt_template.replace('{response}', response[:2000])
        
        try:
            result = await self._call_llm(prompt)
            if self._is_issue(result):
                return Issue(
                    trace_id=trace.trace_id,
                    issue_type=IssueType.AI_DETECTED,
                    severity=Severity.WARNING,
                    detector_name=self.name,
                    message=f"AI detected issue: {criterion.get('name')}",
                    details={'criterion': criterion.get('name'), 'analysis': result}
                )
        except Exception as e:
            pass
        return None
    
    async def _call_llm(self, prompt: str) -> str:
        if self.provider in ['openai', 'glm', 'openrouter']:
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                return ""
        return ""
    
    def _extract_response(self, trace: TraceData) -> str:
        data = trace.data
        if isinstance(data, dict):
            for key in ['response', 'output', 'content', 'message', 'result', 'final_response']:
                if key in data and isinstance(data[key], str):
                    return data[key]
                if isinstance(data.get(key), dict):
                    return data[key].get('content', '') or data[key].get('text', '')
            
            if 'records' in data:
                for record in data['records']:
                    if record.get('role') == 'assistant' and record.get('content'):
                        return record['content']
        
        return str(data.get('response', '')) if isinstance(data, dict) else ''
    
    def _is_issue(self, result: str) -> bool:
        result_lower = result.lower()
        return any(word in result_lower for word in ['yes', 'true', 'issue', 'error', 'problem', 'concern'])
