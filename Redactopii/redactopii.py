# =============================================================================
# FILE: Redactopii/redactopii.py
# DESCRIPTION: Fixed CLI that handles batch reports correctly
# =============================================================================

import argparse
import json
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

from core.redaction_engine import RedactionEngine
from core.config import RedactionConfig
from integrations.pipeline_integration import RedactionPipeline
# from core.redaction_engine import process_octopii_report as engine


def find_matching_report(reports, input_file):
    """Find the report entry that matches the input file"""
    input_path = Path(input_file).resolve()
    
    for report in reports:
        report_path = Path(report.get("file_path", ""))
        
        # Try exact match
        if report_path.resolve() == input_path:
            return report
        
        # Try filename match
        if report_path.name == input_path.name:
            return report
        
        # Try case-insensitive match
        if report_path.name.lower() == input_path.name.lower():
            return report
    
    return None


def main():
    parser = argparse.ArgumentParser(
        description='PII Redaction Engine - Automatically saves masked files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic redaction
  python redactopii.py --input document.txt --report output.json
  
  # With custom method
  python redactopii.py --input scan.png --report output.json --method blur
  
  # Custom output directory
  python redactopii.py --input file.txt --report output.json --output-dir ./my_outputs
        """
    )

    parser.add_argument('--input', required=True, help='Input file path')
    parser.add_argument('--report', required=True, help='Octopii detection report (output.json)')
    parser.add_argument('--output-dir', default='./outputs', help='Output base directory')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--method', choices=['blur', 'blackbox', 'pixelate'], 
                        help='Redaction method for images')
    parser.add_argument('--threshold', type=float, help='Confidence threshold (0.0-1.0)')

    args = parser.parse_args()

    # Initialize engine
    config = RedactionConfig(args.config) if args.config else RedactionConfig()
    config.set("output_base_dir", args.output_dir)
    
    if args.method:
        config.set("default_image_method", args.method)
    if args.threshold:
        config.set("confidence_threshold", args.threshold)

    engine = RedactionEngine(config)
    pipeline = RedactionPipeline(engine)

    print("=" * 70)
    print("PII REDACTION ENGINE")
    print("=" * 70)
    print(f"Input file:       {args.input}")
    print(f"Detection report: {args.report}")
    print(f"Output directory: {args.output_dir}")
    if args.method:
        print(f"Method:           {args.method}")
    print()

    try:
        # Load the report
        with open(args.report, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        # Handle batch reports (array of reports)
        if isinstance(report_data, list):
            print(f"[INFO] Loaded batch report with {len(report_data)} entries")
            
            # Find matching report for this file
            matching_report = find_matching_report(report_data, args.input)
            
            if matching_report is None:
                print(f"✗ No matching report found for: {args.input}")
                print(f"\nAvailable files in report:")
                for r in report_data[:5]:  # Show first 5
                    print(f"  - {r.get('file_path', 'unknown')}")
                if len(report_data) > 5:
                    print(f"  ... and {len(report_data) - 5} more")
                return 1
            
            report = matching_report
            print(f"[INFO] Found matching report for: {report['file_path']}")
        else:
            report = report_data
        
        # Validate input file exists
        input_path = Path(args.input).resolve()
        if not input_path.exists():
            print(f"✗ Input file not found: {input_path}")
            return 1
        
        # Check if it's an image and validate
        if input_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
            try:
                img = Image.open(input_path)
                img.verify()
                print(f"[INFO] Image validated: {img.format} {img.size}")
            except Exception as e:
                print(f"✗ Cannot open image: {e}")
                return 1
        
        # Check for PII locations
        pii_locations = report.get("pii_with_locations", {})
        if not pii_locations:
            print("[WARN] No PII locations found in report")
            print("       This might mean:")
            print("       1. No PII was detected in the file")
            print("       2. Octopii couldn't determine precise locations")
            print("       3. The file format doesn't support location mapping")
        else:
            print(f"[INFO] Found {len(pii_locations)} PII location(s) to redact:")
            for pii, loc in pii_locations.items():
                print(f"       - {pii[:50]}... at {loc}")
        
        # Process the file
        print(f"\n[INFO] Processing redaction...")
        result = engine.process_octopii_report(
            report=report,
            source_file=str(input_path)
        )
        
        # Check if it's a batch result
        if result.get("status") == "batch_complete":
            print(f"✗ Unexpected batch result. Use single file mode.")
            return 1
        
        # Display results
        redaction_status = result.get("redaction", {}).get("status")
        
        if redaction_status == "success":
            output_path = result["redaction"]["output_path"]
            redaction_count = result["redaction"].get("entities_redacted", 0)
            
            print(f"\n{'='*70}")
            print(f"✓ SUCCESS")
            print(f"{'='*70}")
            print(f"Redacted file:    {output_path}")
            print(f"Entities redacted: {redaction_count}")
            
            # Show all output locations
            print(f"\nGenerated files:")
            print(f"  📄 Redacted:    {output_path}")
            
            report_path = result.get("report")
            if report_path:
                print(f"  📊 Report:      {report_path}")
            
            audit_dir = Path(args.output_dir) / "audit_logs"
            print(f"  📝 Audit logs:  {audit_dir}/")
            
            if input_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                comparison_dir = Path(args.output_dir) / "comparisons"
                print(f"  🔍 Comparisons: {comparison_dir}/")
        
        elif redaction_status == "no_pii":
            print(f"\nℹ️  No PII entities detected - nothing to redact")
            print(f"   Original file copied to: {result['redaction']['output_path']}")
        
        elif redaction_status == "error":
            error_msg = result.get("redaction", {}).get("error", "Unknown error")
            print(f"\n✗ REDACTION FAILED")
            print(f"   Error: {error_msg}")
            return 1
        
        else:
            print(f"\n✗ Unknown status: {redaction_status}")
            print(f"   Full result: {json.dumps(result, indent=2)}")
            return 1
        
        print(f"\n{'='*70}")
        return 0

    except FileNotFoundError as e:
        print(f"\n✗ Error: File not found - {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"\n✗ Error: Invalid JSON in report file - {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())