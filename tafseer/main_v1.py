import re
import json
import os
import sys

# Configuration - set these values as needed
input_file = "test.json"  # Using test.json as requested
output_file = 'processed_output.json'
# Add debug mode to print extra information during processing
debug_mode = True  # Set to False for production

# Enhanced Arabic text markers for better recognition
KITAAB_MARKERS = [
    r'كتاب\s+', # Basic kitaab marker
    r'^\s*(\d+[\s*–\-.\)]+\s*)?كتاب', # Numbered kitaab
    r'كتاب\s+[^\d\s]+', # Kitaab followed by text
]

BAAB_MARKERS = [
    r'باب\s+', # Basic baab marker
    r'^\s*(\d+[\s*–\-.\)]+\s*)?باب', # Numbered baab
    r'باب\s+[^\d\s]+', # Baab followed by text
]

HADITH_MARKERS = [
    r'^\s*(\d+)\s*[-–\.\)]', # Simple numbered hadith
    r'\[\s*الحديث\s*(\d+)\s*[-–\.]', # Hadith in brackets
    r'حديث\s+(\d+)', # Hadith followed by number
]

# Helper functions
def remove_diacritics(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r'[\u064B-\u0652]', '', text)
    text = text.replace('\u200c', '') 
    return text.strip()

def is_strict_number_line(text):
    if not isinstance(text, str):
        return False
    match = re.match(r'^\s*(\d+)\s*[-–\.\)]*\s*$', text)
    return match

def is_strict_baab_line(text):
     if not isinstance(text, str):
        return False
     text = remove_diacritics(text)
     return re.match(r'^\s*باب\s*$', text)

def extract_number_from_text(text):
    match = is_strict_number_line(text)
    if match:
        return int(match.group(1))

    if not isinstance(text, str):
        return None
    match = re.match(r'^\s*(\d+)\s*[-–\.\)]*\s*', text)
    return int(match.group(1)) if match else None

def is_baab_pattern(text):
    if not isinstance(text, str):
        return False
    text = remove_diacritics(text)
    
    # Check against all baab markers
    for pattern in BAAB_MARKERS:
        if re.search(pattern, text, re.UNICODE):
            return True
    return False

def is_kitaab_pattern(text):
    if not isinstance(text, str):
        return False
    text = remove_diacritics(text)
    
    # Check against all kitaab markers
    for pattern in KITAAB_MARKERS:
        if re.search(pattern, text, re.UNICODE):
            return True
    return False

def extract_hadith_number(text):
    if not isinstance(text, str):
        return None
        
    # Check against all hadith markers
    for pattern in HADITH_MARKERS:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    
    # Try traditional pattern if no match
    match = re.match(r'^\s*(\d+)\s*[-–\.\)]', text)
    if match:
        return int(match.group(1))
    return None

# Function to parse JSON input
def parse_json_input(input_file):
    try:
        # Check file size before attempting to read
        file_size_mb = os.path.getsize(input_file) / (1024 * 1024)
        print(f"Input file size: {file_size_mb:.2f} MB")
        
        # Use chunked reading for large files
        print(f"Using chunked reading for {input_file}...")
        chunk_size = 1024 * 1024  # 1MB chunks
        with open(input_file, 'r', encoding="utf-8") as f:
            json_data = ""
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                json_data += chunk
            data = json.loads(json_data)
        return data
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        exit()
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{input_file}': {e}")
        exit()
    except Exception as e:
        print(f"Error reading file: {e}")
        exit()

