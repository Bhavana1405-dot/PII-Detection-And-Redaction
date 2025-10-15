"""
Unit tests for text redaction
"""
import unittest
from Redactopii.core.models import PIIEntity, PIIType
from Redactopii.redactors.text_redactor import TextRedactor
from Redactopii.core.config import RedactionConfig


class TestTextRedaction(unittest.TestCase):
    """Test text redaction functionality"""
    
    def setUp(self):
        self.config = RedactionConfig()
        self.redactor = TextRedactor(self.config)
    
    def test_basic_masking(self):
        """Test basic text masking"""
        text = "Email: john@example.com"
        entity = PIIEntity(
            entity_type=PIIType.EMAIL,
            value="john@example.com",
            confidence=0.9,
            start_pos=7,
            end_pos=23
        )
        
        redacted, results = self.redactor.redact(text, [entity])
        
        self.assertNotIn("john@example.com", redacted)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].success)


if __name__ == '__main__':
    unittest.main()