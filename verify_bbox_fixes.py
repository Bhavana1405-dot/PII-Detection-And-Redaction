#!/usr/bin/env python3
"""
Verify Bounding Box Fixes
This script checks if bounding boxes are now precise after applying fixes

Usage:
    # After running detection with fixed code:
    python verify_bbox_fixes.py output.json
"""

import sys
import json
from pathlib import Path


def estimate_expected_bbox_area(pii_value):
    """Estimate expected bounding box area for a PII value"""
    # Remove separators to get actual character count
    clean_value = pii_value.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')
    char_count = len(clean_value)
    
    # Typical OCR metrics:
    # - Character width: 12-20 pixels (average 15)
    # - Line height: 25-35 pixels (average 30)
    avg_char_width = 15
    avg_line_height = 30
    
    # Expected dimensions
    expected_width = char_count * avg_char_width
    expected_height = avg_line_height
    expected_area = expected_width * expected_height
    
    return {
        "expected_width": expected_width,
        "expected_height": expected_height,
        "expected_area": expected_area,
        "char_count": char_count
    }


def check_bbox_quality(report_path):
    """Analyze bounding box quality in detection report"""
    
    print("=" * 80)
    print("BOUNDING BOX QUALITY ANALYSIS")
    print("=" * 80)
    
    with open(report_path, 'r') as f:
        data = json.load(f)
    
    # Handle batch reports
    if isinstance(data, list):
        print(f"\n[INFO] Batch report with {len(data)} files")
        print("[INFO] Analyzing first file\n")
        report = data[0]
    else:
        report = data
    
    pii_locations = report.get("pii_with_locations", {})
    
    if not pii_locations:
        print("\n❌ NO PII LOCATIONS FOUND")
        print("   The detection phase didn't generate bounding boxes")
        print("\n   Actions:")
        print("   1. Update Octopii/octopii.py with the fixed search_pii function")
        print("   2. Re-run detection: python Octopii/octopii.py <file>")
        return 1
    
    print(f"\nAnalyzing {len(pii_locations)} PII bounding boxes...\n")
    
    # Categorize results
    precise_boxes = []
    acceptable_boxes = []
    oversized_boxes = []
    undersized_boxes = []
    
    print("=" * 80)
    print(f"{'PII Value':<45} {'Size':<15} {'Status':<15}")
    print("=" * 80)
    
    for pii_value, location in pii_locations.items():
        x = location.get("x", 0)
        y = location.get("y", 0)
        w = location.get("width", 0)
        h = location.get("height", 0)
        
        actual_area = w * h
        
        # Get expected dimensions
        expected = estimate_expected_bbox_area(pii_value)
        expected_area = expected["expected_area"]
        
        # Calculate ratio
        if expected_area > 0:
            size_ratio = actual_area / expected_area
        else:
            size_ratio = 0
        
        # Classify
        if 0.5 <= size_ratio <= 2.0:
            status = "✓ PRECISE"
            precise_boxes.append(pii_value)
        elif 2.0 < size_ratio <= 4.0:
            status = "~ ACCEPTABLE"
            acceptable_boxes.append(pii_value)
        elif size_ratio > 4.0:
            status = "✗ TOO LARGE"
            oversized_boxes.append((pii_value, size_ratio))
        else:
            status = "✗ TOO SMALL"
            undersized_boxes.append(pii_value)
        
        # Display
        pii_display = pii_value[:42] + "..." if len(pii_value) > 42 else pii_value
        size_display = f"{w}×{h}"
        
        print(f"{pii_display:<45} {size_display:<15} {status:<15}")
        
        # Show details for problematic boxes
        if size_ratio > 4.0 or size_ratio < 0.5:
            print(f"  Expected: ~{expected['expected_width']}×{expected['expected_height']} "
                  f"(ratio: {size_ratio:.1f}x)")
            print(f"  Actual area: {actual_area}px², Expected: ~{expected_area}px²")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total = len(pii_locations)
    precise_pct = (len(precise_boxes) / total * 100) if total > 0 else 0
    acceptable_pct = (len(acceptable_boxes) / total * 100) if total > 0 else 0
    
    print(f"\nTotal PII with locations: {total}")
    print(f"   Precise (0.5-2x):     {len(precise_boxes)} ({precise_pct:.1f}%)")
    print(f"   Acceptable (2-4x):    {len(acceptable_boxes)} ({acceptable_pct:.1f}%)")
    print(f"   Oversized (>4x):      {len(oversized_boxes)}")
    print(f"   Undersized (<0.5x):   {len(undersized_boxes)}")
    
    # Quality assessment
    print("\n" + "=" * 80)
    print("QUALITY ASSESSMENT")
    print("=" * 80)
    
    if len(oversized_boxes) == 0 and len(undersized_boxes) == 0:
        print("\nEXCELLENT! All bounding boxes are precise or acceptable.")
        print("\n   Your fixes are working correctly!")
        print("\n   Next steps:")
        print("   1. Run redaction: python Redactopii/redactopii.py --input <file> --report output.json")
        print("   2. Check that only PII is redacted, not surrounding text")
        return 0
    
    elif len(oversized_boxes) <= total * 0.2:  # Less than 20% oversized
        print("\n✓ GOOD! Most bounding boxes are precise.")
        print(f"\n   {len(oversized_boxes)} boxes are still oversized:")
        
        for pii, ratio in oversized_boxes[:5]:
            print(f"   - {pii[:50]}... ({ratio:.1f}x too large)")
        
        if len(oversized_boxes) > 5:
            print(f"   ... and {len(oversized_boxes) - 5} more")
        
        print("\n   Recommendations:")
        print("   1. These might be complex PIIs split across many tokens")
        print("   2. Consider adjusting max_tokens_in_pii in find_precise_bbox_for_pii()")
        print("   3. Or accept minor over-redaction for these edge cases")
        return 0
    
    else:
        print("\n⚠ NEEDS IMPROVEMENT!")
        print(f"\n   {len(oversized_boxes)} bounding boxes are too large:")
        
        # Show worst offenders
        oversized_sorted = sorted(oversized_boxes, key=lambda x: x[1], reverse=True)
        for pii, ratio in oversized_sorted[:10]:
            print(f"   - {pii[:50]}... ({ratio:.1f}x too large)")
        
        if len(oversized_boxes) > 10:
            print(f"   ... and {len(oversized_boxes) - 10} more")
        
        print("\n   ACTIONS REQUIRED:")
        print("   1. Verify you've updated octopii.py with the fixed search_pii function")
        print("   2. Check that find_precise_bbox_for_pii() is using STRICT window limits")
        print("   3. Re-run detection: rm output.json && python Octopii/octopii.py <file>")
        print("   4. Run this script again to verify improvements")
        return 1


