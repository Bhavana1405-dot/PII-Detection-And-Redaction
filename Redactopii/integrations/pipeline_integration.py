# =============================================================================
# FILE: Redactopii/integrations/pipeline_integration.py
# DESCRIPTION: Complete end-to-end pipeline for real Octopii integration
# =============================================================================

"""
End-to-end pipeline integration for Octopii detection + Redaction
Handles the actual Octopii output format and produces redacted files
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..core.redaction_engine import RedactionEngine
from .octopii_adapter import OctopiiAdapter


class RedactionPipeline:
    """
    Full detection-to-redaction pipeline
    
    Workflow:
    1. Read Octopii output.json
    2. Parse PII entities using OctopiiAdapter
    3. Load source file
    4. Apply redaction
    5. Save redacted file to outputs/
    6. Generate comprehensive report
    """
    
    def __init__(self, engine: RedactionEngine):
        self.engine = engine
        self.adapter = OctopiiAdapter()
        self.processed_files = []
    
    def process_octopii_output(self, report_path: str, source_file: Optional[str] = None) -> Dict:
        """
        Process Octopii detection output and save redacted files
        
        Args:
            report_path: Path to Octopii output.json
            source_file: Optional override for source file path
                        (if None, uses file_path from report)
        
        Returns:
            Comprehensive report with all results
        """
        # Load Octopii report
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Handle both single report and array of reports
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
        
        # Try enhanced parsing with source text for text files
        entities = self._parse_with_enhancement(report, source_file)
        
        # Process file through redaction engine
        result = self.engine.process_octopii_report(report, source_file)
        
        # Track processed file
        self.processed_files.append({
            "source": source_file,
            "output": result.get("redaction", {}).get("output_path"),
            "timestamp": datetime.now().isoformat()
        })
        
        return result
    
    def _parse_with_enhancement(self, report: Dict, source_file: str) -> List:
        """
        Parse report with position enhancement for text files
        """
        file_ext = Path(source_file).suffix.lower()
        
        # For text files, try to get positions
        if file_ext in ['.txt', '.csv', '.json', '.log']:
            try:
                with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                    source_text = f.read()
                
                # Use enhanced parsing
                return self.adapter.enrich_with_positions(report, source_text)
            except Exception as e:
                self.engine.logger.warning(f"Could not read source text: {e}")
        
        # For other files, use basic parsing
        return self.adapter.parse_report(report)
    
    def process_batch_reports(self, reports: List[Dict]) -> Dict:
        """
        Process multiple Octopii reports in batch
        
        Args:
            reports: List of Octopii report dictionaries
            
        Returns:
            Batch processing results
        """
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
                result = self.process_octopii_output(
                    report_path=None,  # Already loaded
                    source_file=report.get("file_path")
                )
                
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
    
    def process_octopii_directory(self, octopii_output_dir: str) -> Dict:
        """
        Process all reports in Octopii output directory
        
        Args:
            octopii_output_dir: Directory containing output.json files
            
        Returns:
            Combined results for all files
        """
        output_dir = Path(octopii_output_dir)
        
        # Find all output.json files
        report_files = list(output_dir.glob("**/output.json"))
        
        if not report_files:
            return {
                "status": "error",
                "error": f"No output.json files found in {octopii_output_dir}"
            }
        
        all_results = []
        
        for report_file in report_files:
            try:
                result = self.process_octopii_output(str(report_file))
                all_results.append(result)
            except Exception as e:
                self.engine.logger.error(f"Failed to process {report_file}: {e}")
        
        return {
            "status": "directory_complete",
            "timestamp": datetime.now().isoformat(),
            "processed": len(all_results),
            "results": all_results
        }
    
    def generate_summary_report(self) -> Dict:
        """
        Generate summary of all processed files
        
        Returns:
            Summary statistics and file list
        """
        total_files = len(self.processed_files)
        
        if total_files == 0:
            return {
                "status": "no_files_processed",
                "message": "No files have been processed yet"
            }
        
        return {
            "summary": {
                "total_processed": total_files,
                "timestamp": datetime.now().isoformat(),
                "output_directory": str(self.engine.output_dirs["redacted"])
            },
            "files": self.processed_files
        }
    
    def save_batch_report(self, output_path: Optional[str] = None) -> str:
        """
        Save batch processing report to file
        
        Args:
            output_path: Optional custom output path
            
        Returns:
            Path where report was saved
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.engine.output_dirs["reports"] / f"batch_report_{timestamp}.json"
        
        report = self.generate_summary_report()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.engine.logger.info(f"✓ Batch report saved: {output_path}")
        
        return str(output_path)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def quick_redact(octopii_json: str, source_file: str, output_dir: str = "./outputs") -> str:
    """
    Quick redaction function for simple use cases
    
    Args:
        octopii_json: Path to Octopii output.json
        source_file: Path to source file to redact
        output_dir: Output directory for redacted files
        
    Returns:
        Path to redacted file
    """
    from ..core.config import RedactionConfig
    
    # Setup
    config = RedactionConfig()
    config.set("output_base_dir", output_dir)
    
    engine = RedactionEngine(config)
    pipeline = RedactionPipeline(engine)
    
    # Process
    result = pipeline.process_octopii_output(octopii_json, source_file)
    
    # Return path
    if result.get("redaction", {}).get("status") == "success":
        return result["redaction"]["output_path"]
    else:
        raise Exception(f"Redaction failed: {result.get('redaction', {}).get('error')}")


