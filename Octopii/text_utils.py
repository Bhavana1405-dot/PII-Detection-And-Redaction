"""
MIT License

Copyright (c) Research @ RedHunt Labs Pvt Ltd
Written by Owais Shaikh
Email: owais.shaikh@redhuntlabs.com | me@0x4f.in

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import pytesseract, re, json, nltk, itertools, spacy, difflib, math
import pathlib

def string_tokenizer(text):
    final_word_list = []
    words_list = text.replace(" ", "\n").split("\n")
    
    for element in words_list: 
        if len(element) >= 2: 
            final_word_list.append(element)
    
    return final_word_list

def similarity(a, b): return difflib.SequenceMatcher(None, a, b).ratio() * 100

def get_regexes():
    # Get the directory where this script is located
    script_dir = pathlib.Path(__file__).parent.resolve()
    # Build the full path to definitions.json
    definitions_path = script_dir / 'definitions.json'
    
    with open(definitions_path, "r", encoding='utf-8') as json_file:
        rules = json.load(json_file)
    return rules

def email_pii(text, rules):
    email_rules = rules["Email"]["regex"]
    # FIXED: Use re.finditer to get all matches with their positions
    email_addresses = re.findall(email_rules, text)
    email_addresses = list(set(filter(None, email_addresses)))
    return email_addresses

def phone_pii(text, rules):
    phone_rules = rules["Phone Number"]["regex"]
    # FIXED: Findall with groups - extract all matches
    phone_numbers = re.findall(phone_rules, text)
    phone_numbers = list(itertools.chain(*phone_numbers))
    phone_numbers = list(set(filter(None, phone_numbers)))
    return phone_numbers

def id_card_numbers_pii(text, rules):
    results = []
    regional_regexes = {}
    
    for key in rules.keys():
        region = rules[key]["region"]
        if region is not None:
            regional_regexes[key] = rules[key]

    for key in regional_regexes.keys():
        rule = rules[key]["regex"]
        
        if rule is None:
            continue
            
        try:
            # FIXED: Use finditer and group(0) for COMPLETE matches
            matches = [m.group(0) for m in re.finditer(rule, text, re.IGNORECASE)]
        except Exception as e:
            print(f"Error processing {key}: {e}")
            matches = []

        if len(matches) > 0:
            result = {'identifier_class': key, 'result': list(set(matches))}
            results.append(result)

    return results

def read_pdf(pdf):
    pdf_contents = ""
    for page in pdf:
        pdf_contents += str(pytesseract.image_to_string(page, config='--psm 12'))

    return pdf_contents

# python -m spacy download en_core_web_sm
def regional_pii(text):
    import nltk
    from nltk import word_tokenize, pos_tag, ne_chunk
    from nltk.corpus import stopwords

    # Ensure required resources are downloaded
    resources = [
        "punkt",
        "maxent_ne_chunker",
        "maxent_ne_chunker_tab",
        "stopwords",
        "words",
        "averaged_perceptron_tagger",
        "averaged_perceptron_tagger_eng",
    ]
    for resource in resources:
        try:
            nltk.data.find(resource)
        except LookupError:
            try:
                nltk.download(resource)
            except Exception:
                pass

    stop_words = set(stopwords.words('english'))

    words = word_tokenize(text)
    tagged_words = pos_tag(words)
    try:
        named_entities = ne_chunk(tagged_words)
    except LookupError:
        named_entities = []

    locations = []

    for entity in named_entities:
        if isinstance(entity, nltk.tree.Tree):
            if entity.label() in ['GPE', 'GSP', 'LOCATION', 'FACILITY']:
                location_name = ' '.join([word for word, tag in entity.leaves() if word.lower() not in stop_words and len(word) > 2])
                locations.append(location_name)

    return list(set(locations))


def keywords_classify_pii(rules, intelligible_text_list):
    scores = {}

    for key, rule in rules.items():
        scores[key] = 0
        keywords = rule.get("keywords", [])
        if keywords is not None:
            for intelligible_text_word in intelligible_text_list:
                for keywords_word in keywords:
                    if similarity(
                        intelligible_text_word.lower()
                            .replace(".", "")
                            .replace("'", "")
                            .replace("-", "")
                            .replace("_", "")
                            .replace(",", ""),
                        keywords_word.lower()
                    ) > 80: scores[key] += 1

    return scores


def redact_pii(text, rules, redaction_char='█'):
    """
    NEW FUNCTION: Redacts all PII from text based on regex patterns
    Returns: (redacted_text, redaction_report)
    """
    redacted_text = text
    redaction_report = {}
    
    for pii_type, definition in rules.items():
        regex = definition.get('regex')
        if regex is None:
            continue
            
        try:
            # Find all matches
            matches = list(re.finditer(regex, redacted_text, re.IGNORECASE))
            count = len(matches)
            
            if count > 0:
                redaction_report[pii_type] = count
                
                # Replace in reverse order to maintain string indices
                for match in reversed(matches):
                    start, end = match.span()
                    original_text = match.group(0)
                    
                    # Replace with redaction blocks (same length as original)
                    redaction = redaction_char * len(original_text)
                    redacted_text = redacted_text[:start] + redaction + redacted_text[end:]
        
        except Exception as e:
            print(f"Error redacting {pii_type}: {e}")
            continue
    
    return redacted_text, redaction_report