# Improved function to handle different possible JSON structures
def flatten_document(input_data):
    document_flat = []
    position_counter = 0
    
    print("Flattening document structure...")
    found_structure = False
    
    # Structure 1: Pages with text content
    if 'pages' in input_data:
        print("Processing 'pages' structure...")
        found_structure = True
        for page_idx, page in enumerate(input_data['pages']):
            # Handle page text
            page_text = page.get('text', '')
            if page_text:
                # Special handling for Arabic tafseer text - look for span elements first
                if isinstance(page_text, str) and '<span' in page_text:
                    span_pattern = r'<span[^>]*data-type="title"[^>]*id=([^>]+)>([^<]+)</span>'
                    spans = re.finditer(span_pattern, page_text)
                    for span in spans:
                        title_id = span.group(1)
                        title_text = span.group(2)
                        item = {
                            'element': 'span',
                            'text': title_text.strip(),
                            'type': 'p',
                            'data_type': 'title',
                            'id': title_id,
                            'html': span.group(0),
                            'page_idx': page_idx,
                            'position': position_counter
                        }
                        document_flat.append(item)
                        position_counter += 1
                        # Remove the span from the text to avoid duplicates when we split into lines
                        page_text = page_text.replace(span.group(0), '')
                
                # Split the page text into lines or paragraphs
                lines = page_text.split('\n')
                for line in lines:
                    if line.strip():
                        # Check if this line could be a structural element
                        is_kitaab = is_kitaab_pattern(line)
                        is_baab = is_baab_pattern(line)
                        hadith_num = extract_hadith_number(line)
                        
                        # For Arabic tafseer text, we need to correctly set the data_type
                        data_type = None
                        if is_kitaab:
                            data_type = 'kitaab'
                        elif is_baab:
                            data_type = 'baab'
                        elif hadith_num is not None:
                            data_type = 'hadith'
                        
                        item = {
                            'element': None,
                            'text': line.strip(),
                            'type': 'p',
                            'data_type': data_type,
                            'hadith_number': hadith_num,
                            'id': '',
                            'html': line.strip(),
                            'page_idx': page_idx,
                            'position': position_counter
                        }
                        document_flat.append(item)
                        position_counter += 1
            
            # Handle page elements if they exist
            elements = page.get('elements', [])
            for element in elements:
                if element.get('text') and element.get('text').strip():
                    data_type = element.get('data-type') or element.get('dataType')
                    
                    # Check if this element is a structural element
                    element_text = element.get('text', '')
                    is_kitaab = is_kitaab_pattern(element_text)
                    is_baab = is_baab_pattern(element_text)
                    hadith_num = extract_hadith_number(element_text)
                    
                    if is_kitaab:
                        data_type = 'kitaab'
                    elif is_baab:
                        data_type = 'baab'
                    elif hadith_num is not None:
                        data_type = 'hadith'
                    
                    item = {
                        'element': element.get('type'),
                        'text': element_text.strip(),
                        'type': element.get('type', 'p'),
                        'data_type': data_type,
                        'hadith_number': hadith_num,
                        'id': element.get('id', ''),
                        'html': element.get('html', element_text),
                        'page_idx': page_idx,
                        'position': position_counter
                    }
                    document_flat.append(item)
                    position_counter += 1
    
    # Structure 2: Direct content structure - common in tafseer and Islamic texts
    elif 'content' in input_data:
        print("Processing 'content' structure...")
        found_structure = True
        content = input_data['content']
        
        if isinstance(content, list):
            for idx, item in enumerate(content):
                if isinstance(item, dict):
                    text = item.get('text', '')
                    is_kitaab = is_kitaab_pattern(text)
                    is_baab = is_baab_pattern(text)
                    hadith_num = extract_hadith_number(text)
                    
                    data_type = item.get('data-type')
                    if is_kitaab:
                        data_type = 'kitaab'
                    elif is_baab:
                        data_type = 'baab'
                    elif hadith_num is not None:
                        data_type = 'hadith'
                    
                    flat_item = {
                        'element': item.get('type'),
                        'text': text.strip(),
                        'type': item.get('type', 'p'),
                        'data_type': data_type,
                        'hadith_number': hadith_num,
                        'id': item.get('id', ''),
                        'html': item.get('html', text),
                        'page_idx': item.get('page', 0),
                        'position': position_counter
                    }
                    document_flat.append(flat_item)
                    position_counter += 1
                elif isinstance(item, str) and item.strip():
                    is_kitaab = is_kitaab_pattern(item)
                    is_baab = is_baab_pattern(item)
                    hadith_num = extract_hadith_number(item)
                    
                    data_type = None
                    if is_kitaab:
                        data_type = 'kitaab'
                    elif is_baab:
                        data_type = 'baab'
                    elif hadith_num is not None:
                        data_type = 'hadith'
                    
                    flat_item = {
                        'element': None,
                        'text': item.strip(),
                        'type': 'p',
                        'data_type': data_type,
                        'hadith_number': hadith_num,
                        'id': '',
                        'html': item.strip(),
                        'page_idx': 0,
                        'position': position_counter
                    }
                    document_flat.append(flat_item)
                    position_counter += 1
    
    # Structure 3: Direct text items in root
    elif 'items' in input_data:
        print("Processing 'items' structure...")
        found_structure = True
        for idx, item in enumerate(input_data['items']):
            if isinstance(item, dict):
                text = item.get('text', '')
                if text and text.strip():
                    is_kitaab = is_kitaab_pattern(text)
                    is_baab = is_baab_pattern(text)
                    hadith_num = extract_hadith_number(text)
                    
                    data_type = item.get('data-type')
                    if is_kitaab:
                        data_type = 'kitaab'
                    elif is_baab:
                        data_type = 'baab'
                    elif hadith_num is not None:
                        data_type = 'hadith'
                    
                    flat_item = {
                        'element': item.get('type'),
                        'text': text.strip(),
                        'type': item.get('type', 'p'),
                        'data_type': data_type,
                        'hadith_number': hadith_num,
                        'id': item.get('id', ''),
                        'html': item.get('html', text),
                        'page_idx': item.get('page', 0),
                        'position': position_counter
                    }
                    document_flat.append(flat_item)
                    position_counter += 1
    
    # Structure 4: Direct text in root - common in some Islamic text formats
    elif 'text' in input_data and isinstance(input_data['text'], str):
        print("Processing direct text in root...")
        found_structure = True
        text = input_data['text']
        lines = text.split('\n')
        for line in lines:
            if line.strip():
                is_kitaab = is_kitaab_pattern(line)
                is_baab = is_baab_pattern(line)
                hadith_num = extract_hadith_number(line)
                
                data_type = None
                if is_kitaab:
                    data_type = 'kitaab'
                elif is_baab:
                    data_type = 'baab'
                elif hadith_num is not None:
                    data_type = 'hadith'
                
                item = {
                    'element': None,
                    'text': line.strip(),
                    'type': 'p',
                    'data_type': data_type,
                    'hadith_number': hadith_num,
                    'id': '',
                    'html': line.strip(),
                    'page_idx': 0,
                    'position': position_counter
                }
                document_flat.append(item)
                position_counter += 1
    
    # Check for headings in indexes - important for Islamic texts
    if 'indexes' in input_data and 'headings' in input_data['indexes']:
        print("Processing 'indexes.headings' structure...")
        found_structure = True
        for heading_idx, heading in enumerate(input_data['indexes']['headings']):
            title = heading.get('title', '')
            if title:
                is_kitaab = is_kitaab_pattern(title)
                is_baab = is_baab_pattern(title)
                
                data_type = 'title'
                if is_kitaab:
                    data_type = 'kitaab'
                elif is_baab:
                    data_type = 'baab'
                
                item = {
                    'element': None,
                    'text': title,
                    'type': 'p',
                    'data_type': data_type,
                    'id': f'heading-{heading_idx}',
                    'html': title,
                    'page_idx': heading.get('page', 0),
                    'position': position_counter
                }
                document_flat.append(item)
                position_counter += 1
    
    # Fallback: Try to extract any text structures we can find
    if not found_structure or len(document_flat) == 0:
        print("No standard structure found, attempting to extract any text content recursively...")
        def extract_text_recursive(obj, path="root"):
            nonlocal position_counter
            
            if isinstance(obj, dict):
                # Special case for common text containers
                if 'text' in obj and isinstance(obj['text'], str) and obj['text'].strip():
                    text = obj['text'].strip()
                    is_kitaab = is_kitaab_pattern(text)
                    is_baab = is_baab_pattern(text)
                    hadith_num = extract_hadith_number(text)
                    
                    data_type = obj.get('data-type', obj.get('dataType'))
                    if is_kitaab:
                        data_type = 'kitaab'
                    elif is_baab:
                        data_type = 'baab'
                    elif hadith_num is not None:
                        data_type = 'hadith'
                    
                    item = {
                        'element': obj.get('type', obj.get('element')),
                        'text': text,
                        'type': obj.get('type', 'p'),
                        'data_type': data_type,
                        'hadith_number': hadith_num,
                        'id': obj.get('id', ''),
                        'html': obj.get('html', text),
                        'page_idx': obj.get('page', 0),
                        'position': position_counter,
                        'path': f"{path}.text"
                    }
                    document_flat.append(item)
                    position_counter += 1
                
                # Process all other keys
                for key, value in obj.items():
                    if key == 'text':
                        continue  # Already processed above
                    
                    # Special cases for arrays that might contain text
                    if key in ['content', 'items', 'elements', 'children', 'lines', 'paragraphs'] and isinstance(value, list):
                        for idx, item in enumerate(value):
                            extract_text_recursive(item, f"{path}.{key}[{idx}]")
                    else:
                        extract_text_recursive(value, f"{path}.{key}")
            
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    extract_text_recursive(item, f"{path}[{idx}]")
            
            # Direct string values that might be text content (common in some JSON formats)
            elif isinstance(obj, str) and obj.strip() and len(obj.strip()) > 5:  # Minimal length check
                text = obj.strip()
                is_kitaab = is_kitaab_pattern(text)
                is_baab = is_baab_pattern(text)
                hadith_num = extract_hadith_number(text)
                
                data_type = None
                if is_kitaab:
                    data_type = 'kitaab'
                elif is_baab:
                    data_type = 'baab'
                elif hadith_num is not None:
                    data_type = 'hadith'
                
                item = {
                    'element': None,
                    'text': text,
                    'type': 'p',
                    'data_type': data_type,
                    'hadith_number': hadith_num,
                    'id': '',
                    'html': text,
                    'page_idx': 0,
                    'position': position_counter,
                    'path': path
                }
                document_flat.append(item)
                position_counter += 1
        
        extract_text_recursive(input_data)
    
    # Always check for Title format content
    print(f"Checking for additional title formats...")
    for i, item in enumerate(document_flat):
        text = item.get('text', '')
        
        # Check if title was not already assigned but text matches a structural pattern
        if item.get('data_type') is None:
            is_kitaab = is_kitaab_pattern(text)
            is_baab = is_baab_pattern(text)
            hadith_num = extract_hadith_number(text)
            
            if is_kitaab:
                document_flat[i]['data_type'] = 'kitaab'
            elif is_baab:
                document_flat[i]['data_type'] = 'baab'
            elif hadith_num is not None:
                document_flat[i]['data_type'] = 'hadith'
                document_flat[i]['hadith_number'] = hadith_num
    
    print(f"Flattened document contains {len(document_flat)} items.")
    
    # Sort by position to maintain order
    document_flat.sort(key=lambda x: x['position'])
    
    return document_flat

