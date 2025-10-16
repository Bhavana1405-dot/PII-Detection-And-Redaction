# =============================================================================
# FILE: Redactopii/core/models.py
# DESCRIPTION: Data models for PII redaction system
# =============================================================================

"""
Data models for PII redaction system
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict
from enum import Enum


class PIIType(Enum):
    """PII entity types"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    NAME = "name"
    ADDRESS = "address"
    CREDIT_CARD = "credit_card"
    DATE_OF_BIRTH = "date_of_birth"
    DRIVER_LICENSE = "driver_license"
    PASSPORT = "passport"
    CUSTOM = "custom"


class RedactionMethod(Enum):
    """Redaction techniques"""
    MASK = "mask"
    BLUR = "blur"
    BLACKBOX = "blackbox"
    PIXELATE = "pixelate"
    HASH = "hash"
    ENCRYPT = "encrypt"


@dataclass
class BoundingBox:
    """Image coordinates for PII location"""
    x: int
    y: int
    width: int
    height: int
    page: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PIIEntity:
    """Unified PII entity from detection"""
    entity_type: PIIType
    value: str
    confidence: float
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    bounding_box: Optional[BoundingBox] = None
    context: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = {
            "entity_type": self.entity_type.value,
            "value": self.value,
            "confidence": self.confidence,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "context": self.context
        }
        if self.bounding_box:
            result["bounding_box"] = self.bounding_box.to_dict()
        return result


@dataclass
class RedactionResult:
    """Result of redaction operation"""
    original_entity: PIIEntity
    redacted_value: str
    method: RedactionMethod
    timestamp: str
    file_path: str
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "original_entity": self.original_entity.to_dict(),
            "redacted_value": self.redacted_value,
            "method": self.method.value,
            "timestamp": self.timestamp,
            "file_path": self.file_path,
            "success": self.success,
            "error_message": self.error_message
        }