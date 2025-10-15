#!/usr/bin/env python3
"""
Full pipeline runner - Detection to Redaction
"""
import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Redactopii.core.redaction_engine import RedactionEngine
from Redactopii.core.config import RedactionConfig
from Redactopii.integrations.pipeline_integration import RedactionPipeline


def run_full_pipeline(source_file: str, detection_report: str, output_dir: str):
    """Run complete detection-to-redaction pipeline"""
    
    print("=" * 60)
    print("PII Detection & Redaction Pipeline")
    print("=" * 60)
    
    # Initialize
    config = RedactionConfig()
    engine = RedactionEngine(config)
    pipeline = RedactionPipeline(engine)
    
    print(f"\n1. Source File: {source_file}")
    print(f"2. Detection Report: {detection_report}")
    print(f"3. Output Directory: {output_dir}")
    
    # Process
    print("\n4. Processing...")
    result = pipeline.process_octopii_output(detection_report, source_file)
    
    # Save results
    output_path = Path(output_dir) / "redaction_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✓ Complete! Report saved to: {output_path}")
    print(f"  - Total entities: {result['summary']['total_entities']}")
    print(f"  - Redacted: {result['summary']['redacted_entities']}")
    print(f"  - Failed: {result['summary']['failed_redactions']}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(description='Full PII Pipeline')
    parser.add_argument('--source', required=True, help='Source file')
    parser.add_argument('--report', required=True, help='Detection report')
    parser.add_argument('--output', required=True, help='Output directory')
    
    args = parser.parse_args()
    
    return run_full_pipeline(args.source, args.report, args.output)


if __name__ == '__main__':
    sys.exit(main())