# Main processing function to build the hierarchy from flattened document
def process_structure(document_flat):
    # Initialize structure
    document_structure = {"kitaabs": []}
    current_kitaab = None
    current_baab = None
    current_baab_context = [] 
    current_context_list = None 
    current_sub_baab = None 
    current_hadith = None 
    
    # Track content that doesn't belong to any structure
    unknown_content = []
    
    # Process each item sequentially from the ordered document_flat
    print("Starting structure processing...")
    i = 0
    
    while i < len(document_flat):
        item = document_flat[i]
        text = remove_diacritics(item.get('text', ''))
        
        # --- Kitaab Detection with multiple patterns ---
        is_kitaab = False
        
        # Standard data-type based detection
        if item.get('data_type') == 'kitaab' or item.get('data_type') == 'title' and is_kitaab_pattern(text):
            is_kitaab = True
        
        # Content-based detection
        elif is_kitaab_pattern(text):
            is_kitaab = True
    
        if is_kitaab:
            if debug_mode:
                print(f"--- Detected KITAAB: {item['text'][:80]} ---")
    
            # Close previous hadith if active (its content is already added)
            if current_hadith:
                if debug_mode:
                    print(f"  Closed previous HADITH ({current_hadith.get('hadith_number', 'N/A')})")
                current_hadith = None
    
            # Close previous sub-baab if active
            if current_sub_baab:
                if debug_mode:
                    print(f"  Closed previous SUB-BAAB ({current_sub_baab.get('number', 'N/A')})")
                current_sub_baab = None
    
            # Close the previous Baab if one is open within the current Kitaab
            if current_baab and current_kitaab:
                # Ensure the context list for the *main* baab is used when closing
                current_baab['context'] = current_baab_context
                current_kitaab['baabs'].append(current_baab)
                if debug_mode:
                    print(f"  Closed previous BAAB ({current_baab.get('number', 'N/A')}) with {len(current_baab_context)} context items.")
                current_baab_context = [] 
                current_baab = None 
    
            # Close the previous Kitaab if one is open
            if current_kitaab:
                # Add any unknown content to the kitaab
                if unknown_content:
                    if 'unclassified_content' not in current_kitaab:
                        current_kitaab['unclassified_content'] = []
                    current_kitaab['unclassified_content'].extend(unknown_content)
                    unknown_content = []
                    
                document_structure['kitaabs'].append(current_kitaab)
                if debug_mode:
                    print(f"  Closed previous KITAAB ({current_kitaab.get('number', 'N/A')}).")
    
            # Start a new Kitaab
            kitaab_number = extract_number_from_text(text)
            current_kitaab = {
                "number": kitaab_number if kitaab_number is not None else len(document_structure['kitaabs']) + 1,
                "title": item['text'].strip(),
                "baabs": [],
                "id": item.get('id', f"kitaab-{item['position']}")
            }
            if debug_mode:
                print(f"  Started new KITAAB: Number={current_kitaab['number']}, Title='{current_kitaab['title'][:80]}...'")
    
            # Reset all context/baab/sub-baab/hadith state
            current_baab = None
            current_baab_context = []
            current_context_list = None 
            current_sub_baab = None
            current_hadith = None
            i += 1 
            continue 
    
        # --- Baab Detection with multiple patterns ---
        is_baab = False
        
        # Standard data-type based detection
        if item.get('data_type') == 'baab':
            is_baab = True
        
        # Content-based detection
        elif is_baab_pattern(text):
            is_baab = True
    
        if is_baab:
            if not current_kitaab:
                if debug_mode:
                    print(f"Warning: Detected a potential BAAB pattern ('{item['text'][:80]}...') but no current KITAAB is active.")
                # Store this as unknown content
                unknown_content.append(item['text'].strip())
                i += 1 
                continue 
            else:
                if debug_mode:
                    print(f"--- Detected BAAB: {item['text'][:80]} --- (Item type: {item['type']}, data-type: {item.get('data_type')})")
    
                # Close previous hadith if active
                if current_hadith:
                    if debug_mode:
                        print(f"  Closed previous HADITH ({current_hadith.get('hadith_number', 'N/A')})")
                    current_hadith = None 
    
                # Close previous sub-baab if active
                if current_sub_baab:
                    if debug_mode:
                        print(f"  Closed previous SUB-BAAB ({current_sub_baab.get('number', 'N/A')})")
                    current_sub_baab = None 
    
                # Close the previous Baab if it exists within the current Kitaab
                if current_baab:
                    current_baab['context'] = current_baab_context 
                    current_kitaab['baabs'].append(current_baab)
                    if debug_mode:
                        print(f"  Closed previous BAAB ({current_baab.get('number', 'N/A')}) with {len(current_baab_context)} context items.")
    
                # Start a new Baab
                baab_number = extract_number_from_text(text)
                current_baab_context = [] 
                current_baab = {
                    "number": baab_number if baab_number is not None else len(current_kitaab['baabs']) + 1,
                    "title": item['text'].strip(),
                    "context": current_baab_context, 
                    "id": item.get('id', f"baab-{item['position']}")
                }
    
                # Set the context list pointer to the main baab context initially
                current_context_list = current_baab_context
                current_sub_baab = None 
                current_hadith = None 
    
                if debug_mode:
                    print(f"  Started new BAAB: Number={current_baab['number']}, Title='{current_baab['title'][:80]}...'")
                i += 1 # Consume the Baab item
                continue
    
        # --- Sub-Baab Detection (requires lookahead) ---
        # Check if we are in a Baab AND there is a next item
        is_sub_baab_marker = False
        if current_baab and i + 1 < len(document_flat):
            next_item = document_flat[i+1]
            # Use original text for strict matching
            item_original_text = item.get('text', '')
            next_item_original_text = next_item.get('text', '')
    
            # Check if current item is strict number line AND next item is strict 'باب' line
            if is_strict_number_line(item_original_text) and is_strict_baab_line(next_item_original_text):
                is_sub_baab_marker = True
                
            # Alternative sub-baab pattern
            elif is_strict_number_line(item_original_text) and "باب" in next_item_original_text and len(next_item_original_text) < 50:
                is_sub_baab_marker = True
    
        if is_sub_baab_marker:
            if debug_mode:
                print(f"--- Detected SUB-BAAB marker: '{item.get('text', '')[:40]}' AND '{next_item.get('text', '')[:40]}' ---")
    
            # Close previous hadith if active
            if current_hadith:
                if debug_mode:
                    print(f"  Closed previous HADITH ({current_hadith.get('hadith_number', 'N/A')})")
                current_hadith = None
    
            # Close previous sub-baab if active
            if current_sub_baab:
                if debug_mode:
                    print(f"  Closed previous SUB-BAAB ({current_sub_baab.get('number', 'N/A')})")
    
            # Start a new Sub-Baab
            sub_baab_number = extract_number_from_text(item.get('text', ''))
            # Combine the two lines for the sub-baab title
            sub_baab_title = f"{item.get('text', '').strip()} {next_item.get('text', '').strip()}".strip()
    
            # Create the sub-baab dictionary
            new_sub_baab = {
                "number": sub_baab_number if sub_baab_number is not None else len([c for c in current_baab_context if isinstance(c, dict) and 'context' in c]) + 1,
                "title": sub_baab_title,
                "context": [] # Initialize context list for this sub-baab
            }
            # Append the new sub-baab dictionary DIRECTLY to the main baab's context list
            current_baab_context.append(new_sub_baab)
            # Update the context list pointer to the new sub-baab's context list
            current_context_list = new_sub_baab['context']
            # Set the current sub-baab state
            current_sub_baab = new_sub_baab
            current_hadith = None
    
            if debug_mode:
                print(f"  Started new SUB-BAAB: Number={current_sub_baab['number']}, Title='{current_sub_baab['title'][:80]}...'")

            i += 2 # Consume both the number line and the 'باب' line
            continue # Move to the next item

        # --- Hadith Detection with enhanced patterns ---
        is_hadith_marker = False
        hadith_number = None
        
        # Data-type based detection
        if item.get('data_type') == 'hadith' and item.get('hadith_number') is not None:
            is_hadith_marker = True
            hadith_number = item.get('hadith_number')
        
        # Standard hadith number detection
        elif current_baab and is_strict_number_line(item.get('text', '')):
            match = is_strict_number_line(item.get('text', ''))
            if match:
                is_hadith_marker = True
                hadith_number = int(match.group(1))
        
        # Alternative hadith detection methods
        elif current_baab and extract_hadith_number(item.get('text', '')):
            hadith_number = extract_hadith_number(item.get('text', ''))
            is_hadith_marker = True

        if is_hadith_marker and hadith_number is not None:
            if debug_mode:
                print(f"--- Detected HADITH marker: '{item.get('text', '')[:40]}' (Number: {hadith_number}) ---")

            # Close the previous hadith if one was active
            if current_hadith:
                if debug_mode:
                    print(f"  Closed previous HADITH ({current_hadith.get('hadith_number', 'N/A')})")

            # Start a new Hadith block
            new_hadith = {
                "hadith_number": hadith_number,
                "context": [] # Initialize context list for this hadith
            }
            
            # Append the new hadith dictionary to the list currently pointed to by current_context_list
            if current_context_list is not None:
                current_context_list.append(new_hadith)
            else:
                # If no current context list, create one in the current baab
                if current_baab:
                    current_context_list = current_baab['context']
                    current_context_list.append(new_hadith)
                else:
                    print(f"Error: current_context_list is None when detecting HADITH for item {i} ({item['text'][:50]}...)")

            # Update the context list pointer to the new hadith's context list
            current_context_list = new_hadith['context']
            # Set the current hadith state
            current_hadith = new_hadith

            # Append the current item's text (the marker line) as the first line of the hadith's content
            cleaned_text = item.get('text', '').strip()
            if cleaned_text:
                current_context_list.append(cleaned_text) # Append just the string

            i += 1 # Consume the Hadith marker item
            continue # Move to the next item

        # --- Content Accumulation with more flexible rules ---
        # Relaxed criteria: Add text to the current context list if we're in any structured element
        if current_baab or current_kitaab:
            cleaned_text = item.get('text', '').strip()
            if cleaned_text:
                # Skip items that are already processed as structure markers
                if item.get('data_type') in ['kitaab', 'baab', 'title']:
                    i += 1
                    continue
                    
                # If we're in a specific context, add it there
                if current_context_list is not None:
                    current_context_list.append(cleaned_text) # Append just the string
                
                # If we're in a kitaab but not yet in a baab, add to kitaab-level content
                elif current_kitaab and not current_baab:
                    # Create a kitaab-level content field if it doesn't exist
                    if 'content' not in current_kitaab:
                        current_kitaab['content'] = []
                    current_kitaab['content'].append(cleaned_text)
                else:
                    # Fallback: add to unknown content
                    unknown_content.append(cleaned_text)
                    if debug_mode:
                        print(f"Warning: Could not determine where to place content: {cleaned_text[:50]}...")
            i += 1 # Consume the content item
            continue
        else:
            # Content before any structure - save as unknown
            cleaned_text = item.get('text', '').strip()
            if cleaned_text:
                unknown_content.append(cleaned_text)
            i += 1 # Consume the item
            continue

    # --- Finish the last Kitaab, Baab, Sub-Baab, and Hadith ---
    print("Finishing structure processing...")

    # Close the very last hadith if one was open
    if current_hadith:
        print(f"  Closed final HADITH ({current_hadith.get('hadith_number', 'N/A')})")

    # Close the very last sub-baab if one was open
    if current_sub_baab:
        print(f"  Closed final SUB-BAAB ({current_sub_baab.get('number', 'N/A')})")

    # Close the very last Baab if one was open
    if current_baab and current_kitaab:
        current_baab['context'] = current_baab_context # Ensure main baab context is finalized
        current_kitaab['baabs'].append(current_baab)
        print(f"  Closed final BAAB ({current_baab.get('number', 'N/A')}) with {len(current_baab_context)} context items.")

    # Close the very last Kitaab if one was open
    if current_kitaab:
        # Add any remaining unknown content to the last kitaab
        if unknown_content:
            if 'unclassified_content' not in current_kitaab:
                current_kitaab['unclassified_content'] = []
            current_kitaab['unclassified_content'].extend(unknown_content)
            unknown_content = []
        
        document_structure['kitaabs'].append(current_kitaab)
        print(f"  Closed final KITAAB ({current_kitaab.get('number', 'N/A')}).")
    else:
        print("No KITAABs were detected in the document.")

    # If there's still unknown content and no kitaabs were detected, add it to the root
    if unknown_content and len(document_structure['kitaabs']) == 0:
        document_structure['unclassified_content'] = unknown_content
        print(f"Added {len(unknown_content)} unclassified content items to the root")

    return document_structure

