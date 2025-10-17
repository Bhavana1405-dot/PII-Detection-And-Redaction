
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
    identifiers = text_utils.id_card_numbers_pii(text, rules)
    identifiers = identifiers[0]["result"] if identifiers else []

    if temp_dir in file_path:
        file_path = urllib.parse.unquote(file_path.replace(temp_dir, ""))

    # --- PII Location Mapping ---
    pii_locations = {}

    def normalize_text(s):
        return s.lower().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

    if bounding_box_data:
        # --- Image/PDF: use bounding boxes ---
        texts = bounding_box_data['text']
        lefts = bounding_box_data['left']
        tops = bounding_box_data['top']
        widths = bounding_box_data['width']
        heights = bounding_box_data['height']

        def find_bbox_for_pii(pii):
            norm_pii = normalize_text(pii)
            n = len(texts)
            match_indices = []
            norm_tokens = [normalize_text(t) for t in texts]

            # single-token match
            for i, tok in enumerate(norm_tokens):
                if tok and (tok in norm_pii or norm_pii in tok):
                    match_indices = [i]
                    break

            # sliding window (multi-token)
            if not match_indices:
                max_window = 6
                for start in range(n):
                    concat = norm_tokens[start]
                    if norm_pii in concat:
                        match_indices = [start]
                        break
                    for end in range(start+1, min(start+max_window, n)):
                        concat += norm_tokens[end]
                        if norm_pii in concat:
                            match_indices = list(range(start, end+1))
                            break
                    if match_indices:
                        break

            if match_indices:
                x_min = min(lefts[i] for i in match_indices)
                y_min = min(tops[i] for i in match_indices)
                x_max = max(lefts[i] + widths[i] for i in match_indices)
                y_max = max(tops[i] + heights[i] for i in match_indices)
                return {"x": int(x_min), "y": int(y_min), "width": int(x_max - x_min), "height": int(y_max - y_min)}
            return None

        for pii in emails + phone_numbers + identifiers + addresses:
            bbox = find_bbox_for_pii(pii)
            if bbox:
                pii_locations[pii] = bbox

    else:
        # --- Plain text: use character offsets ---
        norm_text = normalize_text(text)
        for pii in emails + phone_numbers + identifiers + addresses:
            start = norm_text.find(normalize_text(pii))
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
            


