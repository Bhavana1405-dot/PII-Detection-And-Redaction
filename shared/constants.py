"""
Shared constants between detection and redaction
"""

# File type constants
SUPPORTED_IMAGE_FORMATS = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
SUPPORTED_TEXT_FORMATS = ['.txt', '.csv', '.json']
SUPPORTED_DOC_FORMATS = ['.pdf', '.docx']

# PII type patterns
PII_TYPES = [
    "email", "phone", "ssn", "name", "address", 
    "credit_card", "date_of_birth", "driver_license", "passport"
]

# Confidence thresholds
DEFAULT_CONFIDENCE_THRESHOLD = 0.7
HIGH_CONFIDENCE_THRESHOLD = 0.9
LOW_CONFIDENCE_THRESHOLD = 0.5