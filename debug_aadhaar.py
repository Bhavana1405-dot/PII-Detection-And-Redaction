#!/usr/bin/env python3
"""
Debug script to see exactly how OCR is reading Aadhaar numbers
This will show you what text is being extracted and why detection fails
"""

import sys
import os
sys.path.insert(0, 'Octopii')

import cv2
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_path

# Path to your PDF
PDF_PATH = "dummy-pii/InsureLoans.pdf"

# Windows Poppler path
if os.name == 'nt':
    POPPLER_PATH = r"C:\Users\Bhavana\Downloads\Release-25.07.0-0\poppler-25.07.0\Library\bin"
else:
    POPPLER_PATH = None

print("=" * 80)
print("AADHAAR DETECTION DEBUG")
print("=" * 80)

# Convert first page of PDF
pages = convert_from_path(PDF_PATH, dpi=400, poppler_path=POPPLER_PATH)
page = pages[0]

# Get OCR data with bounding boxes
ocr_data = pytesseract.image_to_data(page, output_type=Output.DICT)

# Get full text
full_text = pytesseract.image_to_string(page)

print("\n1. SEARCHING FOR AADHAAR PATTERNS IN FULL TEXT")
print("-" * 80)

# Look for Aadhaar-like patterns in full text
import re

# Try different patterns
patterns = [
    (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', "Standard (4-4-4)"),
    (r'\b\d{12}\b', "Consolidated (12 digits)"),
    (r'9999[\s-]?0000[\s-]?1111', "Specific test Aadhaar"),
    (r'1111[\s-]?2222[\s-]?3333', "Another test Aadhaar"),
    (r'4444[\s-]?5555[\s-]?6666', "Third test Aadhaar"),
]

for pattern, desc in patterns:
    matches = re.findall(pattern, full_text)
    if matches:
        print(f"✓ {desc}: Found {len(matches)} match(es)")
        for m in matches[:3]:
            print(f"    - '{m}'")
    else:
        print(f"✗ {desc}: No matches")

print("\n2. CHECKING OCR TOKEN-BY-TOKEN")
print("-" * 80)
print("Looking for tokens that might be parts of Aadhaar numbers...\n")

# Find tokens that look like they might be Aadhaar parts
aadhaar_candidates = []

for i, text in enumerate(ocr_data['text']):
    if not text or len(text) < 4:
        continue
    
    # Check if this looks like an Aadhaar segment
    if re.match(r'^\d{4,12}$', text):
        x = ocr_data['left'][i]
        y = ocr_data['top'][i]
        w = ocr_data['width'][i]
        h = ocr_data['height'][i]
        
        aadhaar_candidates.append({
            'text': text,
            'bbox': (x, y, w, h),
            'index': i
        })

if aadhaar_candidates:
    print(f"Found {len(aadhaar_candidates)} candidate numeric tokens:")
    for candidate in aadhaar_candidates[:20]:  # Show first 20
        print(f"  Token: '{candidate['text']}'")
        print(f"    Position: ({candidate['bbox'][0]}, {candidate['bbox'][1]})")
        print(f"    Size: {candidate['bbox'][2]}x{candidate['bbox'][3]}")
        print()
else:
    print("No numeric tokens found that could be Aadhaar parts")

print("\n3. CHECKING SPECIFIC AADHAAR LOCATIONS")
print("-" * 80)

# Known Aadhaar numbers from your test data
known_aadhaars = [
    "9999 0000 1111",
    "9999-0000-1111", 
    "999900001111",
    "1111 2222 3333",
    "1111-2222-3333",
    "111122223333",
    "4444 5555 6666",
    "4444-5555-6666",
    "444455556666"
]

print("Searching for known Aadhaar numbers:\n")

for aadhaar in known_aadhaars:
    # Try exact match
    if aadhaar in full_text:
        print(f"✓ Found exact: '{aadhaar}'")
    else:
        # Try normalized (remove spaces/hyphens)
        normalized = aadhaar.replace(' ', '').replace('-', '')
        if normalized in full_text.replace(' ', '').replace('-', ''):
            print(f"~ Found normalized: '{aadhaar}' (as '{normalized}')")
        else:
            print(f"✗ Not found: '{aadhaar}'")

print("\n4. SAMPLE OF OCR OUTPUT")
print("-" * 80)
print("First 1000 characters of extracted text:\n")
print(full_text[:1000])
print("\n...")

print("\n5. RECOMMENDATIONS")
print("-" * 80)

# Count how many 12-digit sequences we found
consolidated_pattern = r'\b\d{12}\b'
consolidated_matches = re.findall(consolidated_pattern, full_text)

if len(consolidated_matches) > 0:
    print(f"✓ Found {len(consolidated_matches)} 12-digit number(s)")
    print("  These are likely Aadhaar numbers without separators")
    print("\n  ACTION: Your regex \\b\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}\\b should work")
    print("  ISSUE: The OCR might be adding extra spaces/characters")
else:
    print("✗ No 12-digit sequences found")
    print("\n  POSSIBLE CAUSES:")
    print("  1. OCR is breaking Aadhaar into separate tokens")
    print("  2. OCR quality is poor (increase DPI?)")
    print("  3. Aadhaar numbers have special formatting in PDF")
    print("\n  ACTIONS:")
    print("  1. Try preprocessing: increase PDF conversion DPI to 600")
    print("  2. Update search_pii() to reconstruct split numbers")
    print("  3. Check if PDF has selectable text (not scanned image)")

print("\n" + "=" * 80)