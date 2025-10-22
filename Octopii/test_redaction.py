"""
Document Redaction Script for Octopii
Redacts PII from images and PDFs by drawing black boxes over detected PII
"""

import cv2
import numpy as np
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_path
from PIL import Image
import json
import pathlib
import re
import os
import sys
from datetime import datetime

# Import from your existing modules
import text_utils

class DocumentRedactor:
    def __init__(self):
        self.rules = text_utils.get_regexes()
        
    def normalize_text(self, text):
        """Normalize text for matching"""
        return text.lower().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    def find_pii_in_text(self, text):
        """Find all PII in text using regex patterns"""
        pii_found = []
        
        for pii_type, definition in self.rules.items():
            regex = definition.get('regex')
            if regex is None:
                continue
            
            try:
                # Find all matches with their positions
                for match in re.finditer(regex, text, re.IGNORECASE):
                    pii_found.append({
                        'type': pii_type,
                        'value': match.group(0),
                        'start': match.start(),
                        'end': match.end()
                    })
            except Exception as e:
                print(f"Error processing {pii_type}: {e}")
                
        return pii_found
    
    def find_bounding_boxes(self, ocr_data, pii_list):
        """Find bounding boxes for detected PII"""
        texts = ocr_data['text']
        lefts = ocr_data['left']
        tops = ocr_data['top']
        widths = ocr_data['width']
        heights = ocr_data['height']
        
        boxes_to_redact = []
        
        for pii in pii_list:
            pii_value = pii['value']
            norm_pii = self.normalize_text(pii_value)
            n = len(texts)
            
            # Normalize all tokens
            norm_tokens = [self.normalize_text(str(t)) for t in texts]
            
            # Try single token match first
            match_indices = []
            for i, tok in enumerate(norm_tokens):
                if tok and len(tok) > 0:
                    # Check if token is part of PII or vice versa
                    if (tok in norm_pii or norm_pii in tok) and len(tok) > 2:
                        match_indices = [i]
                        break
            
            # Try multi-token sliding window
            if not match_indices:
                max_window = 8
                for start in range(n):
                    if not norm_tokens[start]:
                        continue
                    concat = norm_tokens[start]
                    if norm_pii in concat:
                        match_indices = [start]
                        break
                    for end in range(start + 1, min(start + max_window, n)):
                        if not norm_tokens[end]:
                            continue
                        concat += norm_tokens[end]
                        if norm_pii in concat:
                            match_indices = list(range(start, end + 1))
                            break
                    if match_indices:
                        break
            
            # Calculate bounding box from matched tokens
            if match_indices:
                x_min = min(lefts[i] for i in match_indices)
                y_min = min(tops[i] for i in match_indices)
                x_max = max(lefts[i] + widths[i] for i in match_indices)
                y_max = max(tops[i] + heights[i] for i in match_indices)
                
                boxes_to_redact.append({
                    'x': int(x_min),
                    'y': int(y_min),
                    'width': int(x_max - x_min),
                    'height': int(y_max - y_min),
                    'pii_type': pii['type'],
                    'value': pii_value
                })
        
        return boxes_to_redact
    
    def redact_image(self, image_path, output_path=None):
        """Redact PII from an image file"""
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not read image {image_path}")
            return None
        
        # Perform OCR
        ocr_data = pytesseract.image_to_data(image, output_type=Output.DICT)
        
        # Extract text
        text = " ".join([t for t in ocr_data["text"] if t and t.strip()])
        
        # Find PII
        pii_found = self.find_pii_in_text(text)
        
        print(f"\nFound {len(pii_found)} PII instances:")
        for pii in pii_found:
            print(f"  - {pii['type']}: {pii['value']}")
        
        # Find bounding boxes
        boxes = self.find_bounding_boxes(ocr_data, pii_found)
        
        print(f"Redacting {len(boxes)} bounding boxes")
        
        # Draw black rectangles over PII
        for box in boxes:
            cv2.rectangle(
                image,
                (box['x'], box['y']),
                (box['x'] + box['width'], box['y'] + box['height']),
                (0, 0, 0),  # Black color
                -1  # Filled rectangle
            )
        
        # Save redacted image
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_path = f"{base_name}_redacted_{timestamp}.png"
        
        cv2.imwrite(output_path, image)
        print(f"\nRedacted image saved to: {output_path}")
        
        return output_path, pii_found
    
    def redact_pdf(self, pdf_path, output_path=None):
        """Redact PII from a PDF file"""
        # Detect Windows for Poppler path
        if os.name == 'nt':
            POPPLER_PATH = r"C:\Users\Bhavana\Downloads\Release-25.07.0-0\poppler-25.07.0\Library\bin"
        else:
            POPPLER_PATH = None
        
        # Convert PDF to images
        try:
            pages = convert_from_path(pdf_path, 400, poppler_path=POPPLER_PATH)
        except Exception as e:
            print(f"Error converting PDF: {e}")
            return None
        
        redacted_pages = []
        all_pii = []
        
        for page_num, page in enumerate(pages):
            print(f"\nProcessing page {page_num + 1}/{len(pages)}...")
            
            # Convert PIL image to OpenCV format
            page_cv = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            
            # Perform OCR
            ocr_data = pytesseract.image_to_data(page, output_type=Output.DICT)
            
            # Extract text
            text = " ".join([t for t in ocr_data["text"] if t and t.strip()])
            
            # Find PII
            pii_found = self.find_pii_in_text(text)
            all_pii.extend(pii_found)
            
            print(f"Found {len(pii_found)} PII instances on page {page_num + 1}")
            
            # Find bounding boxes
            boxes = self.find_bounding_boxes(ocr_data, pii_found)
            
            # Draw black rectangles
            for box in boxes:
                cv2.rectangle(
                    page_cv,
                    (box['x'], box['y']),
                    (box['x'] + box['width'], box['y'] + box['height']),
                    (0, 0, 0),
                    -1
                )
            
            # Convert back to PIL
            page_redacted = Image.fromarray(cv2.cvtColor(page_cv, cv2.COLOR_BGR2RGB))
            redacted_pages.append(page_redacted)
        
        # Save as PDF
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_path = f"{base_name}_redacted_{timestamp}.pdf"
        
        if redacted_pages:
            redacted_pages[0].save(
                output_path, 
                save_all=True, 
                append_images=redacted_pages[1:],
                resolution=100.0,
                quality=95
            )
            print(f"\nRedacted PDF saved to: {output_path}")
        
        return output_path, all_pii


