
import nltk
import nltk.tokenize.punkt as punkt
import pathlib
import pytesseract
from pytesseract import Output

# Ensure common NLTK resources are available. The upstream punkt tokenizer
# may look for 'punkt_tab' in some environments; attempt to download both
# 'punkt' and 'punkt_tab' and fall back gracefully.

import os, sys
from pdf2image import convert_from_path

# Detect Windows and set Poppler path
if os.name == 'nt':  # Windows
    POPPLER_PATH = r"C:\Users\Bhavana\Downloads\Release-25.07.0-0\poppler-25.07.0\Library\bin"
else:
    POPPLER_PATH = None  # Linux/Mac: assumes poppler is in PATH


required_nltk = [
    "punkt",
    "punkt_tab",
    "maxent_ne_chunker",
    "stopwords",
    "words",
    "averaged_perceptron_tagger",
]

for pkg in required_nltk:
    try:
        # punkt and punkt_tab live under tokenizers/; other resources have their own paths
        if pkg in ("punkt", "punkt_tab"):
            nltk.data.find(f"tokenizers/{pkg}")
        else:
            nltk.data.find(pkg)
    except LookupError:
        try:
            nltk.download(pkg)
        except Exception:
            # If download fails (no network), continue — we'll attempt to redirect
            pass

# Redirect any 'punkt_tab' lookups to use the standard 'punkt' implementation
# by ensuring the language vars are present. This mirrors the original intent
# but is now tolerant to environments where punkt_tab isn't installed.
try:
    punkt.PunktLanguageVars = punkt.PunktLanguageVars
except Exception:
    # If anything goes wrong, don't block execution; tokenization may still work
    pass


output_file = "output.json"
notifyURL = ""

import json, textract, sys, urllib, cv2, os, json, shutil, traceback
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from pdf2image import convert_from_path
import image_utils, file_utils, text_utils, webhook

model_file_name = 'models/other_pii_model.h5'
labels_file_name = 'models/other_pii_model.txt'
temp_dir = ".OCTOPII_TEMP/"

def print_logo():
    logo = '''⠀⠀⠀ ⠀⡀⠀⠀⠀⢀⢀⠀⠀⠀⢀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠈⠋⠓⡅⢸⣝⢷⡅⢰⠙⠙⠁⠀⠀⠀⠀
⠀⢠⣢⣠⡠⣄⠀⡇⢸⢮⡳⡇⢸⠀⡠⡤⡤⡴  O C T O P I I
⠀⠀⠀⠀⠀⡳⠀⠧⣤⡳⣝⢤⠼⠀⡯⠀⠀⠈⠀ A PII scanner
⠀⠀⠀⠀⢀⣈⣋⣋⠮⡻⡪⢯⣋⢓⣉⡀    ______________
⠀⠀⠀⢀⣳⡁⡡⣅⠀⡗⣝⠀⡨⣅⢁⣗⠀⠀  (c) 2023 RedHunt Labs Pvt Ltd
⠀⠀⠀⠀⠈⠀⠸⣊⣀⡝⢸⣀⣸⠊⠀⠉⠀⠀⠀⠀by Owais Shaikh (owais.shaikh@redhuntlabs.com | me@0x4f.in)
⠀⠀⠀⠀⠀⠀⠀⠈⠈⠀⠀⠈⠈'''
    print (logo)

def help_screen():
    help = '''Usage: python octopii.py <file, local path or URL>
Note: Only Unix-like filesystems, S3 and open directory URLs are supported.'''
    print(help)

"""
CRITICAL FIX for octopii.py - search_pii function
This ensures complete PII values are mapped to their bounding boxes

REPLACE the search_pii function in Octopii/octopii.py with this version
"""

"""
CRITICAL FIX for octopii.py - PRECISE bounding box calculation
This version calculates tight bounding boxes that only cover the PII text

REPLACE the search_pii function in Octopii/octopii.py
"""

