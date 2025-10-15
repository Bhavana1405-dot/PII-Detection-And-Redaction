"""
Custom exceptions for PII redaction system
"""

class RedactionException(Exception):
    """Base exception for redaction errors"""
    pass


class InvalidFileTypeException(RedactionException):
    """Raised when file type is not supported"""
    pass


class RedactionFailedException(RedactionException):
    """Raised when redaction operation fails"""
    pass


class ConfigurationException(RedactionException):
    """Raised for configuration errors"""
    pass


class EncryptionException(RedactionException):
    """Raised for encryption-related errors"""
    pass