def batch_redact_from_octopii(octopii_output_file: str, output_dir: str = "./outputs") -> Dict:
    """
    Batch redact all files detected by Octopii
    
    Args:
        octopii_output_file: Path to Octopii output.json with multiple reports
        output_dir: Output directory for redacted files
        
    Returns:
        Batch processing results
    """
    from ..core.config import RedactionConfig
    
    # Setup
    config = RedactionConfig()
    config.set("output_base_dir", output_dir)
    
    engine = RedactionEngine(config)
    pipeline = RedactionPipeline(engine)
    
    # Load and process
    with open(octopii_output_file, 'r') as f:
        reports = json.load(f)
    
    # Handle single report or array
    if isinstance(reports, dict):
        reports = [reports]
    
    return pipeline.process_batch_reports(reports)


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("REDACTION PIPELINE - Usage Examples")
    print("=" * 70)
    
    # Example 1: Simple single file redaction
    print("\nExample 1: Single File Redaction")
    print("-" * 70)
    print("""
from Redactopii.integrations.pipeline_integration import quick_redact

# Quick redaction
redacted_path = quick_redact(
    octopii_json="output.json",
    source_file="customer_data.txt",
    output_dir="./my_outputs"
)

print(f"Redacted file saved to: {redacted_path}")
    """)
    
    # Example 2: Full pipeline with custom config
    print("\nExample 2: Custom Configuration")
    print("-" * 70)
    print("""
from Redactopii.core.redaction_engine import RedactionEngine
from Redactopii.core.config import RedactionConfig
from Redactopii.integrations.pipeline_integration import RedactionPipeline

# Custom configuration
config = RedactionConfig()
config.set("default_image_method", "pixelate")
config.set("confidence_threshold", 0.85)
config.set("save_comparison", True)

# Initialize
engine = RedactionEngine(config)
pipeline = RedactionPipeline(engine)

# Process
result = pipeline.process_octopii_output(
    report_path="output.json",
    source_file="scan.png"
)

print(f"Status: {result['redaction']['status']}")
print(f"Output: {result['redaction']['output_path']}")
    """)
    
    # Example 3: Batch processing
    print("\nExample 3: Batch Processing")
    print("-" * 70)
    print("""
from Redactopii.integrations.pipeline_integration import batch_redact_from_octopii

# Process all files from Octopii scan
results = batch_redact_from_octopii(
    octopii_output_file="output.json",
    output_dir="./batch_outputs"
)

print(f"Processed: {results['total_files']}")
print(f"Successful: {results['successful']}")
print(f"Failed: {results['failed']}")
    """)
    
    # Example 4: Directory scanning
    print("\nExample 4: Process Octopii Directory")
    print("-" * 70)
    print("""
from Redactopii.core.redaction_engine import RedactionEngine
from Redactopii.core.config import RedactionConfig
from Redactopii.integrations.pipeline_integration import RedactionPipeline

engine = RedactionEngine(RedactionConfig())
pipeline = RedactionPipeline(engine)

# Process entire directory of Octopii outputs
results = pipeline.process_octopii_directory("./octopii_scans/")

# Save summary
report_path = pipeline.save_batch_report()
print(f"Report saved to: {report_path}")
    """)
    
    print("\n" + "=" * 70)
    print("Pipeline ready for production use!")
    print("=" * 70)