# =============================================================================
# FILE: redactopii.py - FIXED VERSION
# DESCRIPTION: Fixed to return proper exit codes (0 for success, 1 for failure)
# =============================================================================

import argparse
import json
import sys
from pathlib import Path
from PIL import Image

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'core'))
sys.path.insert(0, str(Path(__file__).parent / 'integrations'))

try:
    from core.redaction_engine import RedactionEngine
    from core.config import RedactionConfig
    from integrations.pipeline_integration import RedactionPipeline
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the Redactopii directory")
    sys.exit(1)


def find_matching_report(reports, input_file):
    """Find the report entry that matches the input file"""
    input_path = Path(input_file).resolve()
    
    for report in reports:
        report_path_str = report.get("file_path", "")
        if not report_path_str:
            continue
            
        report_path = Path(report_path_str)
        
        # Try exact match
        try:
            if report_path.resolve() == input_path:
                return report
        except:
            pass
        
        # Try filename match
        if report_path.name == input_path.name:
            return report
        
        # Try case-insensitive match
        if report_path.name.lower() == input_path.name.lower():
            return report
        
        # Try stem match (without extension)
        if report_path.stem == input_path.stem:
            return report
    
    return None


def validate_input_file(input_path):
    """Validate input file exists and is readable"""
    if not input_path.exists():
        print(f"✗ Error: Input file not found: {input_path}", file=sys.stderr)
        return False
    
    # Check if it's an image and validate
    if input_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
        try:
            img = Image.open(input_path)
            img.verify()
            print(f"[INFO] Image validated: {img.format} {img.size}")
            return True
        except Exception as e:
            print(f"Error: Cannot open image: {e}", file=sys.stderr)
            return False
    
    # Check if it's a PDF
    elif input_path.suffix.lower() == '.pdf':
        try:
            with open(input_path, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    print(f" Error: File does not appear to be a valid PDF", file=sys.stderr)
                    return False
            print(f"[INFO] PDF file validated")
            return True
        except Exception as e:
            print(f"Error: Cannot read PDF: {e}", file=sys.stderr)
            return False
    
    # Text files
    elif input_path.suffix.lower() in ['.txt', '.csv', '.md', '.json']:
        try:
            input_path.read_text(encoding='utf-8')
            print(f"[INFO] Text file validated")
            return True
        except Exception as e:
            print(f"Error: Cannot read text file: {e}", file=sys.stderr)
            return False
    
    print(f"[WARN] Unknown file type: {input_path.suffix}")
    return True  # Allow unknown types to proceed


def main():
    parser = argparse.ArgumentParser(
        description='PII Redaction Engine - Automatically redacts PII from documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic redaction
  python redactopii.py --input document.txt --report output.json
  
  # Redact PDF with blur method
  python redactopii.py --input scan.pdf --report output.json --method blur
  
  # Redact image with blackbox method
  python redactopii.py --input photo.jpg --report output.json --method blackbox
  
  # Custom output directory
  python redactopii.py --input file.txt --report output.json --output-dir ./my_outputs
        """
    )

    parser.add_argument('--input', required=True, help='Input file path')
    parser.add_argument('--report', required=True, help='Octopii detection report (output.json)')
    parser.add_argument('--output-dir', default='./outputs', help='Output base directory (default: ./outputs)')
    parser.add_argument('--config', help='Configuration file path (optional)')
    parser.add_argument('--method', choices=['blur', 'blackbox', 'pixelate'], 
                        default='blur',
                        help='Redaction method for images/PDFs (default: blur)')
    parser.add_argument('--threshold', type=float, default=0.7,
                        help='Confidence threshold 0.0-1.0 (default: 0.7)')
    parser.add_argument('--verbose', action='store_true', 
                        help='Enable verbose output')

    args = parser.parse_args()

    # Print header
    print("=" * 70)
    print("PII REDACTION ENGINE")
    print("=" * 70)
    print(f"Input file:       {args.input}")
    print(f"Detection report: {args.report}")
    print(f"Output directory: {args.output_dir}")
    print(f"Method:           {args.method}")
    print(f"Threshold:        {args.threshold}")
    print()

    # Validate input file
    input_path = Path(args.input).resolve()
    if not validate_input_file(input_path):
        sys.exit(1)  # Explicit exit code

    # Validate report file
    report_path = Path(args.report)
    if not report_path.exists():
        print(f"Error: Report file not found: {report_path}", file=sys.stderr)
        sys.exit(1)  # Explicit exit code

    # Initialize engine
    try:
        config = RedactionConfig(args.config) if args.config else RedactionConfig()
        config.set("output_base_dir", args.output_dir)
        config.set("default_image_method", args.method)
        config.set("confidence_threshold", args.threshold)
        
        if args.verbose:
            config.set("log_level", "DEBUG")

        engine = RedactionEngine(config)
        pipeline = RedactionPipeline(engine)
        
        print("[INFO] Redaction engine initialized")
    except Exception as e:
        print(f"Error initializing engine: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)  # Explicit exit code

    try:
        # Load the report
        print(f"[INFO] Loading detection report...")
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        # Handle batch reports (array of reports)
        if isinstance(report_data, list):
            print(f"[INFO] Loaded batch report with {len(report_data)} entries")
            
            # Find matching report for this file
            matching_report = find_matching_report(report_data, str(input_path))
            
            if matching_report is None:
                print(f"No matching report found for: {input_path.name}", file=sys.stderr)
                print(f"\n[INFO] Available files in report:")
                for i, r in enumerate(report_data[:10], 1):  # Show first 10
                    print(f"  {i}. {r.get('file_path', 'unknown')}")
                if len(report_data) > 10:
                    print(f"  ... and {len(report_data) - 10} more")
                print(f"\n[HINT] Make sure the file path in the report matches your input file")
                sys.exit(1)  # Explicit exit code
            
            report = matching_report
            print(f"[INFO] Found matching report for: {report.get('file_path')}")
        else:
            report = report_data
            print(f"[INFO] Loaded single report")
        
        # Check for PII in report
        pii_count = 0
        pii_count += len(report.get("emails", []))
        pii_count += len(report.get("phone_numbers", []))
        pii_count += len(report.get("identifiers", []))
        pii_count += len(report.get("addresses", []))
        
        print(f"[INFO] Report contains {pii_count} PII entities")
        
        pii_locations = report.get("pii_with_locations", {})
        if not pii_locations:
            print("[WARN] No PII locations found in report")
            print("       This might mean:")
            print("       1. No PII was detected in the file")
            print("       2. Octopii couldn't determine precise locations")
            print("       3. The file is plain text (no bounding boxes needed)")
        else:
            print(f"[INFO] Found {len(pii_locations)} PII location(s) with coordinates")
            if args.verbose:
                for pii, loc in list(pii_locations.items())[:5]:
                    print(f"       - {pii[:40]}... at {loc}")
                if len(pii_locations) > 5:
                    print(f"       ... and {len(pii_locations) - 5} more")
        
        # Process the file
        print(f"\n[INFO] Starting redaction process...")
        result = engine.process_octopii_report(
            report=report,
            source_file=str(input_path)
        )
        
        # Display results
        redaction_status = result.get("redaction", {}).get("status")
        
        if redaction_status == "success":
            output_path = result["redaction"]["output_path"]
            redaction_count = result["redaction"].get("entities_redacted", 0)
            
            print(f"\n{'='*70}")
            print(f"SUCCESS")
            print(f"{'='*70}")
            print(f"Redacted file:     {output_path}")
            print(f"Entities redacted: {redaction_count}")
            
            # Show all output locations
            print(f"\n[INFO] Generated files:")
            print(f"   Redacted:    {output_path}")
            
            report_file = result.get("report")
            if report_file:
                print(f"   Report:      {report_file}")
            
            audit_dir = Path(args.output_dir) / "audit_logs"
            print(f"   Audit logs:  {audit_dir}/")
            
            print(f"\n[INFO] All outputs saved to: {args.output_dir}/")
            
            # CRITICAL: Return 0 for success
            sys.exit(0)
        
        elif redaction_status == "no_pii":
            print(f"\nℹ  No PII entities detected - nothing to redact")
            print(f"   Original file copied to: {result['redaction']['output_path']}")
            
            # Still a success - return 0
            sys.exit(0)
        
        elif redaction_status == "error":
            error_msg = result.get("redaction", {}).get("error", "Unknown error")
            print(f"\nREDACTION FAILED", file=sys.stderr)
            print(f"   Error: {error_msg}", file=sys.stderr)
            if args.verbose:
                print(f"\n   Full result: {json.dumps(result, indent=2)}", file=sys.stderr)
            sys.exit(1)  # Explicit exit code
        
        else:
            print(f"\n Unknown status: {redaction_status}", file=sys.stderr)
            if args.verbose:
                print(f"   Full result: {json.dumps(result, indent=2)}", file=sys.stderr)
            sys.exit(1)  # Explicit exit code

    except FileNotFoundError as e:
        print(f"\n✗ Error: File not found - {e}", file=sys.stderr)
        sys.exit(1)  # Explicit exit code
    except json.JSONDecodeError as e:
        print(f"\n Error: Invalid JSON in report file", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        print(f"\n[HINT] Make sure {args.report} is a valid JSON file", file=sys.stderr)
        sys.exit(1)  # Explicit exit code
    except KeyboardInterrupt:
        print(f"\n\n Interrupted by user", file=sys.stderr)
        sys.exit(1)  # Explicit exit code
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)  # Explicit exit code


if __name__ == '__main__':
    main()