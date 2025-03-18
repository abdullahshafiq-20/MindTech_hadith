import json
import os
import re

def load_json_file(file_path):
    """Load JSON data from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return None

def save_json_file(data, file_path):
    """Save JSON data to file with proper formatting"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved to {file_path}")
        return True
    except Exception as e:
        print(f"Error saving to {file_path}: {str(e)}")
        return False

def extract_names_from_text(text):
    """Extract potential narrator names from Arabic text"""
    # Pattern for common narrator name prefixes like "حدثنا", "أخبرنا", "عن", etc.
    narrator_pattern = r'(حدثنا|أخبرنا|سمعت|عن|قال|روى)\s+([^\s]+\s+[^\s]+(\s+[^\s]+)?)'
    matches = re.findall(narrator_pattern, text)
    names = [match[1].strip() for match in matches]
    return names

def normalize_arabic_text(text):
    """Normalize Arabic text for better matching"""
    if not text:
        return ""
    # Remove diacritical marks (tashkeel)
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    # Normalize alef forms
    text = re.sub(r'[إأآا]', 'ا', text)
    # Normalize yaa forms
    text = re.sub(r'[يى]', 'ي', text)
    # Normalize taa marbouta
    text = text.replace('ة', 'ه')
    return text.strip()

def name_similarity(name1, name2):
    """Calculate similarity between two Arabic names"""
    name1 = normalize_arabic_text(name1)
    name2 = normalize_arabic_text(name2)
    
    # If either name contains the other, consider a match
    if name1 in name2 or name2 in name1:
        return True
        
    # Split names into parts and check for partial matches
    parts1 = name1.split()
    parts2 = name2.split()
    
    # If both names have at least 2 matching parts, consider a match
    matching_parts = 0
    for part1 in parts1:
        if len(part1) < 3:  # Skip very short parts
            continue
        for part2 in parts2:
            if len(part2) < 3:  # Skip very short parts
                continue
            if part1 == part2 or part1 in part2 or part2 in part1:
                matching_parts += 1
                break
    
    # Return true if at least 2 parts match or if more than 50% of parts match
    min_required = min(len(parts1), len(parts2))
    min_required = 2 if min_required > 2 else min_required
    
    return matching_parts >= min_required

def validate_narrator_data(original_text, narrator_data):
    """Validate narrator data against original text"""
    validation_results = {}
    
    # Check if narrator name appears in text
    narrator_name = narrator_data.get("narrator", "")
    full_name = narrator_data.get("full_name", "")
    aliases = narrator_data.get("aliases", [])
    
    # Combined list of all name forms
    all_name_forms = [narrator_name, full_name] + aliases
    all_name_forms = [name for name in all_name_forms if name and name != "Unknown"]
    
    # Check if any name form appears in text
    name_found = False
    for name in all_name_forms:
        if normalize_arabic_text(name) in normalize_arabic_text(original_text):
            name_found = True
            break
    
    # Extract potential names from text and check for similarities
    if not name_found:
        extracted_names = extract_names_from_text(original_text)
        for extracted_name in extracted_names:
            for name in all_name_forms:
                if name_similarity(extracted_name, name):
                    name_found = True
                    break
            if name_found:
                break
    
    validation_results["name_validated"] = name_found
    
    # Check for teacher/student relations
    teachers = narrator_data.get("teachers", [])
    students = narrator_data.get("students", [])
    
    # Check if teacher names appear in text
    teachers_validated = 0
    for teacher in teachers:
        teacher_name = teacher.get("name", "")
        if teacher_name and teacher_name != "Unknown":
            if normalize_arabic_text(teacher_name) in normalize_arabic_text(original_text):
                teachers_validated += 1
                continue
                
            # Check teacher name similarity
            for extracted_name in extract_names_from_text(original_text):
                if name_similarity(extracted_name, teacher_name):
                    teachers_validated += 1
                    break
    
    validation_results["teachers_validated"] = teachers_validated > 0 if teachers else None
    
    # Check if student names appear in text
    students_validated = 0
    for student in students:
        student_name = student.get("name", "")
        if student_name and student_name != "Unknown":
            if normalize_arabic_text(student_name) in normalize_arabic_text(original_text):
                students_validated += 1
                continue
                
            # Check student name similarity
            for extracted_name in extract_names_from_text(original_text):
                if name_similarity(extracted_name, student_name):
                    students_validated += 1
                    break
    
    validation_results["students_validated"] = students_validated > 0 if students else None
    
    # Overall validation result
    validation_results["is_validated"] = name_found and (
        (teachers_validated > 0 if teachers else True) or 
        (students_validated > 0 if students else True)
    )
    
    return validation_results

