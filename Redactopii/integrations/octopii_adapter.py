# =============================================================================
# FILE: Redactopii/integrations/octopii_adapter.py
# DESCRIPTION: Complete adapter for ACTUAL Octopii output format
# =============================================================================

from typing import Dict, List, Optional
import re
from core.models import PIIEntity, PIIType, BoundingBox


class OctopiiAdapter:
    """Parse and convert Octopii reports to internal format"""
    
    @staticmethod
    def parse_report(report: Dict) -> List[PIIEntity]:
        """Convert Octopii JSON report to PIIEntity list"""
        entities = []
        
        # Parse emails
        for email in report.get("emails", []):
            entities.append(PIIEntity(
                entity_type=PIIType.EMAIL,
                value=email,
                confidence=0.95,
                start_pos=None,
                end_pos=None,
                bounding_box=None,
                context=f"Email in {report.get('file_path', 'unknown')}"
            ))
        
        # Parse phone numbers
        for phone in report.get("phone_numbers", []):
            entities.append(PIIEntity(
                entity_type=PIIType.PHONE,
                value=phone,
                confidence=0.90,
                start_pos=None,
                end_pos=None,
                bounding_box=None,
                context=f"Phone in {report.get('file_path', 'unknown')}"
            ))
        
        # Parse addresses
        for address in report.get("addresses", []):
            entities.append(PIIEntity(
                entity_type=PIIType.ADDRESS,
                value=address,
                confidence=0.85,
                start_pos=None,
                end_pos=None,
                bounding_box=None,
                context=f"Address in {report.get('file_path', 'unknown')}"
            ))
        
        # Parse identifiers
        for identifier in report.get("identifiers", []):
            id_type, confidence = OctopiiAdapter._detect_identifier_type(identifier)
            
            entities.append(PIIEntity(
                entity_type=id_type,
                value=identifier,
                confidence=confidence,
                start_pos=None,
                end_pos=None,
                bounding_box=None,
                context=f"ID in {report.get('file_path', 'unknown')}"
            ))
        
        return entities
    
    @staticmethod
    def _detect_identifier_type(identifier: str) -> tuple:
        """Detect identifier type from pattern"""
        # SSN pattern
        if re.match(r'^\d{3}-\d{2}-\d{4}$', identifier) or re.match(r'^\d{9}$', identifier):
            return PIIType.SSN, 0.95
        
        # Credit card
        clean_id = identifier.replace(' ', '').replace('-', '')
        if re.match(r'^\d{13,19}$', clean_id):
            if OctopiiAdapter._luhn_check(clean_id):
                return PIIType.CREDIT_CARD, 0.98
            return PIIType.CREDIT_CARD, 0.85
        
        # Passport
        if re.match(r'^[A-Z0-9]{6,9}$', identifier.upper()):
            return PIIType.PASSPORT, 0.75
        
        # Driver's license
        if re.match(r'^[A-Z]{1,2}\d{5,8}$', identifier.upper()) or \
           re.match(r'^\d{7,9}$', identifier):
            return PIIType.DRIVER_LICENSE, 0.80
        
        return PIIType.CUSTOM, 0.70
    
    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        """Validate credit card using Luhn algorithm"""
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        
        return checksum % 10 == 0
    
    @staticmethod
    def enrich_with_positions(report: Dict, source_text: Optional[str] = None) -> List[PIIEntity]:
        """Enhanced parser that finds positions in source text"""
        entities = []
        
        if not source_text:
            return OctopiiAdapter.parse_report(report)
        
        # Find emails with positions
        for email in report.get("emails", []):
            match = re.search(re.escape(email), source_text)
            entities.append(PIIEntity(
                entity_type=PIIType.EMAIL,
                value=email,
                confidence=0.95,
                start_pos=match.start() if match else None,
                end_pos=match.end() if match else None,
                bounding_box=None,
                context=source_text[max(0, match.start()-20):match.end()+20] if match else None
            ))
        
        # Find phones with positions
        for phone in report.get("phone_numbers", []):
            match = re.search(re.escape(phone), source_text)
            entities.append(PIIEntity(
                entity_type=PIIType.PHONE,
                value=phone,
                confidence=0.90,
                start_pos=match.start() if match else None,
                end_pos=match.end() if match else None,
                bounding_box=None,
                context=source_text[max(0, match.start()-20):match.end()+20] if match else None
            ))
        
        # Find addresses with positions
        for address in report.get("addresses", []):
            match = re.search(re.escape(address), source_text, re.IGNORECASE)
            entities.append(PIIEntity(
                entity_type=PIIType.ADDRESS,
                value=address,
                confidence=0.85,
                start_pos=match.start() if match else None,
                end_pos=match.end() if match else None,
                bounding_box=None,
                context=source_text[max(0, match.start()-20):match.end()+20] if match else None
            ))
        
        # Find identifiers with positions
        for identifier in report.get("identifiers", []):
            id_type, confidence = OctopiiAdapter._detect_identifier_type(identifier)
            match = re.search(re.escape(identifier), source_text)
            
            entities.append(PIIEntity(
                entity_type=id_type,
                value=identifier,
                confidence=confidence,
                start_pos=match.start() if match else None,
                end_pos=match.end() if match else None,
                bounding_box=None,
                context=source_text[max(0, match.start()-20):match.end()+20] if match else None
            ))
        
        return entities