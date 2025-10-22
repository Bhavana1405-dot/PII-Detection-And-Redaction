#!/usr/bin/env python3
"""
Quick fix for detection - Test if Aadhaar/PAN are being detected
"""
import sys
sys.path.insert(0, 'Octopii')

import text_utils
import re

# Test text from your PDF
test_text = """
Aadhaar (synthetic): 9999 0000 1111
PAN (synthetic): AAAAP1234Q
Phone: +91-98234-56789
Email: aarti.kumari.synthetic@example.com
"""

print("Testing PII Detection...")
print("=" * 70)

rules = text_utils.get_regexes()

# Test Aadhaar
print("\n1. Testing Aadhaar detection:")
aadhaar_regex = rules["Aadhaar Card"]["regex"]
print(f"   Regex: {aadhaar_regex}")
matches = [m.group(0) for m in re.finditer(aadhaar_regex, test_text)]
print(f"   Found: {matches}")

if "9999 0000 1111" in matches:
    print("   ✓ PASS: Aadhaar detected correctly")
else:
    print("   ✗ FAIL: Aadhaar NOT detected!")
    print("   → Update definitions.json with: \\b\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}\\b")

# Test PAN
print("\n2. Testing PAN detection:")
pan_regex = rules["Permanent Account Number"]["regex"]
print(f"   Regex: {pan_regex}")
matches = [m.group(0) for m in re.finditer(pan_regex, test_text)]
print(f"   Found: {matches}")

if "AAAAP1234Q" in matches:
    print("   ✓ PASS: PAN detected correctly")
else:
    print("   ✗ FAIL: PAN NOT detected!")
    print("   → Update definitions.json with: \\b[A-Z]{5}\\d{4}[A-Z]\\b")

# Test with text_utils function
print("\n3. Testing id_card_numbers_pii function:")
identifiers = text_utils.id_card_numbers_pii(test_text, rules)
print(f"   Found {len(identifiers)} identifier types")
for id_result in identifiers:
    print(f"   - {id_result['identifier_class']}: {id_result['result']}")

print("\n" + "=" * 70)