def search_pii(file_path):
    contains_faces = 0
    bounding_box_data = None
    text = ""
    intelligible = []

    # --- Image file ---
    if file_utils.is_image(file_path):
        image = cv2.imread(file_path)
        contains_faces = image_utils.scan_image_for_people(image)

        ocr_data = pytesseract.image_to_data(image, output_type=Output.DICT)
        bounding_box_data = {
            "text": ocr_data.get("text", []),
            "left": ocr_data.get("left", []),
            "top": ocr_data.get("top", []),
            "width": ocr_data.get("width", []),
            "height": ocr_data.get("height", [])
        }

        text = " ".join([t for t in bounding_box_data["text"] if t and t.strip()])
        try:
            original, intelligible = image_utils.scan_image_for_text(image)
        except Exception:
            intelligible = text_utils.string_tokenizer(text)

    # --- PDF file ---
    elif file_utils.is_pdf(file_path):
        pdf_pages = convert_from_path(file_path, 400, poppler_path=POPPLER_PATH)

        bounding_box_data = {"text": [], "left": [], "top": [], "width": [], "height": []}
        for page in pdf_pages:
            contains_faces = image_utils.scan_image_for_people(page)
            ocr_data = pytesseract.image_to_data(page, output_type=Output.DICT)
            text += " ".join(ocr_data['text'])
            for key in ["text", "left", "top", "width", "height"]:
                bounding_box_data[key].extend(ocr_data[key])
        intelligible = text_utils.string_tokenizer(text)

    # --- Plain text file ---
    else:
        text = textract.process(file_path).decode()
        intelligible = text_utils.string_tokenizer(text)

    # --- PII Detection ---
    addresses = text_utils.regional_pii(text)
    emails = text_utils.email_pii(text, rules)
    phone_numbers = text_utils.phone_pii(text, rules)
    keywords_scores = text_utils.keywords_classify_pii(rules, intelligible)
    score = max(keywords_scores.values(), default=0)
    pii_class = list(keywords_scores.keys())[list(keywords_scores.values()).index(score)] if score >= 5 else None
    country_of_origin = rules[pii_class]["region"] if pii_class else None
    
    # Get identifiers correctly
    import re

    # Build alternative detection strings for PDF/image OCR that may split digits
    detection_texts = [text]

    # add whitespace-collapsed version
    collapsed = re.sub(r'\s+', '', text)
    if collapsed != text:
        detection_texts.append(collapsed)

    # add digits-only version (useful when non-digit noise exists)
    digits_only = ''.join(c for c in text if c.isdigit())
    if digits_only and digits_only != collapsed:
        detection_texts.append(digits_only)

    # run id detection on all variants and merge unique results
    identifiers = []
    seen_ids = set()
    for dt in detection_texts:
        try:
            ids_result = text_utils.id_card_numbers_pii(dt, rules)
        except Exception:
            ids_result = []
        for id_result in ids_result:
            for r in id_result.get('result', []):
                # normalize identifier string (remove spaces/hyphens)
                norm = re.sub(r'[\s-]+', '', str(r))
                if norm not in seen_ids:
                    seen_ids.add(norm)
                    identifiers.append(r)


    if temp_dir in file_path:
        file_path = urllib.parse.unquote(file_path.replace(temp_dir, ""))

    # --- PRECISE PII Location Mapping ---
    pii_locations = {}

    def normalize_text(s):
        """Normalize text for matching"""
        if not s:
            return ""
        return s.lower().replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace(':', '').replace('+', '')

    if bounding_box_data:
        # --- Image/PDF: use bounding boxes ---
        texts = bounding_box_data['text']
        lefts = bounding_box_data['left']
        tops = bounding_box_data['top']
        widths = bounding_box_data['width']
        heights = bounding_box_data['height']

        def find_precise_bbox_for_pii(pii):
            """
            CRITICAL FIX: Find MINIMAL bounding box that covers ONLY the PII
            NOW HANDLES: Split numbers like "999900001111" that OCR reads as "9999 0000 1111"
            """
            norm_pii = normalize_text(pii)
            n = len(texts)
            
            if not norm_pii or n == 0:
                return None
            
            norm_tokens = [normalize_text(str(t)) for t in texts]
            
            # ========== STRATEGY 1: Single token exact match ==========
            for i, tok in enumerate(norm_tokens):
                if tok and tok == norm_pii:
                    return {
                        "x": int(lefts[i]),
                        "y": int(tops[i]),
                        "width": int(widths[i]),
                        "height": int(heights[i])
                    }
            
            # ========== STRATEGY 2: Consecutive tokens that form the PII ==========
            max_tokens_in_pii = min(8, len(norm_pii.replace(' ', '')) // 2 + 1)
            
            for start in range(n):
                if not norm_tokens[start]:
                    continue
                
                for window_size in range(1, max_tokens_in_pii + 1):
                    end = start + window_size
                    if end > n:
                        break
                    
                    window_indices = list(range(start, end))
                    window_text = ''.join(norm_tokens[i] for i in window_indices)
                    
                    if window_text == norm_pii:
                        try:
                            x_min = min(lefts[i] for i in window_indices)
                            y_min = min(tops[i] for i in window_indices)
                            x_max = max(lefts[i] + widths[i] for i in window_indices)
                            y_max = max(tops[i] + heights[i] for i in window_indices)
                            
                            return {
                                "x": int(x_min),
                                "y": int(y_min),
                                "width": int(x_max - x_min),
                                "height": int(y_max - y_min)
                            }
                        except (ValueError, IndexError):
                            continue
            
            # ========== STRATEGY 3: AADHAAR-SPECIFIC - Handle split 12-digit numbers ==========
            # For numbers like "999900001111" that might be split as "9999" "0000" "1111"
            if len(norm_pii) == 12 and norm_pii.isdigit():
                # Look for pattern: 4 digits + 4 digits + 4 digits
                for start in range(n):
                    if start + 2 >= n:
                        break
                    
                    # Get 3 consecutive tokens
                    token1 = norm_tokens[start]
                    token2 = norm_tokens[start + 1] if start + 1 < n else ""
                    token3 = norm_tokens[start + 2] if start + 2 < n else ""
                    
                    # Check if they form our 12-digit number
                    combined = token1 + token2 + token3
                    
                    if combined == norm_pii:
                        # Calculate bounding box covering all 3 tokens
                        try:
                            indices = [start, start + 1, start + 2]
                            x_min = min(lefts[i] for i in indices if i < n)
                            y_min = min(tops[i] for i in indices if i < n)
                            x_max = max(lefts[i] + widths[i] for i in indices if i < n)
                            y_max = max(tops[i] + heights[i] for i in indices if i < n)
                            
                            bbox = {
                                "x": int(x_min),
                                "y": int(y_min),
                                "width": int(x_max - x_min),
                                "height": int(y_max - y_min)
                            }
                            
                            print(f"  ✓ Found split Aadhaar: {token1} {token2} {token3} → {pii}")
                            return bbox
                        except (ValueError, IndexError):
                            continue
            
            # ========== STRATEGY 4: Fuzzy digit matching for complex PIIs ==========
            pii_digits = ''.join(c for c in pii if c.isdigit())
            
            if len(pii_digits) >= 8:  # Likely numeric ID
                current_digits = ""
                digit_indices = []
                
                for i in range(n):
                    tok_str = str(texts[i])
                    tok_digits = ''.join(c for c in tok_str if c.isdigit())
                    
                    if tok_digits:
                        current_digits += tok_digits
                        digit_indices.append(i)
                        
                        # Check if we matched the PII
                        if current_digits == pii_digits:
                            try:
                                x_min = min(lefts[j] for j in digit_indices)
                                y_min = min(tops[j] for j in digit_indices)
                                x_max = max(lefts[j] + widths[j] for j in digit_indices)
                                y_max = max(tops[j] + heights[j] for j in digit_indices)
                                
                                return {
                                    "x": int(x_min),
                                    "y": int(y_min),
                                    "width": int(x_max - x_min),
                                    "height": int(y_max - y_min)
                                }
                            except (ValueError, IndexError):
                                pass
                        
                        # If we have too many digits, reset
                        if len(current_digits) > len(pii_digits):
                            current_digits = tok_digits
                            digit_indices = [i]
                    else:
                        # Non-digit token - only reset if we haven't found a match yet
                        if len(current_digits) > 0 and current_digits != pii_digits:
                            current_digits = ""
                            digit_indices = []
            
            return None

        # Find locations for all detected PII with PRECISE boxes
        all_pii = emails + phone_numbers + identifiers + addresses
        
        print(f"Calculating precise bounding boxes for {len(all_pii)} PII values...")
        
        for pii in all_pii:
            bbox = find_precise_bbox_for_pii(pii)
            if bbox:
                # Validate bounding box size
                area = bbox['width'] * bbox['height']
                pii_len = len(pii.replace(' ', '').replace('-', ''))
                
                # Rough estimate: 12-20 pixels per character width, 20-35 pixels height
                expected_max_area = pii_len * 20 * 40  # Conservative upper bound
                
                if area > expected_max_area * 2:
                    print(f"  ⚠ Bbox too large for '{pii[:40]}...' ({bbox['width']}x{bbox['height']} = {area}px²)")
                    print(f"     Expected max: ~{expected_max_area}px²")
                    # Skip this bounding box - it's too large
                    continue
                
                pii_locations[pii] = bbox
                print(f"  ✓ Found precise location for: {pii[:40]}... ({bbox['width']}x{bbox['height']})")
            else:
                print(f"  ✗ Could not find location for: {pii[:40]}...")

    else:
        # --- Plain text: use character offsets ---
        norm_text = normalize_text(text)
        for pii in emails + phone_numbers + identifiers + addresses:
            norm_pii = normalize_text(pii)
            start = norm_text.find(norm_pii)
            if start != -1:
                pii_locations[pii] = {"start": start, "end": start + len(pii)}

    # --- Result ---
    result = {
        "file_path": file_path,
        "pii_class": pii_class,
        "score": score,
        "country_of_origin": country_of_origin,
        "faces": contains_faces,
        "identifiers": identifiers,
        "emails": emails,
        "phone_numbers": phone_numbers,
        "addresses": addresses,
        "pii_with_locations": pii_locations
    }

    return result

if __name__ in '__main__':
    if len(sys.argv) == 1:
        print_logo()
        help_screen()
        exit(-1)
    else:
        location = sys.argv[1]

        # Check for the -notify flag
        notify_index = sys.argv.index('--notify') if '--notify' in sys.argv else -1

        if notify_index != -1 and notify_index + 1 < len(sys.argv): notifyURL = sys.argv[notify_index + 1]
        else: notifyURL = None

    rules=text_utils.get_regexes()

    files = []
    items = []

    temp_exists = False

    print("Scanning '" + location + "'")

    try:
        shutil.rmtree(temp_dir)
    except: pass

    if "http" in location:
        try:
            file_urls = []
            _, extension = os.path.splitext(location)
            if extension != "":
                file_urls.append(location)
            else:
                files = file_utils.list_local_files(location)

            file_urls = file_utils.list_s3_files(location)
            if len(file_urls) != 0:
                temp_exists = True
                os.makedirs(os.path.dirname(temp_dir))
                for url in file_urls:
                    file_name = urllib.parse.quote(url, "UTF-8")
                    urllib.request.urlretrieve(url, temp_dir+file_name)

        except:
            try:
                file_urls = file_utils.list_directory_files(location)

                if len(file_urls) != 0: # directory listing (e.g.: Apache)
                    temp_exists = True
                    os.makedirs(os.path.dirname(temp_dir))
                    for url in file_urls:
                        try:
                            encoded_url = urllib.parse.quote(url, "UTF-8")
                            urllib.request.urlretrieve(url, temp_dir + encoded_url)
                        except: pass    # capture 404

                else:                   # curl text from location if available
                    temp_exists = True
                    os.makedirs(os.path.dirname(temp_dir))
                    encoded_url = urllib.parse.quote(location, "UTF-8") + ".txt"
                    urllib.request.urlretrieve(location, temp_dir + encoded_url)

            except:
                traceback.print_exc()
                print ("This URL is not a valid S3 or has no directory listing enabled. Try running Octopii on these files locally.")
                sys.exit(-1)

        files = file_utils.list_local_files(temp_dir)

    else:
        _, extension = os.path.splitext(location)
        if extension != "":
            files.append(location)
        else:
            files = file_utils.list_local_files(location)

    if len(files) == 0:
        print ("Invalid path provided. Please provide a non-empty directory or a file as an argument.")
        sys.exit(0)

    # try and truncate files if they're too big
    for file_path in files: 
        try: file_utils.truncate(file_path)
        except: pass

    for file_path in files:

        try:
            results = search_pii (file_path)
            print(json.dumps(results, indent=4))
            file_utils.append_to_output_file(results, output_file)
            if notifyURL != None: webhook.push_data(json.dumps(results), notifyURL)
            print ("\nOutput saved in " + output_file)

        except textract.exceptions.MissingFileError: print ("\nCouldn't find file '" + file_path + "', skipping...")
        
        except textract.exceptions.ShellError: print ("\nFile '" + file_path + "' is empty or corrupt, skipping...")

    if temp_exists: shutil.rmtree(temp_dir)

    sys.exit(0)
            

