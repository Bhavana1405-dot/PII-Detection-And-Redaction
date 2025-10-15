"""
Integration layer connecting detection and redaction engines
"""
import os
from typing import List, Tuple
from ..core.redaction_engine import RedactionEngine
from .octopii_adapter import OctopiiAdapter
from ..core.models import PIIEntity

class PipelineIntegration:
    """Runs the end-to-end detection → redaction pipeline"""
    
    def __init__(self, redaction_config: dict):
        self.redaction_engine = RedactionEngine(redaction_config)
    
    def run(self, input_path: str, report_path: str, output_dir: str) -> Tuple[str, List[PIIEntity]]:
        """Executes the full pipeline"""
        print(f"[Pipeline] Loading detection report from: {report_path}")
        detected_entities = OctopiiAdapter.parse_report(report_path)
        
        print(f"[Pipeline] Running redaction on: {input_path}")
        redacted_file, results = self.redaction_engine.redact_file(input_path, detected_entities, output_dir)
        
        print(f"[Pipeline] Redaction completed: {redacted_file}")
        return redacted_file, results
