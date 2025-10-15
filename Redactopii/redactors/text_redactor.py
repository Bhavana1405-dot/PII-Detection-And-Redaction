"""
Text-based redaction implementation
"""
from typing import List, Tuple
from datetime import datetime

from .base_redactor import BaseRedactor
from ..core.models import PIIEntity, RedactionResult, RedactionMethod

class TextRedactor(BaseRedactor):
    """Handles text content redaction"""
    
    def __init__(self, config):
        self.config = config
    
    def redact(self, text: str, entities: List[PIIEntity]) -> Tuple[str, List[RedactionResult]]:
        results = []
        redacted_text = text
        sorted_entities = sorted(
            [e for e in entities if e.start_pos is not None],
            key=lambda x: x.start_pos,
            reverse=True
        )
        for entity in sorted_entities:
            redacted_value = self._mask_text(entity.value)
            redacted_text = redacted_text[:entity.start_pos] + redacted_value + redacted_text[entity.end_pos:]
            results.append(RedactionResult(
                original_entity=entity,
                redacted_value=redacted_value,
                method=RedactionMethod.MASK,
                timestamp=datetime.now().isoformat(),
                file_path="",
                success=True
            ))
        return redacted_text, results
    
    def _mask_text(self, value: str) -> str:
        mask_char = self.config.get("mask_char", "█")
        return mask_char * len(value)
    
    def validate_input(self, text: str) -> bool:
        return isinstance(text, str)
