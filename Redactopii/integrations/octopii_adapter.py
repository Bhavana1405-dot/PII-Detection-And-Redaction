# =============================================================================
# FILE: Redactopii/integrations/octopii_adapter.py
# DESCRIPTION: Complete adapter for ACTUAL Octopii output format
# =============================================================================

"""
Adapter to parse actual Octopii detection reports
Handles the real output format from Octopii scanner
"""
from typing import Dict, List, Optional
import re
from ..core.models import PIIEntity, PIIType, BoundingBox


class OctopiiAdapter:
    """
    Parse and convert Octopii reports to internal format.
    
    Octopii Output Format:
    {
        "file_path": "document.txt",
        "pii_class": "financial",
        "score": 45,
        "country_of_origin": "US",
        "faces": 0,
        "identifiers": ["123-45-6789", "DL12345"],
        "emails": ["user@example.com"],
        "phone_numbers": ["+1-555-123-4567"],
        "addresses": ["123 Main St, City, State"]
    }
    """
    
    @staticmethod
    def parse_report(report: Dict) -> List[PIIEntity]:
        """
        Convert Octopii JSON report to PIIEntity list
        
        Args:
            report: Dictionary from Octopii output.json
            
        Returns:
            List of PIIEntity objects ready for redaction
        """
        entities = []
        
        # Parse emails with high confidence
        for email in report.get("emails", []):
            entities.append(PIIEntity(
                entity_type=PIIType.EMAIL,
                value=email,
                confidence=0.95,
                start_pos=None,  # Octopii doesn't provide position data
                end_pos=None,
                bounding_box=None,
                context=f"Email found in {report.get('file_path', 'unknown')}"
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
                context=f"Phone found in {report.get('file_path', 'unknown')}"
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
                context=f"Address found in {report.get('file_path', 'unknown')}"
            ))
        
        # Parse identifiers (SSN, license, credit cards, etc.)
        identifiers = report.get("identifiers", [])
        if identifiers and isinstance(identifiers, list):
            for identifier in identifiers:
                id_type, confidence = OctopiiAdapter._detect_identifier_type(identifier)
                
                entities.append(PIIEntity(
                    entity_type=id_type,
                    value=identifier,
                    confidence=confidence,
                    start_pos=None,
                    end_pos=None,
                    bounding_box=None,
                    context=f"ID found in {report.get('file_path', 'unknown')}"
                ))
        
        # Add face detection as NAME entity (since faces indicate people)
        faces_count = report.get("faces", 0)
        if faces_count > 0:
            entities.append(PIIEntity(
                entity_type=PIIType.NAME,
                value=f"[{faces_count} face(s) detected]",
                confidence=0.80,
                start_pos=None,
                end_pos=None,
                bounding_box=None,
                context=f"Face detection in {report.get('file_path', 'unknown')}"
            ))
        
        return entities
    
    @staticmethod
    def _detect_identifier_type(identifier: str) -> tuple[PIIType, float]:
        """
        Detect identifier type from pattern and return confidence
        
        Args:
            identifier: String identifier from Octopii
            
        Returns:
            Tuple of (PIIType, confidence_score)
        """
        # SSN pattern: XXX-XX-XXXX or XXXXXXXXX
        if re.match(r'^\d{3}-\d{2}-\d{4}$', identifier) or re.match(r'^\d{9}$', identifier):
            return PIIType.SSN, 0.95
        
        # Credit card: 13-19 digits with optional spaces/dashes
        clean_id = identifier.replace(' ', '').replace('-', '')
        if re.match(r'^\d{13,19}$', clean_id):
            if OctopiiAdapter._luhn_check(clean_id):
                return PIIType.CREDIT_CARD, 0.98
            return PIIType.CREDIT_CARD, 0.85
        
        # Passport number: Usually 6-9 alphanumeric
        if re.match(r'^[A-Z0-9]{6,9}$', identifier.upper()):
            return PIIType.PASSPORT, 0.75
        
        # Driver's license: Varies by region, typically alphanumeric
        if re.match(r'^[A-Z]{1,2}\d{5,8}$', identifier.upper()) or \
           re.match(r'^\d{7,9}$', identifier):
            return PIIType.DRIVER_LICENSE, 0.80
        
        # Date of birth patterns: YYYY-MM-DD, MM/DD/YYYY, etc.
        if re.match(r'^\d{4}-\d{2}-\d{2}$', identifier) or \
           re.match(r'^\d{2}/\d{2}/\d{4}$', identifier) or \
           re.match(r'^\d{2}-\d{2}-\d{4}$', identifier):
            return PIIType.DATE_OF_BIRTH, 0.90
        
        # Default to custom for unknown patterns
        return PIIType.CUSTOM, 0.70
    
    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        """
        Validate credit card number using Luhn algorithm
        
        Args:
            card_number: Clean numeric string
            
        Returns:
            True if valid credit card number
        """
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
        """
        Enhanced parser that finds positions in source text if available
        
        Args:
            report: Octopii report dictionary
            source_text: Optional source text to find positions in
            
        Returns:
            List of PIIEntity objects with position data when possible
        """
        entities = []
        
        # If we have source text, we can find exact positions
        if source_text:
            # Find emails with positions
            for email in report.get("emails", []):
                match = re.search(re.escape(email), source_text)
                if match:
                    entities.append(PIIEntity(
                        entity_type=PIIType.EMAIL,
                        value=email,
                        confidence=0.95,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        bounding_box=None,
                        context=source_text[max(0, match.start()-20):match.end()+20]
                    ))
                else:
                    # Fallback: add without position
                    entities.append(PIIEntity(
                        entity_type=PIIType.EMAIL,
                        value=email,
                        confidence=0.95,
                        start_pos=None,
                        end_pos=None,
                        bounding_box=None,
                        context=None
                    ))
            
            # Find phone numbers with positions
            for phone in report.get("phone_numbers", []):
                match = re.search(re.escape(phone), source_text)
                if match:
                    entities.append(PIIEntity(
                        entity_type=PIIType.PHONE,
                        value=phone,
                        confidence=0.90,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        bounding_box=None,
                        context=source_text[max(0, match.start()-20):match.end()+20]
                    ))
                else:
                    entities.append(PIIEntity(
                        entity_type=PIIType.PHONE,
                        value=phone,
                        confidence=0.90,
                        start_pos=None,
                        end_pos=None,
                        bounding_box=None,
                        context=None
                    ))
            
            # Find addresses with positions (more complex due to multi-line)
            for address in report.get("addresses", []):
                # Try to find address (may need fuzzy matching)
                match = re.search(re.escape(address), source_text, re.IGNORECASE)
                if match:
                    entities.append(PIIEntity(
                        entity_type=PIIType.ADDRESS,
                        value=address,
                        confidence=0.85,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        bounding_box=None,
                        context=source_text[max(0, match.start()-20):match.end()+20]
                    ))
                else:
                    entities.append(PIIEntity(
                        entity_type=PIIType.ADDRESS,
                        value=address,
                        confidence=0.85,
                        start_pos=None,
                        end_pos=None,
                        bounding_box=None,
                        context=None
                    ))
            
            # Find identifiers with positions
            for identifier in report.get("identifiers", []):
                id_type, confidence = OctopiiAdapter._detect_identifier_type(identifier)
                match = re.search(re.escape(identifier), source_text)
                
                if match:
                    entities.append(PIIEntity(
                        entity_type=id_type,
                        value=identifier,
                        confidence=confidence,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        bounding_box=None,
                        context=source_text[max(0, match.start()-20):match.end()+20]
                    ))
                else:
                    entities.append(PIIEntity(
                        entity_type=id_type,
                        value=identifier,
                        confidence=confidence,
                        start_pos=None,
                        end_pos=None,
                        bounding_box=None,
                        context=None
                    ))
        else:
            # No source text, use basic parsing
            entities = OctopiiAdapter.parse_report(report)
        
        return entities
    
    @staticmethod
    def parse_multiple_reports(reports: List[Dict]) -> Dict[str, List[PIIEntity]]:
        """
        Parse multiple Octopii reports (for batch processing)
        
        Args:
            reports: List of Octopii report dictionaries
            
        Returns:
            Dictionary mapping file paths to entity lists
        """
        results = {}
        
        for report in reports:
            file_path = report.get("file_path", "unknown")
            entities = OctopiiAdapter.parse_report(report)
            results[file_path] = entities
        
        return results
    
    @staticmethod
    def get_summary_stats(report: Dict) -> Dict:
        """
        Get summary statistics from Octopii report
        
        Args:
            report: Octopii report dictionary
            
        Returns:
            Dictionary with summary statistics
        """
        return {
            "file_path": report.get("file_path", "unknown"),
            "pii_class": report.get("pii_class"),
            "score": report.get("score", 0),
            "country": report.get("country_of_origin"),
            "has_faces": report.get("faces", 0) > 0,
            "total_pii_count": (
                len(report.get("emails", [])) +
                len(report.get("phone_numbers", [])) +
                len(report.get("addresses", [])) +
                len(report.get("identifiers", []))
            ),
            "breakdown": {
                "emails": len(report.get("emails", [])),
                "phones": len(report.get("phone_numbers", [])),
                "addresses": len(report.get("addresses", [])),
                "identifiers": len(report.get("identifiers", []))
            }
        }


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

