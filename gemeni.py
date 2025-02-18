import google.generativeai as genai
from google.api_core import exceptions, retry
import json
import time
import os

@retry.Retry(predicate=retry.if_exception_type(
    exceptions.InternalServerError,
    exceptions.TooManyRequests,
    exceptions.ServiceUnavailable
))
def get_narrator_info(pages_text, current_pages):  # Modified to accept page numbers
    genai.configure(api_key="AIzaSyAGMdxQCc8joq2MicuKEHi3spvJR1wSuqM")
    model = genai.GenerativeModel('gemini-1.5-flash-8b', generation_config={
        "temperature": 0.3,  # Lower temperature for more focused responses
        "top_p": 0.8,
        "top_k": 40,
        "max_output_tokens": 8192,
    })
    
    prompt = f"""
    You are an expert in Islamic narrator biographies (علم الرجال). Analyze this Arabic text and extract narrator information.
    Focus ONLY on clear biographical information and teacher-student relationships. Return valid JSON with no additional text.

    Important rules:
    1. Only extract information explicitly stated in the text
    2. Use "Unknown" for missing information
    3. Include Arabic text where available
    4. Focus on main biographical elements and relationships
    5. Look specifically for terms like "روى عن", "حدثنا", "أخبرنا", "سمعت من" for teacher relationships
    6. Look for "روى عنه", "حدث عنه", "أخذ عنه" for student relationships
    
    Text to analyze:
    {pages_text}

    Return strictly in this JSON format:
    {{
        "narrators": [
            {{
                "narrator": "الاسم بالعربية",
                "full_name": "الاسم الكامل مع النسب",
                "aliases": ["الأسماء البديلة"],
                "birth_year": "سنة الولادة الهجرية",
                "death_year": "سنة الوفاة الهجرية",
                "birthplace": "مكان الولادة",
                "primary_locations": ["المدن الرئيسية"],
                "era": "الطبقة (مثل: تابعي، تابع تابعين)",
                "travel_history": ["رحلاته العلمية"],
                "did_travel_for_hadith": "نعم/لا/غير معروف",
                "memory_changes": "تغيرات في حفظه وضبطه",
                "known_tadlis": "نعم/لا/غير معروف",
                "scholarly_reliability": ["درجة الثقة والضبط"],
                "scholarly_evaluations": {{
                    "اسم العالم": "تقييمه وتعليله"
                }},
                "teachers": [
                    {{
                        "name": "اسم الشيخ",
                        "relationship_type": "نوع العلاقة (سماع/إجازة/مناولة)",
                        "notable_narrations": ["أهم المرويات عنه"]
                    }}
                ],
                "students": [
                    {{
                        "name": "اسم التلميذ",
                        "relationship_type": "نوع العلاقة",
                        "notable_narrations": ["أهم المرويات"]
                    }}
                ]
            }}
        ]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"API Error: {str(e)}")
        return None

def clean_json_response(response_text):
    """Clean and validate JSON response"""
    if not response_text:
        return None
        
    # Remove any markdown formatting
    cleaned = response_text.strip()
    if "```" in cleaned:
        cleaned = cleaned.split("```")[1] if "```json" in cleaned else cleaned.split("```")[1]
        cleaned = cleaned.strip()
    
    # Remove any non-JSON text before or after
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}") + 1
    if (start_idx >= 0 and end_idx > 0):
        cleaned = cleaned[start_idx:end_idx]
    
    try:
        return json.loads(cleaned)
    except:
        return None

def load_existing_narrators(output_file):
    """Load existing narrators from file if it exists"""
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("narrators", [])
        except:
            return []
    return []

def save_narrators(narrators, output_file):
    """Save narrators to file with proper formatting"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"narrators": narrators}, f, ensure_ascii=False, indent=2)

def process_json_file(input_file="output/output.json", output_file="narrators_info.json"):
    # Read the input JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Load existing narrators if any
    all_narrators = load_existing_narrators(output_file)
    initial_count = len(all_narrators)
    print(f"Loaded {initial_count} existing narrators")
    
    pages = data['pages']
    
    # Process pages in batches of 2
    batch_size = 3
    
    for i in range(0, len(pages), batch_size):
        batch_pages = pages[i:i + batch_size]
        
        # Get page range for current batch
        start_page = batch_pages[0].get('page_number', str(i+1))
        end_page = batch_pages[-1].get('page_number', str(i+batch_size))
        page_range = f"{start_page}-{end_page}"
        
        # Combine text from batch pages
        combined_text = "\n".join(page['text'] for page in batch_pages)
        
        print(f"\nProcessing pages {page_range}...")
        
        # Get narrator information with page numbers
        narrator_info = get_narrator_info(combined_text, page_range)
        if not narrator_info:
            print(f"No valid response for batch {i//batch_size + 1}")
            continue
            
        print("Raw response received, cleaning...")
        
        # Clean and parse the response
        cleaned_data = clean_json_response(narrator_info)
        if not cleaned_data:
            print("Failed to parse response")
            continue
            
        # Extract and save narrators from response
        if "narrators" in cleaned_data:
            batch_narrators = cleaned_data["narrators"]
            if batch_narrators:
                # Update IDs and page numbers
                next_id = len(all_narrators) + 1
                for narrator in batch_narrators:
                    narrator["narrator_id"] = str(next_id)
                    narrator["page_from"] = page_range
                    next_id += 1
                
                # Add new narrators
                all_narrators.extend(batch_narrators)
                
                # Save after each successful batch
                save_narrators(all_narrators, output_file)
                
                print(f"Added and saved {len(batch_narrators)} narrators from batch")
            else:
                print("No narrators found in batch")
        
        # Add delay between batches
        time.sleep(3)
    
    # Final summary
    final_count = len(all_narrators)
    new_narrators = final_count - initial_count
    print(f"\nProcessing complete:")
    print(f"- Initial narrators: {initial_count}")
    print(f"- New narrators added: {new_narrators}")
    print(f"- Total narrators: {final_count}")
    
    return all_narrators

if __name__ == "__main__":
    narrators = process_json_file()
    print(f"\nScript completed successfully")
