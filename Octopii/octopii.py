import nltk
import nltk.tokenize.punkt as punkt
import pathlib
import pytesseract
from pytesseract import Output

# Ensure common NLTK resources are available
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
        if pkg in ("punkt", "punkt_tab"):
            nltk.data.find(f"tokenizers/{pkg}")
        else:
            nltk.data.find(pkg)
    except LookupError:
        try:
            nltk.download(pkg)
        except Exception:
            pass

try:
    punkt.PunktLanguageVars = punkt.PunktLanguageVars
except Exception:
    pass


output_file = "output.json"
notifyURL = ""

import json, textract, sys, urllib, cv2, os, json, shutil, traceback, re
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
    detection_texts = [text]
    collapsed = re.sub(r'\s+', '', text)
    if collapsed != text:
        detection_texts.append(collapsed)
    digits_only = ''.join(c for c in text if c.isdigit())
    if digits_only and digits_only != collapsed:
        detection_texts.append(digits_only)

    identifiers = []
    seen_ids = set()
    for dt in detection_texts:
        try:
            ids_result = text_utils.id_card_numbers_pii(dt, rules)
        except Exception:
            ids_result = []
        for id_result in ids_result:
            for r in id_result.get('result', []):
                norm = re.sub(r'[\s-]+', '', str(r))
                if norm not in seen_ids:
                    seen_ids.add(norm)
                    identifiers.append(r)

    if temp_dir in file_path:
        file_path = urllib.parse.unquote(file_path.replace(temp_dir, ""))

    # --- ENHANCED PII Location Mapping ---
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
            ULTRA-PRECISE bounding box finder with MULTI-LINE support
            
            NEW: Handles PII that spans across multiple lines (e.g., line-wrapped Aadhaar)
            
            Improvements:
            1. Multi-line detection with intelligent line break handling
            2. Horizontal gap detection within same line
            3. Vertical progression tracking (top-to-bottom flow)
            4. Smart validation thresholds
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
            
            # ========== STRATEGY 2: Multi-line consecutive tokens ==========
            max_tokens_in_pii = min(10, len(norm_pii.replace(' ', '')) + 2)
            
            for start in range(n):
                if not norm_tokens[start]:
                    continue
                
                for window_size in range(2, max_tokens_in_pii + 1):
                    end = start + window_size
                    if end > n:
                        break
                    
                    window_indices = list(range(start, end))
                    window_text = ''.join(norm_tokens[i] for i in window_indices)
                    
                    if window_text == norm_pii:
                        try:
                            # Group tokens by line (Y-position clustering)
                            lines = []
                            current_line = [window_indices[0]]
                            current_y = tops[window_indices[0]]
                            
                            for idx in window_indices[1:]:
                                y_diff = abs(tops[idx] - current_y)
                                
                                # If Y difference > 20px, it's a new line
                                if y_diff > 20:
                                    lines.append(current_line)
                                    current_line = [idx]
                                    current_y = tops[idx]
                                else:
                                    current_line.append(idx)
                            
                            lines.append(current_line)  # Add last line
                            
                            # Validate line progression (top-to-bottom, left-to-right)
                            is_valid = True
                            
                            # Check horizontal gaps WITHIN each line
                            for line_indices in lines:
                                for i in range(len(line_indices) - 1):
                                    idx1 = line_indices[i]
                                    idx2 = line_indices[i + 1]
                                    gap = lefts[idx2] - (lefts[idx1] + widths[idx1])
                                    
                                    # Allow max 50px gap on same line
                                    if gap > 50:
                                        print(f"  ⚠ Large horizontal gap: {gap}px for '{pii[:30]}...'")
                                        is_valid = False
                                        break
                                
                                if not is_valid:
                                    break
                            
                            if not is_valid:
                                continue
                            
                            # Check line breaks make sense (next line should start left)
                            if len(lines) > 1:
                                for i in range(len(lines) - 1):
                                    first_line_last_idx = lines[i][-1]
                                    second_line_first_idx = lines[i + 1][0]
                                    
                                    # Next line should be below and to the left (line wrap)
                                    y_progression = tops[second_line_first_idx] - tops[first_line_last_idx]
                                    x_regression = lefts[second_line_first_idx] - lefts[first_line_last_idx]
                                    
                                    # Vertical: must go down (20-80px typical line height)
                                    if not (20 < y_progression < 100):
                                        print(f"  ⚠ Invalid vertical progression: {y_progression}px")
                                        is_valid = False
                                        break
                                    
                                    # Horizontal: second line should start left of first line end (wrap)
                                    # But not too far left (must be reasonable wrap)
                                    if x_regression > 50:  # Moving right = not a wrap
                                        print(f"  ⚠ Not a line wrap (moving right: {x_regression}px)")
                                        is_valid = False
                                        break
                            
                            if not is_valid:
                                continue
                            
                            # Calculate bounding box covering all lines
                            x_min = min(lefts[i] for i in window_indices)
                            y_min = min(tops[i] for i in window_indices)
                            x_max = max(lefts[i] + widths[i] for i in window_indices)
                            y_max = max(tops[i] + heights[i] for i in window_indices)
                            
                            bbox_width = x_max - x_min
                            bbox_height = y_max - y_min
                            bbox_area = bbox_width * bbox_height
                            
                            # Validate size (more lenient for multi-line)
                            pii_len = len(norm_pii)
                            num_lines = len(lines)
                            
                            # For multi-line: width can be full page width
                            # Height should be reasonable (lines * ~40px)
                            expected_max_height = num_lines * 80  # Max 80px per line
                            
                            if bbox_height > expected_max_height:
                                print(f"  ⚠ Bbox too tall: {bbox_height}px for {num_lines} line(s)")
                                continue
                            
                            # Area check (more lenient for multi-line)
                            # Single line: ~15-25px/char * 40px height
                            # Multi-line: page_width * lines * 60px
                            max_reasonable_area = 800 * num_lines * 60  # Assume max 800px page width
                            
                            if bbox_area > max_reasonable_area:
                                print(f"  ⚠ Bbox area too large: {bbox_area}px² for {num_lines} line(s)")
                                continue
                            
                            print(f"  ✓ Found {num_lines}-line match for '{pii[:30]}...': {bbox_width}x{bbox_height}")
                            
                            return {
                                "x": int(x_min),
                                "y": int(y_min),
                                "width": int(bbox_width),
                                "height": int(bbox_height)
                            }
                        except (ValueError, IndexError) as e:
                            print(f"  ⚠ Error processing window: {e}")
                            continue
            
            # ========== STRATEGY 3: AADHAAR-SPECIFIC with line-wrap support ==========
            if len(norm_pii) == 12 and norm_pii.isdigit():
                # Try different token groupings: 1+1+1, 2+1, 1+2, 3, 4, 5, etc.
                for start in range(n):
                    for num_tokens in range(1, min(6, n - start)):
                        indices = list(range(start, start + num_tokens))
                        tokens = [norm_tokens[i] for i in indices if i < n]
                        
                        if len(tokens) < 1:
                            continue
                        
                        combined = ''.join(tokens)
                        
                        if combined == norm_pii:
                            try:
                                # Allow multi-line Aadhaar
                                # Group by lines
                                lines = []
                                current_line = [indices[0]]
                                current_y = tops[indices[0]]
                                
                                for idx in indices[1:]:
                                    if abs(tops[idx] - current_y) > 20:
                                        lines.append(current_line)
                                        current_line = [idx]
                                        current_y = tops[idx]
                                    else:
                                        current_line.append(idx)
                                lines.append(current_line)
                                
                                # Check gaps within lines
                                valid = True
                                for line_indices in lines:
                                    for i in range(len(line_indices) - 1):
                                        gap = lefts[line_indices[i+1]] - (lefts[line_indices[i]] + widths[line_indices[i]])
                                        if gap > 50:
                                            valid = False
                                            break
                                
                                if not valid:
                                    continue
                                
                                x_min = min(lefts[i] for i in indices)
                                y_min = min(tops[i] for i in indices)
                                x_max = max(lefts[i] + widths[i] for i in indices)
                                y_max = max(tops[i] + heights[i] for i in indices)
                                
                                bbox_width = x_max - x_min
                                bbox_height = y_max - y_min
                                bbox_area = bbox_width * bbox_height
                                
                                # For Aadhaar across 2 lines: 
                                # Width: up to full page (~800px)
                                # Height: 2 lines (~80px)
                                max_area = 800 * len(lines) * 60
                                
                                if bbox_area > max_area:
                                    print(f"  ⚠ Aadhaar bbox too large: {bbox_width}x{bbox_height}={bbox_area}px²")
                                    continue
                                
                                token_preview = '-'.join(tokens[:5])
                                print(f"  ✓ Found {len(lines)}-line Aadhaar: {token_preview} → {pii}")
                                
                                return {
                                    "x": int(x_min),
                                    "y": int(y_min),
                                    "width": int(bbox_width),
                                    "height": int(bbox_height)
                                }
                                
                            except (ValueError, IndexError):
                                continue
            
            # ========== STRATEGY 4: Fuzzy digit accumulation with multi-line ==========
            pii_digits = ''.join(c for c in pii if c.isdigit())
            
            if len(pii_digits) >= 8:
                current_digits = ""
                digit_indices = []
                
                for i in range(n):
                    tok_str = str(texts[i])
                    tok_digits = ''.join(c for c in tok_str if c.isdigit())
                    
                    if tok_digits:
                        # Check proximity to previous digit token
                        if digit_indices:
                            prev_idx = digit_indices[-1]
                            
                            # Check if it's a reasonable continuation
                            y_diff = abs(tops[i] - tops[prev_idx])
                            x_diff = lefts[i] - (lefts[prev_idx] + widths[prev_idx])
                            
                            # Allow line break: Y increases 20-100px, X goes negative (wrap)
                            is_line_break = (20 < y_diff < 100) and (x_diff < 0)
                            
                            # Or same line: Y within 15px, X gap < 100px
                            is_same_line = (y_diff < 15) and (x_diff < 100)
                            
                            if not (is_line_break or is_same_line):
                                # Reset - not a valid continuation
                                current_digits = tok_digits
                                digit_indices = [i]
                                continue
                        
                        # Add to sequence
                        current_digits += tok_digits
                        digit_indices.append(i)
                        
                        # Check match
                        if current_digits == pii_digits:
                            try:
                                x_min = min(lefts[j] for j in digit_indices)
                                y_min = min(tops[j] for j in digit_indices)
                                x_max = max(lefts[j] + widths[j] for j in digit_indices)
                                y_max = max(tops[j] + heights[j] for j in digit_indices)
                                
                                bbox_width = x_max - x_min
                                bbox_height = y_max - y_min
                                bbox_area = bbox_width * bbox_height
                                
                                # Estimate number of lines
                                y_positions = sorted(set(tops[j] for j in digit_indices))
                                num_lines = len([y for i, y in enumerate(y_positions) if i == 0 or y - y_positions[i-1] > 20])
                                
                                expected_max = 800 * max(num_lines, 1) * 60
                                
                                if bbox_area <= expected_max:
                                    print(f"  ✓ Fuzzy match ({num_lines} line(s)): {bbox_width}x{bbox_height}")
                                    return {
                                        "x": int(x_min),
                                        "y": int(y_min),
                                        "width": int(bbox_width),
                                        "height": int(bbox_height)
                                    }
                            except (ValueError, IndexError):
                                pass
                        
                        # Too many digits - reset
                        if len(current_digits) > len(pii_digits):
                            current_digits = tok_digits
                            digit_indices = [i]
            
            # ========== STRATEGY 5: Substring match in single token ==========
            for i, tok in enumerate(norm_tokens):
                if tok and norm_pii in tok and len(norm_pii) > 6:
                    tok_start_idx = tok.find(norm_pii)
                    char_width = widths[i] / max(1, len(tok))
                    
                    x_offset = int(tok_start_idx * char_width)
                    pii_width = int(len(norm_pii) * char_width)
                    
                    bbox = {
                        "x": int(lefts[i] + x_offset),
                        "y": int(tops[i]),
                        "width": int(pii_width),
                        "height": int(heights[i])
                    }
                    
                    if bbox['width'] * bbox['height'] < len(norm_pii) * 30 * 60:
                        print(f"  ✓ Substring match for '{pii[:30]}...'")
                        return bbox
            
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
                
                if area > expected_max_area * 10:
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