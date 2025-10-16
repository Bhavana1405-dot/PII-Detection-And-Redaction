# =============================================================================
# FILE: Redactopii/redactopii.py
# DESCRIPTION: Redactopii - PII Redaction Engine CLI with safe redaction
# USAGE: python redactopii.py --input file.png --report output.json
# =============================================================================

import argparse
import json
import sys
from pathlib import Path
from PIL import Image

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.redaction_engine import RedactionEngine
from core.config import RedactionConfig
from integrations.pipeline_integration import RedactionPipeline
from integrations.pipeline_integration import normalize_report_paths


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

    parser.add_argument('--input', required=True, help='Input file or directory path')
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
    print(f"Input path:       {args.input}")
    print(f"Detection report: {args.report}")
    print(f"Output directory: {args.output_dir}")
    if args.method:
        print(f"Method:           {args.method}")
    print()

    try:
        # Resolve paths
        input_path = Path(args.input).resolve()
        report_path = Path(args.report).resolve()

        # Normalize report paths
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)

            if isinstance(report_data, list):
                for entry in report_data:
                    file_path = Path(entry.get("file_path", ""))
                    if not file_path.is_absolute():
                        entry["file_path"] = str((input_path / file_path.name).resolve())

                # Save fixed version
                fixed_report_path = report_path.parent / "output_fixed.json"
                with open(fixed_report_path, "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=4)

                args.report = str(fixed_report_path)
                print(f"[INFO] Normalized file paths in report → {fixed_report_path}")
        except Exception as e:
            print(f"[WARN] Could not normalize report paths: {e}")

        # Determine files to process
        if input_path.is_file():
            files_to_process = [input_path]
        elif input_path.is_dir():
            files_to_process = [f for f in input_path.iterdir() if f.is_file()]
        else:
            print(f"✗ Invalid input path: {input_path}")
            return 1

        for file in files_to_process:
            print(f"\n[INFO] Processing: {file}")

            # Validate the image
            try:
                img = Image.open(file)
                img.verify()  # checks if the file is corrupted
            except Exception as e:
                print(f"✗ Cannot open image: {file} -> {e}")
                continue

            # Normalize report paths for this file
            args.report = normalize_report_paths(args.report, file)

            # Safe redaction
            try:
                result = pipeline.process_octopii_output(args.report, file)

                # Check PII coordinates within bounds
                if Path(file).suffix.lower() in ['.png', '.jpg', '.jpeg']:
                    img = Image.open(file)
                    width, height = img.size
                    for pii_entry in result.get("redaction", {}).get("pii_entries", []):
                        for loc in pii_entry.get("locations", []):
                            if loc["x"] + loc["width"] > width or loc["y"] + loc["height"] > height:
                                print(f"[WARN] Adjusting PII coordinates outside image bounds for {file}")
                                loc["x"] = min(loc["x"], width - 1)
                                loc["y"] = min(loc["y"], height - 1)

                # Display results
                if result.get("redaction", {}).get("status") == "success":
                    output_path = result["redaction"]["output_path"]
                    redaction_count = result["redaction"].get("entities_redacted", 0)
                    print(f"✓ Redacted file saved: {output_path}")
                    print(f"✓ Redacted {redaction_count} PII entities")

                    print(f"\nOutput locations:")
                    print(f"  - Redacted file: {output_path}")
                    if Path(output_path).suffix.lower() in ['.png', '.jpg', '.jpeg']:
                        comparison_dir = Path(args.output_dir) / "comparisons"
                        print(f"  - Comparison:    {comparison_dir}/")
                    audit_dir = Path(args.output_dir) / "audit_logs"
                    report_dir = Path(args.output_dir) / "reports"
                    print(f"  - Audit log:     {audit_dir}/")
                    print(f"  - Full report:   {report_dir}/")

                elif result.get("redaction", {}).get("status") == "no_pii":
                    print("ℹ No PII entities detected - nothing to redact")
                else:
                    print(f"✗ Redaction failed: {result.get('redaction', {}).get('error', 'Unknown error')}")

            except Exception as e:
                import traceback
                print(f"[ERROR] Pipeline failed for {file}: {e}")
                traceback.print_exc()
                continue

        print("=" * 70)
        return 0

    except FileNotFoundError as e:
        print(f"\n✗ Error: File not found - {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
