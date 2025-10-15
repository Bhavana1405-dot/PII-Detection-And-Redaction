"""
Unit tests for image redaction
"""
import unittest
from Redactopii.redactors.image_redactor import ImageRedactor
from Redactopii.core.config import RedactionConfig


class TestImageRedaction(unittest.TestCase):
    """Test image redaction functionality"""
    
    def setUp(self):
        self.config = RedactionConfig()
        self.redactor = ImageRedactor(self.config)
    
    def test_validate_image_type(self):
        """Test image type validation"""
        self.assertTrue(self.redactor.validate_input("test.png"))
        self.assertTrue(self.redactor.validate_input("test.jpg"))
        self.assertFalse(self.redactor.validate_input("test.txt"))


if __name__ == '__main__':
    unittest.main()