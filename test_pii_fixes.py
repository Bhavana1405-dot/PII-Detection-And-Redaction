#!/usr/bin/env python3
"""
Complete Test Suite for PII Detection and Redaction Fixes
Run this to verify all fixes are working correctly

Usage:
    python test_pii_fixes.py
    
    # Or with verbose output:
    python test_pii_fixes.py --verbose
"""

import sys
import os
from pathlib import Path
import argparse

# Add Octopii to path
SCRIPT_DIR = Path(__file__).parent.resolve()
OCTOPII_DIR = SCRIPT_DIR / 'Octopii'

if not OCTOPII_DIR.exists():
    print(f"Error: Octopii directory not found at {OCTOPII_DIR}")
    print(f"Please run this script from your project root directory")
    sys.exit(1)

sys.path.insert(0, str(OCTOPII_DIR))

try:
    import text_utils
    import re
except ImportError as e:
    print(f"Error importing text_utils: {e}")
    print(f"Make sure Octopii/text_utils.py exists")
    sys.exit(1)

# Test data from synthetic documents
TEST_TEXT = """
SYNTHETIC DATA — FOR TESTING ONLY

Patient Details:
- Patient Name: Aarti Kumari (SYNTHETIC)
- Gender: Female
- Age: 34
- Date of Birth: 18-Apr-1991
- Address: H.No. 12, Greens Avenue, Sector 7, Indrapuri, Jaipur, Rajasthan — 302017
- Contact Phone: +91-98234-56789
- Email: aarti.kumari.synthetic@example.com
- Aadhaar (synthetic): 9999 0000 1111
- PAN (synthetic): AAAAP1234Q

Applicant Details:
- Name: Rohit Verma (SYNTHETIC)
- Mobile: +91-98111-22334
- Email: rohit.verma.synthetic@example.com
- PAN (synthetic): RERVP9876Z
- Aadhaar (synthetic): 1111 2222 3333

Bank Details:
- Bank Account Number: 000987654321
- IFSC: JJVB0001122
- Account Holder: Rohit Verma

Additional PIIs:
- Another Aadhaar: 4444 5555 6666
- Phone: +91-99876-55443
- Alternative Aadhaar format: 7777-8888-9999
- Consolidated Aadhaar: 111122223333
"""

VERBOSE = False

