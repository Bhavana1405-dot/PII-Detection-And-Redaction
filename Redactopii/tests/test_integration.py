"""
Integration tests
"""
import unittest
from Redactopii.core.redaction_engine import RedactionEngine
from Redactopii.core.config import RedactionConfig


class TestIntegration(unittest.TestCase):
    """Test full integration"""
    
    def setUp(self):
        self.config = RedactionConfig()
        self.engine = RedactionEngine(self.config)
    
    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.logger)


if __name__ == '__main__':
    unittest.main()