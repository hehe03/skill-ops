import json
import glob
from pathlib import Path
from typing import Iterator
from src.models import TraceData


class TraceLoader:
    def __init__(self, trace_dir: str):
        self.trace_dir = Path(trace_dir)
    
    def load_single(self, file_path: Path) -> TraceData:
        if file_path.suffix == '.jsonl':
            return self._load_jsonl(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return self._parse_trace(data)
    
    def _load_jsonl(self, file_path: Path) -> TraceData:
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        trace_id = file_path.stem
        
        first_user_msg = None
        final_response = None
        tool_count = 0
        has_error = False
        latency_ms = None
        total_tokens = 0
        
        for record in records:
            if record.get('role') == 'user' and first_user_msg is None:
                first_user_msg = record.get('content', '')
            
            if record.get('role') == 'assistant':
                content = record.get('content', '')
                if content:
                    final_response = content
            
            if record.get('role') == 'tool':
                tool_count += 1
                content = record.get('content', '')
                if content:
                    total_tokens += len(content)
                
                if record.get('has_error'):
                    has_error = True
                
                if record.get('latency_ms'):
                    latency_ms = record.get('latency_ms')
        
        data = {
            'trace_id': trace_id,
            'records': records,
            'user_query': first_user_msg,
            'final_response': final_response,
            'tool_count': tool_count,
            'has_error': has_error,
            'latency_ms': latency_ms,
            'total_tokens': total_tokens
        }
        
        return TraceData(
            trace_id=trace_id,
            data=data,
            duration_ms=latency_ms,
            total_tokens=total_tokens if total_tokens > 0 else None,
            response_length=len(final_response) if final_response else 0,
            has_error=has_error
        )
    
    def load_all(self) -> list[TraceData]:
        traces = []
        for file_path in self._find_files():
            traces.append(self.load_single(file_path))
        return traces
    
    def iter_batches(self, batch_size: int) -> Iterator[list[TraceData]]:
        batch = []
        for file_path in self._find_files():
            batch.append(self.load_single(file_path))
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch
    
    def _find_files(self) -> list[Path]:
        patterns = ['**/*.json', '**/*.jsonl']
        files = []
        for pattern in patterns:
            files.extend(self.trace_dir.glob(pattern))
        return sorted(files)
    
    def _parse_trace(self, data: dict) -> TraceData:
        trace_id = data.get('trace_id') or data.get('id') or data.get('_id', 'unknown')
        
        duration_ms = self._extract_number(data, ['duration_ms', 'duration', 'latency'])
        total_tokens = self._extract_int(data, ['total_tokens', 'tokens', 'usage.total_tokens'])
        response_length = self._extract_int(data, ['response_length', 'response.length', 'output_length'])
        has_error = self._extract_bool(data, ['has_error', 'error', 'is_error'])
        
        timestamp = data.get('timestamp') or data.get('created_at')
        
        return TraceData(
            trace_id=trace_id,
            data=data,
            duration_ms=duration_ms,
            total_tokens=total_tokens,
            response_length=response_length,
            has_error=has_error,
            timestamp=timestamp
        )
    
    def _extract_field(self, data: dict, keys: list[str]):
        for key in keys:
            if '.' in key:
                parts = key.split('.')
                value = data
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        return None
                return value
            else:
                value = data.get(key)
                if value is not None:
                    return value
        return None
    
    def _extract_number(self, data: dict, keys: list[str]) -> float | None:
        value = self._extract_field(data, keys)
        if value is not None and isinstance(value, (int, float)):
            return float(value)
        return None
    
    def _extract_int(self, data: dict, keys: list[str]) -> int | None:
        value = self._extract_field(data, keys)
        if value is not None and isinstance(value, int):
            return value
        return None
    
    def _extract_bool(self, data: dict, keys: list[str]) -> bool | None:
        value = self._extract_field(data, keys)
        if value is not None:
            return bool(value)
        return None
