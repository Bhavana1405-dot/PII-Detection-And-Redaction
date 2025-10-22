#!/usr/bin/env python3
"""
Check detection quality and bounding box sizes
This will show if bounding boxes are too large

Usage:
    python check_detection.py output.json
"""

import sys
import json
from pathlib import Path


def check_detection_quality(report_path):
    """Check if bounding boxes are reasonable"""
    
    print("=" * 70)
    print("DETECTION QUALITY CHECK")
    print("=" * 70)
    
    with open(report_path, 'r') as f:
        data = json.load(f)
    
    # Handle batch
    if isinstance(data, list):
        report = data[0]
    else:
        report = data
    
    pii_locations = report.get("pii_with_locations", {})
    
    if not pii_locations:
        print("\n❌ NO PII LOCATIONS FOUND!")
        print("   Redaction will not work.")
        print("\n   Action: Fix detection first")
        print("   Run: python Octopii/octopii.py <file>")
        return
    
    print(f"\nFound {len(pii_locations)} PII with locations")
    print()
    
    # Check each bounding box
    print("=" * 70)
    print("BOUNDING BOX ANALYSIS")
    print("=" * 70)
    
    issues = []
    
    for pii_value, location in pii_locations.items():
        x = location.get("x", 0)
        y = location.get("y", 0)
        w = location.get("width", 0)
        h = location.get("height", 0)
        
        area = w * h
        
        # Estimate expected size based on PII type
        pii_len = len(pii_value)
        
        # Rough estimate: ~15 pixels per character width, ~25 pixels height
        expected_w = pii_len * 15
        expected_h = 25
        expected_area = expected_w * expected_h
        
        # Check if box is too large
        if area > expected_area * 3:  # More than 3x expected
            status = "⚠️  TOO LARGE"
            issues.append(pii_value)
        elif area < expected_area * 0.3:  # Less than 30% expected
            status = "⚠️  TOO SMALL"
            issues.append(pii_value)
        else:
            status = "✓ OK"
        
        print(f"\nPII: {pii_value}")
        print(f"  Location: x={x}, y={y}, w={w}, h={h}")
        print(f"  Area: {area} px² (expected ~{expected_area} px²)")
        print(f"  Status: {status}")
        
        if status != "✓ OK":
            ratio = area / expected_area if expected_area > 0 else 0
            print(f"  Warning: Box is {ratio:.1f}x expected size!")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} bounding box issues")
        print("\nProblematic PIIs:")
        for pii in issues:
            print(f"  - {pii[:50]}...")
        
        print("\n🔧 FIXES:")
        print("\n1. The bounding boxes are too large/imprecise")
        print("   This causes over-redaction (redacting nearby text)")
        print()
        print("2. Update Octopii/octopii.py:")
        print("   - Use the improved find_bbox_for_pii function")
        print("   - It calculates tighter boxes around PII only")
        print()
        print("3. Update Redactopii/core/redaction_engine.py:")
        print("   - Use _calculate_precise_bbox with minimal padding")
        print("   - Add only 5px padding instead of using full OCR boxes")
        print()
        print("4. Re-run detection:")
        print("   rm output.json")
        print("   python Octopii/octopii.py <file>")
        print()
        print("5. Re-run redaction:")
        print("   python Redactopii/redactopii.py --input <file> --report output.json")
        
    else:
        print("\n✓ All bounding boxes look reasonable")
        print("  If redaction still over-redacts:")
        print("  1. Update redaction_engine.py with precise bbox calculation")
        print("  2. Reduce padding from default to 5 pixels")
    
    print("\n" + "=" * 70)


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_detection.py output.json")
        sys.exit(1)
    
    report_path = sys.argv[1]
    
    if not Path(report_path).exists():
        print(f"Error: File not found: {report_path}")
        sys.exit(1)
    
    try:
        check_detection_quality(report_path)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()