# Post-process the structure to ensure all hadith and content are properly captured
def post_process_structure(document_structure):
    # Check for missing content in baabs
    total_baabs = 0
    empty_baabs = 0
    
    # Collect statistics and fix any issues
    for kitaab_idx, kitaab in enumerate(document_structure['kitaabs']):
        for baab_idx, baab in enumerate(kitaab['baabs']):
            total_baabs += 1
            if len(baab['context']) == 0:
                empty_baabs += 1
                
                # If a baab has no context and the next baab exists, check if we can move some content
                if baab_idx + 1 < len(kitaab['baabs']):
                    next_baab = kitaab['baabs'][baab_idx + 1]
                    if 'title' in next_baab:
                        # We can't safely take content from the next baab
                        continue
                        
                    # Look for potential content in the next baab that might belong to this one
                    # For now, we'll just log the empty baabs rather than trying to fix automatically
                    if debug_mode:
                        print(f"Empty BAAB found: Kitaab {kitaab['number']}, Baab {baab['number']}: {baab['title'][:50]}...")
            
            # Check sub-baabs and hadiths in the baab context
            for ctx_idx, ctx_item in enumerate(baab['context']):
                if isinstance(ctx_item, dict) and 'context' in ctx_item:
                    # This is a sub-baab or hadith
                    if len(ctx_item['context']) == 0 and debug_mode:
                        # This is an empty sub-structure
                        item_type = "SUB-BAAB" if 'number' in ctx_item else "HADITH"
                        number = ctx_item.get('number', ctx_item.get('hadith_number', 'unknown'))
                        print(f"Empty {item_type} found: Kitaab {kitaab['number']}, Baab {baab['number']}, {item_type} {number}")
    
    if debug_mode:
        print(f"Post-processing complete: {empty_baabs}/{total_baabs} baabs are empty ({empty_baabs/total_baabs*100:.1f}%)")
    
    return document_structure