def validate_narrators(output_json_path, narrators_json_path, validated_output_path=None):
    """Validate narrator data against original text and add validation field"""
    # Load JSON files
    output_data = load_json_file(output_json_path)
    narrators_data = load_json_file(narrators_json_path)
    
    if not output_data or not narrators_data:
        print("Failed to load one or both JSON files")
        return False
    
    if "pages" not in output_data or "narrators" not in narrators_data:
        print("Invalid JSON structure in one or both files")
        return False
    
    # Create a dictionary of pages by page number for easy access
    pages_dict = {}
    for page in output_data["pages"]:
        page_num = page.get("page_number")
        if page_num:
            # Store page number as both integer and string to handle different formats
            pages_dict[page_num] = page.get("text", "")
            pages_dict[str(page_num)] = page.get("text", "")
    
    print(f"Loaded {len(pages_dict)//2} pages from {output_json_path}")
    print(f"Page numbers available: {sorted([k for k in pages_dict.keys() if not isinstance(k, str)])[:10]}... (showing first 10)")
    
    # Validate each narrator
    validation_stats = {"total": 0, "validated": 0, "failed": 0}
    
    for idx, narrator in enumerate(narrators_data["narrators"]):
        validation_stats["total"] += 1
        
        # Print progress every 10 narrators
        if idx % 10 == 0:
            print(f"Processing narrator {idx+1}/{len(narrators_data['narrators'])}...")
        
        # Get page information 
        # Check for different possible page range field names
        page_range = None
        for field in ["page_range", "page_from", "source_page", "pages"]:
            if field in narrator and narrator[field]:
                page_range = narrator[field]
                break
        
        if not page_range:
            print(f"No page information found for narrator: {narrator.get('narrator', 'Unknown')}")
            narrator["validation_details"] = {"is_validated": False, "reason": "No page information found"}
            narrator["is_validated"] = False
            validation_stats["failed"] += 1
            continue
        
        # Handle different page range formats
        start_page = None
        end_page = None
        
        # Format: "1-5" (range)
        if isinstance(page_range, str) and "-" in page_range:
            try:
                parts = page_range.split("-")
                start_page = parts[0].strip()
                end_page = parts[1].strip()
                
                # Try to convert to integers if possible
                if start_page.isdigit():
                    start_page = int(start_page)
                if end_page.isdigit():
                    end_page = int(end_page)
            except Exception as e:
                print(f"Error parsing page range '{page_range}': {str(e)}")
        # Format: Single page (string or int)
        else:
            start_page = page_range
            end_page = page_range
            
            # Try to convert to integers if possible
            if isinstance(start_page, str) and start_page.isdigit():
                start_page = int(start_page)
                end_page = start_page
        
        # Combine text from pages in range
        original_text = ""
        pages_found = []
        
        if isinstance(start_page, int) and isinstance(end_page, int):
            # Numeric range
            for page_num in range(start_page, end_page + 1):
                if page_num in pages_dict:
                    original_text += pages_dict[page_num] + "\n"
                    pages_found.append(page_num)
                elif str(page_num) in pages_dict:
                    original_text += pages_dict[str(page_num)] + "\n"
                    pages_found.append(page_num)
        else:
            # Non-numeric - try both the original value and as string
            if start_page in pages_dict:
                original_text += pages_dict[start_page] + "\n"
                pages_found.append(start_page)
            
            if end_page in pages_dict and end_page != start_page:
                original_text += pages_dict[end_page] + "\n"
                pages_found.append(end_page)
        
        if not original_text:
            print(f"No page content found for range: {page_range}")
            if isinstance(start_page, int) and isinstance(end_page, int):
                print(f"Looking for pages {start_page} to {end_page}")
            else:
                print(f"Looking for page identifiers: {start_page}, {end_page}")
            
            # Try matching with flexible page numbering - look for pages with similar numbers
            nearby_pages = []
            if isinstance(start_page, int):
                for offset in range(-5, 6):  # Check ±5 pages
                    check_page = start_page + offset
                    if check_page in pages_dict:
                        nearby_pages.append(check_page)
            
            if nearby_pages:
                print(f"Found nearby pages that might match: {nearby_pages}")
            
            narrator["validation_details"] = {"is_validated": False, "reason": f"No page content found for {page_range}"}
            narrator["is_validated"] = False
            validation_stats["failed"] += 1
            continue
        
        print(f"Found content on {len(pages_found)} pages for narrator: {narrator.get('narrator', 'Unknown')}")
        
        # Validate narrator against original text
        validation_results = validate_narrator_data(original_text, narrator)
        
        # Add validation results to narrator data
        narrator["is_validated"] = validation_results["is_validated"]
        narrator["validation_details"] = validation_results
        narrator["validation_details"]["pages_found"] = pages_found
        
        if validation_results["is_validated"]:
            validation_stats["validated"] += 1
        else:
            validation_stats["failed"] += 1
    
    # Save validated data
    if validated_output_path is None:
        # Generate output path based on input path
        base_name = os.path.splitext(narrators_json_path)[0]
        validated_output_path = f"{base_name}_validated.json"
    
    success = save_json_file(narrators_data, validated_output_path)
    
    # Print validation statistics
    print("\nValidation Summary:")
    print(f"Total narrators processed: {validation_stats['total']}")
    if validation_stats['total'] > 0:
        print(f"Narrators validated: {validation_stats['validated']} ({validation_stats['validated']/validation_stats['total']*100:.1f}%)")
        print(f"Narrators failed validation: {validation_stats['failed']} ({validation_stats['failed']/validation_stats['total']*100:.1f}%)")
    
    return success

if __name__ == "__main__":
    # Default file paths
    output_json_path = "output/output.json"
    narrators_json_path = "narrators_info_QwenPlus.json"
    validated_output_path = "narrators_info_QwenPlus_validated.json"
    
    # Validate narrators
    validate_narrators(output_json_path, narrators_json_path, validated_output_path)