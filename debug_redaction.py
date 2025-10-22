#!/usr/bin/env python3
"""
Debug script to diagnose redaction issues
This will show you exactly what's being detected and where

Usage:
    python debug_redaction.py output.json
"""

import sys
import json
from pathlib import Path

def analyze_detection_report(report_path):
    """Analyze the detection report and show what's detected"""
    
    print("=" * 70)
    print("REDACTION DEBUG ANALYSIS")
    print("=" * 70)
    
    with open(report_path, 'r') as f:
        data = json.load(f)
    
    # Handle both single report and batch
    if isinstance(data, list):
        print(f"\n[INFO] Batch report with {len(data)} files")
        print("[INFO] Analyzing first file only\n")
        report = data[0]
    else:
        report = data
    
    # Show file info
    print(f"File: {report.get('file_path', 'unknown')}")
    print(f"PII Class: {report.get('pii_class', 'none')}")
    print(f"Score: {report.get('score', 0)}")
    print()
    
    # Count PII
    identifiers = report.get("identifiers", [])
    emails = report.get("emails", [])
    phones = report.get("phone_numbers", [])
    addresses = report.get("addresses", [])
    pii_locations = report.get("pii_with_locations", {})
    
    total_detected = len(identifiers) + len(emails) + len(phones) + len(addresses)
    total_with_locations = len(pii_locations)
    
    print("=" * 70)
    print("DETECTION SUMMARY")
    print("=" * 70)
    print(f"Total PII Detected: {total_detected}")
    print(f"  - Identifiers: {len(identifiers)}")
    print(f"  - Emails: {len(emails)}")
    print(f"  - Phones: {len(phones)}")
    print(f"  - Addresses: {len(addresses)}")
    print()
    print(f"Total with Locations: {total_with_locations}")
    print()
    
    # Show detected identifiers
    if identifiers:
        print("=" * 70)
        print("DETECTED IDENTIFIERS (Aadhaar, PAN, etc.)")
        print("=" * 70)
        for i, identifier in enumerate(identifiers, 1):
            in_locations = identifier in pii_locations
            status = "✓ HAS LOCATION" if in_locations else "✗ NO LOCATION"
            print(f"{i}. {identifier:<30} {status}")
            
            if in_locations:
                loc = pii_locations[identifier]
                print(f"   Location: {loc}")
        print()
    
    # Show emails
    if emails:
        print("=" * 70)
        print("DETECTED EMAILS")
        print("=" * 70)
        for i, email in enumerate(emails, 1):
            in_locations = email in pii_locations
            status = "✓ HAS LOCATION" if in_locations else "✗ NO LOCATION"
            print(f"{i}. {email:<40} {status}")
        print()
    
    # Show phones
    if phones:
        print("=" * 70)
        print("DETECTED PHONE NUMBERS")
        print("=" * 70)
        for i, phone in enumerate(phones, 1):
            in_locations = phone in pii_locations
            status = "✓ HAS LOCATION" if in_locations else "✗ NO LOCATION"
            print(f"{i}. {phone:<25} {status}")
        print()
    
    # Show what's in pii_with_locations
    print("=" * 70)
    print("PII WITH LOCATIONS (What will be redacted)")
    print("=" * 70)
    
    if not pii_locations:
        print("❌ NO PII LOCATIONS FOUND!")
        print()
        print("This is why nothing is being redacted!")
        print()
        print("Common causes:")
        print("1. OCR couldn't read the text clearly")
        print("2. PII values don't match OCR output exactly")
        print("3. Bounding box detection failed")
        print()
        print("Solutions:")
        print("1. Update octopii.py with the fixed search_pii function")
        print("2. Re-run detection: python Octopii/octopii.py <file>")
        print("3. Check OCR quality (image resolution, clarity)")
    else:
        for pii_value, location in pii_locations.items():
            print(f"PII: {pii_value}")
            print(f"  Location: {location}")
            print()
    
    # Analysis
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    missing_locations = total_detected - total_with_locations
    
    if missing_locations == 0:
        print("✓ All detected PII have locations")
        print("✓ Redaction should work correctly")
    else:
        print(f"⚠ {missing_locations} PII values are missing locations")
        print(f"⚠ These will NOT be redacted")
        print()
        
        # Find which ones are missing
        missing = []
        for pii in identifiers + emails + phones + addresses:
            if pii not in pii_locations:
                missing.append(pii)
        
        print("Missing locations for:")
        for pii in missing[:10]:  # Show first 10
            print(f"  - {pii}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")
        
        print()
        print("ACTION REQUIRED:")
        print("1. Replace search_pii function in Octopii/octopii.py")
        print("2. Re-run detection to get locations for all PII")
        print("3. Then run redaction again")
    
    print()
    print("=" * 70)


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_redaction.py output.json")
        sys.exit(1)
    
    report_path = sys.argv[1]
    
    if not Path(report_path).exists():
        print(f"Error: File not found: {report_path}")
        sys.exit(1)
    
    try:
        analyze_detection_report(report_path)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()