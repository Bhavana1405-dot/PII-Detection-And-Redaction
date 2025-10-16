# =============================================================================
# FILE: Redactopii/redactopii.py
# DESCRIPTION: Redactopii - PII Redaction Engine CLI
# USAGE: python redactopii.py --input file.png --report output.json
# =============================================================================

"""
Redactopii - PII Redaction Engine CLI
Automatically saves redacted files to outputs/ directory
"""
import argparse
import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.redaction_engine import RedactionEngine
from core.config import RedactionConfig
from integrations.pipeline_integration import RedactionPipeline


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
    
    # Process file
    try:
        result = pipeline.process_octopii_output(args.report, args.input)
        
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        
        if result.get("redaction", {}).get("status") == "success":
            output_path = result["redaction"]["output_path"]
            print(f"✓ Redacted file saved: {output_path}")
            
            redaction_count = result["redaction"].get("entities_redacted", 0)
            print(f"✓ Redacted {redaction_count} PII entities")
            
            # Show output locations
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
            return 1
        
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