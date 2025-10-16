# =============================================================================
# FILE: Redactopii/integrations/pipeline_integration.py
# DESCRIPTION: End-to-end pipeline integration
# =============================================================================

"""
End-to-end pipeline integration for Octopii detection + Redaction
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.redaction_engine import RedactionEngine
from integrations.octopii_adapter import OctopiiAdapter


class RedactionPipeline:
    """Full detection-to-redaction pipeline"""
    
    def __init__(self, engine: RedactionEngine):
        self.engine = engine
        self.adapter = OctopiiAdapter()
        self.processed_files = []
    
    def process_octopii_output(self, report_path: str, source_file: Optional[str] = None) -> Dict:
        """Process Octopii detection output and save redacted files"""
        
        # Load Octopii report
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Handle both single report and array
        if isinstance(report, list):
            return self.process_batch_reports(report)
        
        # Get source file path
        if source_file is None:
            source_file = report.get("file_path")
            if not source_file:
                raise ValueError("No source file path found in report")
        
        # Check if source file exists
        if not Path(source_file).exists():
            return {
                "status": "error",
                "error": f"Source file not found: {source_file}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Process file
        result = self.engine.process_octopii_report(report, source_file)
        
        # Track processed file
        self.processed_files.append({
            "source": source_file,
            "output": result.get("redaction", {}).get("output_path"),
            "timestamp": datetime.now().isoformat()
        })
        
        return result
    
    def process_batch_reports(self, reports: List[Dict]) -> Dict:
        """Process multiple Octopii reports in batch"""
        results = {
            "status": "batch_complete",
            "timestamp": datetime.now().isoformat(),
            "total_files": len(reports),
            "successful": 0,
            "failed": 0,
            "results": []
        }
        
        for report in reports:
            try:
                result = self.process_octopii_output(None, report.get("file_path"))
                
                if result.get("redaction", {}).get("status") == "success":
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                
                results["results"].append(result)
                
            except Exception as e:
                results["failed"] += 1
                results["results"].append({
                    "status": "error",
                    "file": report.get("file_path", "unknown"),
                    "error": str(e)
                })
        
        return results


def quick_redact(octopii_json: str, source_file: str, output_dir: str = "./outputs") -> str:
    """Quick redaction function for simple use cases"""
    from core.config import RedactionConfig
    
    config = RedactionConfig()
    config.set("output_base_dir", output_dir)
    
    engine = RedactionEngine(config)
    pipeline = RedactionPipeline(engine)
    
    result = pipeline.process_octopii_output(octopii_json, source_file)
    
    if result.get("redaction", {}).get("status") == "success":
        return result["redaction"]["output_path"]
    else:
        raise Exception(f"Redaction failed: {result.get('redaction', {}).get('error')}")
