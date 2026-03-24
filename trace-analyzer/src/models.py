from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from enum import Enum


class Severity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class IssueType(Enum):
    RULE_VIOLATION = "rule_violation"
    STATISTICAL_ANOMALY = "statistical_anomaly"
    AI_DETECTED = "ai_detected"
    CONTENT_PATTERN = "content_pattern"


@dataclass
class Issue:
    trace_id: str
    issue_type: IssueType
    severity: Severity
    detector_name: str
    message: str
    details: dict = field(default_factory=dict)
    timestamp: Optional[datetime] = None


@dataclass
class TraceData:
    trace_id: str
    data: dict
    duration_ms: Optional[float] = None
    total_tokens: Optional[int] = None
    response_length: Optional[int] = None
    has_error: Optional[bool] = None
    timestamp: Optional[datetime] = None


@dataclass
class AnalysisResult:
    total_traces: int
    issues: list[Issue]
    stats: dict[str, Any]
    processing_time: float
    timestamp: datetime = field(default_factory=datetime.now)
