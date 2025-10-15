"""
Unit tests for audit logging
"""
import os
from security.audit_logger import AuditLogger

def test_audit_log_creation(tmp_path):
    log_file = tmp_path / "audit.log"
    logger = AuditLogger(str(log_file))
    
    logger.log_action("TEST_ACTION", details={"user": "demo"})
    
    assert log_file.exists()
    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "TEST_ACTION" in content