def main():
    if len(sys.argv) < 2:
        print("Usage: python redact_documents.py <file_path>")
        print("Supported formats: PDF, PNG, JPG, JPEG")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    # Create redactor
    redactor = DocumentRedactor()
    
    # Determine file type and redact
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    print(f"Processing file: {file_path}")
    print("=" * 60)
    
    if ext == '.pdf':
        output_path, pii_found = redactor.redact_pdf(file_path)
    elif ext in ['.png', '.jpg', '.jpeg']:
        output_path, pii_found = redactor.redact_image(file_path)
    else:
        print(f"Error: Unsupported file format: {ext}")
        sys.exit(1)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"REDACTION SUMMARY")
    print("=" * 60)
    print(f"Total PII found: {len(pii_found)}")
    
    # Group by type
    pii_by_type = {}
    for pii in pii_found:
        pii_type = pii['type']
        if pii_type not in pii_by_type:
            pii_by_type[pii_type] = []
        pii_by_type[pii_type].append(pii['value'])
    
    print("\nPII by type:")
    for pii_type, values in pii_by_type.items():
        print(f"  {pii_type}: {len(set(values))} unique value(s)")
        for val in set(values):
            print(f"    - {val}")
    
    print(f"\nRedacted file saved to: {output_path}")


if __name__ == '__main__':
    main()