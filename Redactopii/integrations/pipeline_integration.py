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


# -----------------------------
# Utility: Normalize report paths
# -----------------------------
def normalize_report_paths(report_path: str, input_path: str) -> str:
    """
    Normalize the file_path entries in Octopii report so they point to actual local files.
    - report_path: path to output.json
    - input_path: the input file or folder used for redaction
    Returns: path to fixed report JSON
    """
    report_path = Path(report_path).resolve()
    input_path = Path(input_path).resolve()

    # Determine base folder for source images
    if input_path.is_file():
        base_folder = input_path.parent
    else:
        base_folder = input_path

    # Load the report
    with open(report_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)

    # Normalize paths
    if isinstance(report_data, list):
        for entry in report_data:
            file_path = entry.get("file_path", "")
            # Remove leading 'Octopii/' or duplicate 'dummy-pii/' prefixes
            file_path = file_path.replace("Octopii/", "").lstrip("\\/")  # remove leading slash/backslash
            file_path_parts = Path(file_path).parts
            # If first part is same as base folder name, skip it
            if file_path_parts and file_path_parts[0] == base_folder.name:
                file_path = Path(*file_path_parts[1:])
            # Build absolute path
            entry["file_path"] = str((base_folder / file_path).resolve())

    # Save fixed report
    fixed_report_path = report_path.parent / "output_fixed.json"
    with open(fixed_report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=4)

    return str(fixed_report_path)


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
            source_file = report.get("file_path")  # Get the source file path
            try:
                # Check for missing path
                if not source_file:
                    raise ValueError("A report in the batch is missing the 'file_path' key.")
                
                # Check if file exists
                if not Path(source_file).exists():
                    raise FileNotFoundError(f"Source file specified in report not found: {source_file}")

                # Call the engine directly instead of the flawed recursive call
                result = self.engine.process_octopii_report(report, source_file)
                
                if result.get("redaction", {}).get("status") == "success":
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                
                results["results"].append(result)
                
            except Exception as e:
                results["failed"] += 1
                results["results"].append({
                    "status": "error",
                    "file": source_file or "unknown",
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