def compare_reports(old_report_path, new_report_path):
    """Compare old vs new bounding boxes to show improvements"""
    
    print("\n" + "=" * 80)
    print("BEFORE vs AFTER COMPARISON")
    print("=" * 80)
    
    with open(old_report_path, 'r') as f:
        old_data = json.load(f)
    with open(new_report_path, 'r') as f:
        new_data = json.load(f)
    
    if isinstance(old_data, list):
        old_report = old_data[0]
    else:
        old_report = old_data
    
    if isinstance(new_data, list):
        new_report = new_data[0]
    else:
        new_report = new_data
    
    old_locations = old_report.get("pii_with_locations", {})
    new_locations = new_report.get("pii_with_locations", {})
    
    print(f"\nComparing {len(old_locations)} PII from old vs {len(new_locations)} from new\n")
    
    improvements = 0
    degradations = 0
    
    for pii in old_locations:
        if pii not in new_locations:
            continue
        
        old_loc = old_locations[pii]
        new_loc = new_locations[pii]
        
        old_area = old_loc.get("width", 0) * old_loc.get("height", 0)
        new_area = new_loc.get("width", 0) * new_loc.get("height", 0)
        
        expected = estimate_expected_bbox_area(pii)
        expected_area = expected["expected_area"]
        
        old_ratio = old_area / expected_area if expected_area > 0 else 0
        new_ratio = new_area / expected_area if expected_area > 0 else 0
        
        change = ((new_area - old_area) / old_area * 100) if old_area > 0 else 0
        
        if abs(change) > 10:  # More than 10% change
            pii_display = pii[:50] + "..." if len(pii) > 50 else pii
            
            if new_ratio < old_ratio and new_ratio <= 2.0:
                print(f"✓ {pii_display}")
                print(f"  Old: {old_loc['width']}×{old_loc['height']} ({old_ratio:.1f}x)")
                print(f"  New: {new_loc['width']}×{new_loc['height']} ({new_ratio:.1f}x)")
                print(f"  → {abs(change):.1f}% smaller (IMPROVED!)")
                improvements += 1
            elif new_ratio > old_ratio:
                print(f"✗ {pii_display}")
                print(f"  Old: {old_loc['width']}×{old_loc['height']} ({old_ratio:.1f}x)")
                print(f"  New: {new_loc['width']}×{new_loc['height']} ({new_ratio:.1f}x)")
                print(f"  → {change:.1f}% larger (WORSE!)")
                degradations += 1
    
    print(f"\n{'='*80}")
    print(f"Improvements: {improvements}")
    print(f"Degradations: {degradations}")
    
    if improvements > degradations:
        print("\n✓ Overall: Bounding boxes are MORE PRECISE after fixes")
    elif degradations > improvements:
        print("\n✗ Overall: Bounding boxes got WORSE - check your changes")
    else:
        print("\n~ Overall: Mixed results - some improved, some got worse")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python verify_bbox_fixes.py output.json")
        print("  python verify_bbox_fixes.py old_output.json new_output.json  # Compare")
        sys.exit(1)
    
    report_path = sys.argv[1]
    
    if not Path(report_path).exists():
        print(f"Error: File not found: {report_path}")
        sys.exit(1)
    
    try:
        if len(sys.argv) == 3:
            # Comparison mode
            old_report = sys.argv[1]
            new_report = sys.argv[2]
            
            if not Path(new_report).exists():
                print(f"Error: File not found: {new_report}")
                sys.exit(1)
            
            compare_reports(old_report, new_report)
        else:
            # Analysis mode
            exit_code = check_bbox_quality(report_path)
            sys.exit(exit_code)
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()