from abc import ABC, abstractmethod
from src.models import TraceData, Issue, IssueType, Severity


class BaseDetector(ABC):
    @abstractmethod
    def detect(self, traces: list[TraceData]) -> list[Issue]:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
