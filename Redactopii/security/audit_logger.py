"""
Implements audit logging for redaction operations
"""
import json
import datetime
import os

class AuditLogger:
    """Logs all redaction actions for traceability and compliance"""
    
    def __init__(self, log_dir: str = "outputs/audit_logs"):
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"audit_{timestamp}.json")

    def log_action(self, action: str, details: dict):
        """Appends an entry to the audit log"""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def log_pipeline_event(self, stage: str, status: str):
        """Simplified event log (for pipeline milestones)"""
        self.log_action("pipeline_event", {"stage": stage, "status": status})