if __name__ == "__main__":
    # Example 1: Parse basic Octopii report
    sample_report = {
        "file_path": "customer_data.txt",
        "pii_class": "financial",
        "score": 67,
        "country_of_origin": "US",
        "faces": 0,
        "identifiers": ["123-45-6789", "4532015112830366"],
        "emails": ["john.doe@example.com", "jane@company.org"],
        "phone_numbers": ["+1-555-123-4567", "555-987-6543"],
        "addresses": ["123 Main St, Springfield, IL 62701"]
    }
    
    print("=" * 70)
    print("Example 1: Basic Parsing")
    print("=" * 70)
    
    adapter = OctopiiAdapter()
    entities = adapter.parse_report(sample_report)
    
    print(f"\nFound {len(entities)} PII entities:")
    for entity in entities:
        print(f"  - {entity.entity_type.value}: {entity.value} (confidence: {entity.confidence})")
    
    # Example 2: Get summary statistics
    print("\n" + "=" * 70)
    print("Example 2: Summary Statistics")
    print("=" * 70)
    
    stats = adapter.get_summary_stats(sample_report)
    print(f"\nFile: {stats['file_path']}")
    print(f"PII Class: {stats['pii_class']}")
    print(f"Score: {stats['score']}")
    print(f"Total PII: {stats['total_pii_count']}")
    print(f"Breakdown: {stats['breakdown']}")
    
    # Example 3: Enhanced parsing with source text
    print("\n" + "=" * 70)
    print("Example 3: Enhanced Parsing with Positions")
    print("=" * 70)
    
    source_text = """
    Customer Information:
    Name: John Doe
    Email: john.doe@example.com
    Phone: +1-555-123-4567
    SSN: 123-45-6789
    Address: 123 Main St, Springfield, IL 62701
    Credit Card: 4532015112830366
    """
    
    enriched_entities = adapter.enrich_with_positions(sample_report, source_text)
    
    print(f"\nFound {len(enriched_entities)} entities with positions:")
    for entity in enriched_entities:
        if entity.start_pos is not None:
            print(f"  - {entity.entity_type.value}: {entity.value}")
            print(f"    Position: {entity.start_pos}-{entity.end_pos}")
            print(f"    Context: ...{entity.context}...")
        else:
            print(f"  - {entity.entity_type.value}: {entity.value} (no position found)")
    
    # Example 4: Batch processing
    print("\n" + "=" * 70)
    print("Example 4: Batch Processing")
    print("=" * 70)
    
    batch_reports = [
        sample_report,
        {
            "file_path": "employee_records.pdf",
            "pii_class": "personal",
            "score": 45,
            "country_of_origin": "UK",
            "faces": 2,
            "identifiers": ["AB123456C"],
            "emails": ["employee@company.com"],
            "phone_numbers": ["+44-20-1234-5678"],
            "addresses": ["10 Downing Street, London"]
        }
    ]
    
    batch_results = adapter.parse_multiple_reports(batch_reports)
    
    print(f"\nProcessed {len(batch_results)} files:")
    for file_path, entities in batch_results.items():
        print(f"  - {file_path}: {len(entities)} entities")
    
    print("\n" + "=" * 70)
    print("Adapter ready for integration!")
    print("=" * 70)