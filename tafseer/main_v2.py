import re
import json
import os

# Configuration - set these values as needed
input_file = "test.json"  # Changed to test.json as requested
output_file = 'processed_output-1.json'
# Add debug mode to print extra information during processing
debug_mode = True  # Set to False for production

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
    return re.match(r'^\s*(\d+[\s*–\-.\)]+\s*)?باب', text)

def extract_hadith_number(text):
    if not isinstance(text, str):
        return None
    match1 = re.match(r'^\s*(\d+)\s*[-–\.\)]', text)
    match2 = re.search(r'\[\s*الحديث\s*(\d+)\s*[-–\.]', text)
    if match1:
        return int(match1.group(1))
    elif match2:
        return int(match2.group(1))
    else:
        return None

# Function to parse JSON input
def parse_json_input(input_file):
    try:
        # Check file size before attempting to read
        file_size_mb = os.path.getsize(input_file) / (1024 * 1024)
        print(f"Input file size: {file_size_mb:.2f} MB")
        
        with open(input_file, 'r', encoding="utf-8") as f:
            data = json.load(f)
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

# Function to handle different possible JSON structures
def flatten_document(input_data):
    document_flat = []
    position_counter = 0
    
    print("Flattening document structure...")
    found_structure = False
    
    # Try to detect and handle different JSON structures
    
    # Structure 1: Pages with text content
    if 'pages' in input_data:
        print("Processing 'pages' structure...")
        found_structure = True
        for page_idx, page in enumerate(input_data['pages']):
            # Handle page text
            page_text = page.get('text', '')
            if page_text:
                # Split the page text into lines or paragraphs
                lines = page_text.split('\n')
                for line in lines:
                    if line.strip():
                        item = {
                            'element': None,
                            'text': line.strip(),
                            'type': 'p',  # Assuming all lines are paragraphs
                            'data_type': None,
                            'id': '',
                            'html': line.strip(),
                            'page_idx': page_idx,
                            'position': position_counter
                        }
                        document_flat.append(item)
                        position_counter += 1
            
            # Check for span/heading elements in the page
            if isinstance(page_text, str) and '<span data-type="title"' in page_text:
                # Extract titles using regex
                title_matches = re.finditer(r'<span data-type="title" id=([^>]+)>([^<]+)</span>', page_text)
                for match in title_matches:
                    title_id = match.group(1)
                    title_text = match.group(2)
                    item = {
                        'element': None,
                        'text': title_text.strip(),
                        'type': 'p',
                        'data_type': 'title',
                        'id': title_id,
                        'html': match.group(0),
                        'page_idx': page_idx,
                        'position': position_counter
                    }
                    document_flat.append(item)
                    position_counter += 1
            
            # Handle page elements if they exist
            elements = page.get('elements', [])
            for element in elements:
                if element.get('text') and element.get('text').strip():
                    item = {
                        'element': element.get('type'),
                        'text': element.get('text', '').strip(),
                        'type': element.get('type', 'p'),
                        'data_type': element.get('data-type'),
                        'id': element.get('id', ''),
                        'html': element.get('html', element.get('text', '')),
                        'page_idx': page_idx,
                        'position': position_counter
                    }
                    document_flat.append(item)
                    position_counter += 1
    
    # Structure 2: Direct content structure
    elif 'content' in input_data:
        print("Processing 'content' structure...")
        found_structure = True
        content = input_data['content']
        
        if isinstance(content, list):
            for idx, item in enumerate(content):
                if isinstance(item, dict):
                    flat_item = {
                        'element': item.get('type'),
                        'text': item.get('text', '').strip(),
                        'type': item.get('type', 'p'),
                        'data_type': item.get('data-type'),
                        'id': item.get('id', ''),
                        'html': item.get('html', item.get('text', '')),
                        'page_idx': item.get('page', 0),
                        'position': position_counter
                    }
                    document_flat.append(flat_item)
                    position_counter += 1
                elif isinstance(item, str) and item.strip():
                    flat_item = {
                        'element': None,
                        'text': item.strip(),
                        'type': 'p',
                        'data_type': None,
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
                    flat_item = {
                        'element': item.get('type'),
                        'text': text.strip(),
                        'type': item.get('type', 'p'),
                        'data_type': item.get('data-type'),
                        'id': item.get('id', ''),
                        'html': item.get('html', text),
                        'page_idx': item.get('page', 0),
                        'position': position_counter
                    }
                    document_flat.append(flat_item)
                    position_counter += 1
                    
    # Structure 4: Direct text keys in the document
    elif 'text' in input_data and isinstance(input_data['text'], str):
        print("Processing direct text in root...")
        found_structure = True
        lines = input_data['text'].split('\n')
        for line in lines:
            if line.strip():
                item = {
                    'element': None,
                    'text': line.strip(),
                    'type': 'p',
                    'data_type': None,
                    'id': '',
                    'html': line.strip(),
                    'page_idx': 0,
                    'position': position_counter
                }
                document_flat.append(item)
                position_counter += 1
    
    # For headings in indexes
    if 'indexes' in input_data and 'headings' in input_data['indexes']:
        print("Processing 'indexes.headings' structure...")
        found_structure = True
        for heading_idx, heading in enumerate(input_data['indexes']['headings']):
            title = heading.get('title', '')
            if title:
                item = {
                    'element': None,
                    'text': title,
                    'type': 'p',
                    'data_type': 'title',
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
                    item = {
                        'element': obj.get('type', obj.get('element')),
                        'text': obj['text'].strip(),
                        'type': obj.get('type', 'p'),
                        'data_type': obj.get('data-type', obj.get('dataType')),
                        'id': obj.get('id', ''),
                        'html': obj.get('html', obj['text'].strip()),
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
                item = {
                    'element': None,
                    'text': obj.strip(),
                    'type': 'p',
                    'data_type': None,
                    'id': '',
                    'html': obj.strip(),
                    'page_idx': 0,
                    'position': position_counter,
                    'path': path
                }
                document_flat.append(item)
                position_counter += 1
        
        extract_text_recursive(input_data)
    
    print(f"Flattened document contains {len(document_flat)} items.")
    
    # Sort by position to maintain order
    document_flat.sort(key=lambda x: x['position'])
    
    return document_flat

# Load the JSON data
print(f"Loading JSON data from {input_file}...")
input_data = parse_json_input(input_file)

# Flatten the document for processing
document_flat = flatten_document(input_data)

# Initialize structure
document_structure = {"kitaabs": []}
current_kitaab = None
current_baab = None
current_baab_context = [] 
current_context_list = None 
current_sub_baab = None 
current_hadith = None 

# Save a sample of the flattened document for debugging
if debug_mode:
    try:
        sample_size = min(100, len(document_flat))
        with open('flattened_sample.json', 'w', encoding='utf-8') as f:
            json.dump(document_flat[:sample_size], f, ensure_ascii=False, indent=2)
        print(f"Saved sample of {sample_size} flattened items to flattened_sample.json")
    except Exception as e:
        print(f"Could not save sample: {e}")

# Process each item sequentially from the ordered document_flat using an index
print("Starting structure processing...")
i = 0
# Track content that doesn't belong to any structure
unknown_content = []

while i < len(document_flat):
    item = document_flat[i]
    text = remove_diacritics(item.get('text', ''))
   
    # --- Kitaab Detection ---
    # Multiple patterns for Kitaab detection - more flexible
    is_kitaab = False
    
    # Standard title with kitaab pattern
    if item.get('data_type') == 'title' and re.match(r'^\s*(\d+[\s*–\-.\)]+\s*)?كتاب', text):
        is_kitaab = True
    
    # Alternative kitaab detection for non-title items starting with kitaab
    elif re.match(r'^\s*(\d+[\s*–\-.\)]+\s*)?كتاب', text) and text.strip().startswith('كتاب'):
        is_kitaab = True
    
    # Additional pattern for chapter titles
    elif re.search(r'كتاب\s+[^\d\s]+', text, re.UNICODE) and len(text.strip()) < 100:
        is_kitaab = True

    if is_kitaab:
        if debug_mode:
            print(f"--- Detected KITAAB: {item['text'][:80]} ---")

        # Close previous hadith if active (its content is already added)
        if current_hadith:
            if debug_mode:
                print(f"  Closed previous HADITH ({current_hadith.get('hadith_number', 'N/A')})")
            current_hadith = None # Reset hadith state

        # Close previous sub-baab if active (its content is already added)
        if current_sub_baab:
            if debug_mode:
                print(f"  Closed previous SUB-BAAB ({current_sub_baab.get('number', 'N/A')})")
            current_sub_baab = None # Reset sub-baab state

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
            # Add any unknown content to the kitaab if it exists
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

    # --- Baab Detection ---
    # Multiple patterns for Baab detection - more flexible
    is_baab = is_baab_pattern(text)
    baab_condition = (item.get('data_type') == 'title' and is_baab) or \
                     (current_kitaab and item['type'] == 'p' and is_baab)
                     
    # Additional pattern for section headers
    if not baab_condition and current_kitaab and re.search(r'باب\s+[^\d\s]+', text, re.UNICODE) and len(text.strip()) < 100:
        baab_condition = True

    if baab_condition:
        if not current_kitaab:
            if debug_mode:
                print(f"Warning: Detected a potential BAAB pattern ('{item['text'][:80]}...') but no current KITAAB is active.")
            # Store this as unknown content
            unknown_content.append(item['text'].strip())
            i += 1 
            continue 
        else:
            if debug_mode:
                print(f"--- Detected BAAB: {item['text'][:80]} --- (Item type: {item['type']}, data-type: {item.get('data-type')})")

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

        # Close previous hadith if active (its content is already added)
        if current_hadith:
            if debug_mode:
                print(f"  Closed previous HADITH ({current_hadith.get('hadith_number', 'N/A')})")
            current_hadith = None # Reset hadith state

        # Close the previous sub-baab if one was active
        if current_sub_baab:
            if debug_mode:
                print(f"  Closed previous SUB-BAAB ({current_sub_baab.get('number', 'N/A')})")
            # The closed sub-baab dictionary is already appended to current_baab_context

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
        current_hadith = None # Ensure no hadith is active within the sub-baab title marker

        if debug_mode:
            print(f"  Started new SUB-BAAB: Number={current_sub_baab['number']}, Title='{current_sub_baab['title'][:80]}...'")

        i += 2 # Consume both the number line and the 'باب' line
        continue # Move to the next item

    # --- Hadith Detection ---
    # Check if we are in a Baab (or Sub-Baab) AND the current item is a strict number line
    # AND it's NOT the start of a Sub-Baab marker (checked above)
    is_hadith_marker = False
    hadith_number_match = None
    
    # Standard hadith number detection
    if current_baab and is_strict_number_line(item.get('text', '')):
        hadith_number_match = is_strict_number_line(item.get('text', ''))
        is_hadith_marker = True
    
    # Alternative hadith detection - number followed by hadith text
    elif current_baab and extract_hadith_number(item.get('text', '')):
        hadith_number = extract_hadith_number(item.get('text', ''))
        # Create a match-like object for consistency
        class MatchObj:
            def group(self, n):
                return str(hadith_number)
        hadith_number_match = MatchObj()
        is_hadith_marker = True

    if is_hadith_marker and hadith_number_match:
        hadith_number = int(hadith_number_match.group(1)) # Extract number from the match object
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

    # --- Content Accumulation ---
    # Relaxed criteria: Add text to the current context list if we're in any structured element
    if current_baab or current_kitaab:
        cleaned_text = item.get('text', '').strip()
        if cleaned_text:
            # If we're in a specific context, add it there
            if current_context_list is not None:
                current_context_list.append(cleaned_text) # Append just the string
            # If we're in a kitaab but not yet in a baab
            elif current_kitaab and not current_baab:
                # Create a kitaab-level content field if it doesn't exist
                if 'content' not in current_kitaab:
                    current_kitaab['content'] = []
                current_kitaab['content'].append(cleaned_text)
            else:
                # Fallback: add to unknown content
                unknown_content.append(cleaned_text)
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

# Close the very last hadith if one was open. Its content is already in its context list.
if current_hadith:
    print(f"  Closed final HADITH ({current_hadith.get('hadith_number', 'N/A')})")

# Close the very last sub-baab if one was open. Its content is already in its context.
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

# Save output
try:
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
    print(f"Error saving JSON file: {e}")