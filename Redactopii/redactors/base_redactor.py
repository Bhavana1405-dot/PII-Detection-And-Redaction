"""
Abstract base class for all redactors
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
from ..core.models import PIIEntity, RedactionResult

class BaseRedactor(ABC):
    """Base class for redaction implementations"""
    
    @abstractmethod
    def redact(self, source, entities: List[PIIEntity]) -> Tuple[any, List[RedactionResult]]:
        """Redact PII from source content"""
        pass
    
    @abstractmethod
    def validate_input(self, source) -> bool:
        """Validate input before redaction"""
        pass