# Main execution
if __name__ == "__main__":
    try:
        # Load the JSON data from test.json
        print(f"Loading JSON data from {input_file}...")
        input_data = parse_json_input(input_file)

        # Flatten the document for processing
        document_flat = flatten_document(input_data)

        # Save a sample of the flattened document for debugging
        if debug_mode:
            try:
                sample_size = min(100, len(document_flat))
                with open('flattened_sample.json', 'w', encoding='utf-8') as f:
                    json.dump(document_flat[:sample_size], f, ensure_ascii=False, indent=2)
                print(f"Saved sample of {sample_size} flattened items to flattened_sample.json")
            except Exception as e:
                print(f"Could not save sample: {e}")

        # Process the flattened document into a structured hierarchy
        document_structure = process_structure(document_flat)
        
        # Post-process to check for and fix issues
        document_structure = post_process_structure(document_structure)

        # Save the output
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(document_structure, f, ensure_ascii=False, indent=2)
        print(f"✅ Hadith structure saved to {output_file}")
        
        # Print statistics about the extraction
        num_kitaabs = len(document_structure['kitaabs'])
        total_baabs = sum(len(kitaab['baabs']) for kitaab in document_structure['kitaabs'])
        print(f"Extracted {num_kitaabs} Kitaabs and {total_baabs} Baabs in total.")
        
        # Count contexts that are not empty
        non_empty_contexts = 0
        total_contexts = 0
        
        for kitaab in document_structure['kitaabs']:
            for baab in kitaab['baabs']:
                total_contexts += 1
                if len(baab['context']) > 0:
                    non_empty_contexts += 1
                    
                # Also check sub-baabs and hadiths in contexts
                for item in baab['context']:
                    if isinstance(item, dict) and 'context' in item:
                        total_contexts += 1
                        if len(item['context']) > 0:
                            non_empty_contexts += 1
        
        print(f"Non-empty contexts: {non_empty_contexts}/{total_contexts} ({non_empty_contexts/total_contexts*100:.1f}% filled)")
        
    except Exception as e:
        import traceback
        print(f"Error processing file: {e}")
        print(traceback.format_exc())
        sys.exit(1)