def print_header(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def print_subheader(title):
    """Print formatted subsection header"""
    print(f"\n{title}")
    print("-" * 70)

def print_pass(msg):
    print(f"    {msg}")

def print_fail(msg):
    print(f"    {msg}")

def print_info(msg):
    if VERBOSE:
        print(f"     {msg}")


class TestResults:
    """Track test results"""
    def __init__(self):
        self.total = 0
        self.passed = 0
    
    def add_pass(self):
        self.total += 1
        self.passed += 1
    
    def add_fail(self):
        self.total += 1
    
    @property
    def failed(self):
        return self.total - self.passed
    
    @property
    def success_rate(self):
        if self.total == 0:
            return 0
        return (self.passed / self.total) * 100


def test_detection(results):
    """Test if all PII types are detected correctly"""
    print_header("TEST 1: PII DETECTION")
    
    rules = text_utils.get_regexes()
    
    # Test 1.1: Aadhaar Card Detection
    print_subheader("1.1 Aadhaar Card Detection")
    aadhaar_regex = rules["Aadhaar Card"]["regex"]
    aadhaar_matches = [m.group(0) for m in re.finditer(aadhaar_regex, TEST_TEXT)]
    
    print_info(f"Regex: {aadhaar_regex}")
    print(f"   Expected: 5 Aadhaar numbers")
    print(f"   Found: {len(aadhaar_matches)} Aadhaar numbers")
    
    if VERBOSE:
        for i, match in enumerate(aadhaar_matches, 1):
            print_info(f"{i}. '{match}'")
    
    if len(aadhaar_matches) >= 4:
        print_pass("Aadhaar detection working")
        results.add_pass()
    else:
        print_fail(f"Only found {len(aadhaar_matches)} Aadhaars, expected at least 4")
        results.add_fail()
    
    # Test 1.2: PAN Detection
    print_subheader("1.2 PAN Card Detection")
    pan_regex = rules["Permanent Account Number"]["regex"]
    pan_matches = [m.group(0) for m in re.finditer(pan_regex, TEST_TEXT)]
    
    print_info(f"Regex: {pan_regex}")
    print(f"   Expected: 2 PAN numbers")
    print(f"   Found: {len(pan_matches)} PAN numbers")
    
    if VERBOSE:
        for i, match in enumerate(pan_matches, 1):
            print_info(f"{i}. '{match}'")
    
    if len(pan_matches) == 2:
        print_pass("PAN detection working")
        results.add_pass()
    else:
        print_fail(f"Found {len(pan_matches)} PANs, expected 2")
        results.add_fail()
    
    # Test 1.3: Email Detection
    print_subheader("1.3 Email Detection")
    email_matches = text_utils.email_pii(TEST_TEXT, rules)
    
    print(f"   Expected: 2 emails")
    print(f"   Found: {len(email_matches)} emails")
    
    if VERBOSE:
        for i, match in enumerate(email_matches, 1):
            print_info(f"{i}. '{match}'")
    
    if len(email_matches) == 2:
        print_pass("Email detection working")
        results.add_pass()
    else:
        print_fail(f"Found {len(email_matches)} emails, expected 2")
        results.add_fail()
    
    # Test 1.4: Phone Number Detection
    print_subheader("1.4 Phone Number Detection")
    phone_matches = text_utils.phone_pii(TEST_TEXT, rules)
    
    print(f"   Expected: 3 phone numbers")
    print(f"   Found: {len(phone_matches)} phone numbers")
    
    if VERBOSE:
        for i, match in enumerate(phone_matches, 1):
            print_info(f"{i}. '{match}'")
    
    if len(phone_matches) >= 3:
        print_pass("Phone detection working")
        results.add_pass()
    else:
        print_fail(f"Found {len(phone_matches)} phones, expected at least 3")
        results.add_fail()
    
    # Test 1.5: Bank Account Detection
    print_subheader("1.5 Bank Account Detection")
    bank_regex = rules["Banking"]["regex"]
    
    if bank_regex:
        bank_matches = [m.group(0) for m in re.finditer(bank_regex, TEST_TEXT)]
        
        print_info(f"Regex: {bank_regex}")
        print(f"   Expected: At least 1 account number")
        print(f"   Found: {len(bank_matches)} account numbers")
        
        if VERBOSE:
            for i, match in enumerate(bank_matches, 1):
                print_info(f"{i}. '{match}'")
        
        if len(bank_matches) >= 1:
            print_pass("Bank account detection working")
            results.add_pass()
        else:
            print_fail("No account numbers detected")
            results.add_fail()
    else:
        print_fail("Banking regex not defined in definitions.json")
        results.add_fail()
    
    # Test 1.6: Complete ID Card Detection
    print_subheader("1.6 ID Card Numbers (via id_card_numbers_pii)")
    identifiers = text_utils.id_card_numbers_pii(TEST_TEXT, rules)
    
    print(f"   Found {len(identifiers)} identifier types:")
    for id_result in identifiers:
        id_class = id_result['identifier_class']
        id_values = id_result['result']
        print(f"     - {id_class}: {len(id_values)} value(s)")
        if VERBOSE:
            for val in id_values:
                print_info(f"* {val}")
    
    if len(identifiers) >= 2:
        print_pass("ID card detection working (found multiple types)")
        results.add_pass()
    else:
        print_fail("Not enough identifier types detected")
        results.add_fail()


def test_complete_matching(results):
    """Test that COMPLETE values are matched, not partial"""
    print_header("TEST 2: COMPLETE VALUE MATCHING")
    
    rules = text_utils.get_regexes()
    
    test_cases = [
        ("9999 0000 1111", "Aadhaar Card", "spaces"),
        ("7777-8888-9999", "Aadhaar Card", "hyphens"),
        ("111122223333", "Aadhaar Card", "no separators"),
        ("AAAAP1234Q", "Permanent Account Number", "standard"),
        ("RERVP9876Z", "Permanent Account Number", "standard"),
        ("+91-98234-56789", "Phone Number", "with country code"),
    ]
    
    for value, pii_type, description in test_cases:
        regex = rules[pii_type]["regex"]
        match = re.search(regex, value)
        
        if match:
            matched_text = match.group(0)
            norm_original = value.replace(' ', '').replace('-', '').replace('+', '')
            norm_matched = matched_text.replace(' ', '').replace('-', '').replace('+', '')
            
            if norm_original == norm_matched:
                print_pass(f"{pii_type} ({description}): '{value}'")
                results.add_pass()
            else:
                print_fail(f"{pii_type} ({description}): Partial match")
                print_info(f"Expected: '{value}'")
                print_info(f"Got: '{matched_text}'")
                results.add_fail()
        else:
            print_fail(f"{pii_type} ({description}): No match for '{value}'")
            results.add_fail()


def test_no_keyword_redaction(results):
    """Verify keywords themselves aren't matched, only values"""
    print_header("TEST 3: KEYWORD vs VALUE DETECTION")
    
    rules = text_utils.get_regexes()
    aadhaar_regex = rules["Aadhaar Card"]["regex"]
    pan_regex = rules["Permanent Account Number"]["regex"]
    
    # Test that keywords don't match
    print_subheader("3.1 Keywords should NOT match")
    non_matches = ["Aadhaar", "aadhaar", "Aadhaar:", "PAN", "PAN:", "UID"]
    
    all_pass = True
    for text in non_matches:
        if re.search(aadhaar_regex, text) or re.search(pan_regex, text):
            print_fail(f"Keyword '{text}' incorrectly matched")
            all_pass = False
            results.add_fail()
        else:
            if VERBOSE:
                print_pass(f"Keyword '{text}' correctly ignored")
    
    if all_pass:
        print_pass("All keywords correctly ignored")
        results.add_pass()
    
    # Test that values DO match
    print_subheader("3.2 Values should match")
    valid_values = [
        ("9999 0000 1111", aadhaar_regex),
        ("1111-2222-3333", aadhaar_regex),
        ("AAAAP1234Q", pan_regex)
    ]
    
    for value, regex in valid_values:
        match = re.search(regex, value)
        if match:
            print_pass(f"Value '{value}' correctly matched")
            results.add_pass()
        else:
            print_fail(f"Value '{value}' not matched")
            results.add_fail()


def test_regex_patterns(results):
    """Test regex patterns for edge cases"""
    print_header("TEST 4: REGEX EDGE CASES")
    
    rules = text_utils.get_regexes()
    
    # Test Aadhaar variations
    print_subheader("4.1 Aadhaar Format Variations")
    aadhaar_regex = rules["Aadhaar Card"]["regex"]
    
    aadhaar_tests = [
        ("9999 0000 1111", True, "with spaces"),
        ("9999-0000-1111", True, "with hyphens"),
        ("999900001111", True, "no separators"),
        ("9999  0000  1111", False, "double spaces (should fail)"),  # Strict test
        ("999 000 111", False, "too short"),
        ("99999999999999", False, "too long"),
    ]
    
    for value, should_match, desc in aadhaar_tests:
        match = re.search(aadhaar_regex, value)
        matched = match is not None
        
        if matched == should_match:
            print_pass(f"{desc}: '{value}' → {matched}")
            results.add_pass()
        else:
            print_fail(f"{desc}: '{value}' → {matched}, expected {should_match}")
            results.add_fail()
    
    # Test word boundaries
    print_subheader("4.2 Word Boundary Testing")
    
    # Should NOT match Aadhaar within a longer number
    test_in_context = "123999900001111456"  # Aadhaar embedded in longer string
    match = re.search(aadhaar_regex, test_in_context)
    
    if not match:
        print_pass("Word boundaries prevent false matches in longer strings")
        results.add_pass()
    else:
        print_fail(f"Incorrectly matched embedded number: {match.group(0)}")
        results.add_fail()


def test_integration(results):
    """Integration test with full document"""
    print_header("TEST 5: FULL INTEGRATION")
    
    rules = text_utils.get_regexes()
    
    print_subheader("5.1 Extract All PII")
    
    # Get all PII
    emails = text_utils.email_pii(TEST_TEXT, rules)
    phones = text_utils.phone_pii(TEST_TEXT, rules)
    identifiers_result = text_utils.id_card_numbers_pii(TEST_TEXT, rules)
    
    # Flatten identifiers
    identifiers = []
    for id_result in identifiers_result:
        identifiers.extend(id_result['result'])
    
    print(f"   Emails: {len(emails)}")
    print(f"   Phones: {len(phones)}")
    print(f"   Identifiers: {len(identifiers)}")
    
    if VERBOSE:
        print_info("Emails:")
        for e in emails:
            print_info(f"  - {e}")
        print_info("Phones:")
        for p in phones:
            print_info(f"  - {p}")
        print_info("Identifiers:")
        for i in identifiers:
            print_info(f"  - {i}")
    
    total_pii = len(emails) + len(phones) + len(identifiers)
    expected_minimum = 10
    
    print(f"\n   Total PII: {total_pii}")
    print(f"   Expected: ≥{expected_minimum}")
    
    if total_pii >= expected_minimum:
        print_pass(f"Integration test passed ({total_pii} PII found)")
        results.add_pass()
    else:
        print_fail(f"Only {total_pii} PII found, expected ≥{expected_minimum}")
        results.add_fail()


def run_all_tests(verbose=False):
    """Run complete test suite"""
    global VERBOSE
    VERBOSE = verbose
    
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "OCTOPII PII DETECTION TEST SUITE" + " " * 21 + "║")
    print("╚" + "═" * 68 + "╝")
    
    results = TestResults()
    
    # Run all test groups
    try:
        test_detection(results)
        test_complete_matching(results)
        test_no_keyword_redaction(results)
        test_regex_patterns(results)
        test_integration(results)
    except Exception as e:
        print(f"\n✗ TEST SUITE CRASHED: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    # Final Summary
    print_header("FINAL TEST SUMMARY")
    print(f"   Total Tests: {results.total}")
    print(f"   Passed: {results.passed}")
    print(f"   Failed: {results.failed}")
    print(f"   Success Rate: {results.success_rate:.1f}%")
    
    if results.failed == 0:
        print("\n    ALL TESTS PASSED!")
        print("   Your PII detection system is working correctly.")
        print("\n   Next steps:")
        print("   1. Run: python Octopii/octopii.py InsureLoans.pdf")
        print("   2. Check output.json for detected PII")
        print("   3. Run: python Redactopii/redactopii.py --input InsureLoans.pdf --report output.json")
        return 0
    else:
        print(f"\n   ⚠ {results.failed} TEST(S) FAILED")
        print("   Please review the failures above.")
        print("\n   Common fixes:")
        print("   1. Update Octopii/definitions.json with new regex patterns")
        print("   2. Update Octopii/text_utils.py id_card_numbers_pii() function")
        print("   3. Ensure you're using re.finditer() with .group(0)")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='Test suite for PII detection fixes',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    exit_code = run_all_tests(verbose=args.verbose)
    
    print("\n" + "=" * 70)
    print("TEST SUITE COMPLETED")
    print("=" * 70 + "\n")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())