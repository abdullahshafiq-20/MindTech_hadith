import requests
import json
import time
import os 
from google.api_core import retry
from dotenv import load_dotenv


load_dotenv()

# Get API keys from environment variables
OPENROUTER_API_KEYS = [
    os.getenv("OPENROUTER_KEY_1", ""),  # as053266
    os.getenv("OPENROUTER_KEY_2", ""),  # resumeTex
    os.getenv("OPENROUTER_KEY_3", ""),  # hmcadet
    os.getenv("OPENROUTER_KEY_4", ""),  # hmcadet2
    os.getenv("OPENROUTER_KEY_5", ""),  #P
]

# Filter out any empty keys
OPENROUTER_API_KEYS = [key for key in OPENROUTER_API_KEYS if key]

if not OPENROUTER_API_KEYS:
    raise ValueError("No API keys found in .env file. Please add OPENROUTER_KEY_1, OPENROUTER_KEY_2, etc.")


# Keep track of API key usage
api_usage_counter = 0
current_api_index = 0

def get_next_api_key():
    """Rotates through API keys after every 10 calls"""
    global api_usage_counter, current_api_index
    
    # Increment usage counter
    api_usage_counter += 1
    
    # Check if we need to rotate to the next key
    if api_usage_counter > 10:
        current_api_index = (current_api_index + 1) % len(OPENROUTER_API_KEYS)
        api_usage_counter = 1  # Reset counter
        print(f"Rotating to API key #{current_api_index+1}")
    
    return OPENROUTER_API_KEYS[current_api_index]

def get_narrator_info(narrator_data):  # Modified to accept narrator data directly
    """Get narrator information using OpenRouter's model based on already extracted narrator data"""
    
    # Extract relevant narrator information for the prompt
    narrator_name = narrator_data.get('narrator', 'Unknown')
    narrator_content = narrator_data.get('full_text', '')
    page_info = f"Pages {narrator_data.get('start_page', 'Unknown')}-{narrator_data.get('end_page', 'Unknown')}"
    
    prompt = f"""
    You are an expert in Islamic narrator biographies (علم الرجال). Analyze this Arabic narrator information and extract structured biographical details.
    Focus ONLY on clear biographical information and teacher-student relationships. Return valid JSON with no additional text.

    Important rules:
    1. Only extract information explicitly stated in the text
    2. Use "Unknown" for missing information
    3. Include Arabic text where available
    4. Focus on main biographical elements and relationships
    5. Look specifically for terms like "روى عن", "حدثنا", "أخبرنا", "سمعت من" for teacher relationships
    6. Look for "روى عنه", "حدث عنه", "أخذ عنه" for student relationships

    
    Narrator name: {narrator_name}
    Page information: {page_info}
    
    Text to analyze:
    {narrator_content}

    You are required to return the strictly data in this JSON format, make sure to written the only data no more thant that. Here is the format:
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
        # Get the next API key from the rotation
        current_api_key = get_next_api_key()
        
        # Site information
        YOUR_SITE_URL = "https://mindtech-hadith-analyzer.com"
        YOUR_SITE_NAME = "MindTech Hadith Analyzer"
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {current_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": YOUR_SITE_URL,
                "X-Title": YOUR_SITE_NAME,
            },
            data=json.dumps({
                "model": "qwen/qwen2.5-vl-72b-instruct:free", # Using text-only model as we don't need vision capabilities
                # "model": "deepseek/deepseek-r1-distill-llama-70b:free", # Using text-only model as we don't need vision capabilities
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert in Islamic narrator biographies (علم الرجال) that analyzes Arabic text and extracts structured information about narrators."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "top_p": 0.8,
                "max_tokens": 4000
            }),
            timeout=60  # Set reasonable timeout
        )
        
        # Debug info about the API key used
        print(f"Using API key #{current_api_index+1} (call #{api_usage_counter}/10)")
        
        # Handle the response
        if response.status_code == 200:
            response_data = response.json()
            content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
            # Debug logging
            print(f"Raw API Response preview: {content}")
            return content
        else:
            print(f"API Error with key #{current_api_index+1}: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"API Error with key #{current_api_index+1}: {str(e)}")
        return None

def clean_json_response(response_text):
    """Clean and validate JSON response"""
    if not response_text:
        print("Empty response received")
        return None
        
    # Debug logging
    print(f"Response length: {len(response_text)}")
    print(f"Response starts with: {response_text[:50]}...")
    
    # Remove any markdown formatting
    cleaned = response_text.strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        if "```json" in cleaned:
            for i, part in enumerate(parts):
                if part.strip() == "json" or part.strip() == "":
                    # The JSON content should be in the next part
                    if i+1 < len(parts):
                        cleaned = parts[i+1].strip()
                        break
        else:
            # Find a part that looks like JSON
            for part in parts:
                if part.strip().startswith("{") and part.strip().endswith("}"):
                    cleaned = part.strip()
                    break
    
    # Remove any non-JSON text before or after
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}") + 1
    if (start_idx >= 0 and end_idx > 0):
        cleaned = cleaned[start_idx:end_idx]
        print(f"Found JSON from index {start_idx} to {end_idx}")
    else:
        print("Could not locate JSON structure in response")
        return None
    
    try:
        json_data = json.loads(cleaned)
        if "narrators" in json_data:
            print(f"Successfully parsed JSON with {len(json_data['narrators'])} narrators")
        else:
            print("JSON parsed but no 'narrators' key found")
        return json_data
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
        print(f"Problem near: {cleaned[max(0, e.pos-30):min(len(cleaned), e.pos+30)]}")
        return None
    except Exception as e:
        print(f"Unexpected error parsing JSON: {str(e)}")
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

def process_narrators_file(input_file="output/output_narrators.json", output_file="narr_info_1.json"):
    """Process already extracted narrators directly instead of page text"""
    # Read the input JSON file with narrators
    with open(input_file, 'r', encoding='utf-8') as f:
        narrators_data = json.load(f)
    
    # Load existing narrators if any
    all_narrators = load_existing_narrators(output_file)
    initial_count = len(all_narrators)
    print(f"Loaded {initial_count} existing narrators")
    
    # Process narrators in batches of 2
    batch_size = 5
    total_narrators = len(narrators_data)
    
    print(f"Found {total_narrators} narrators to process")
    
    for i in range(0, total_narrators, batch_size):
        batch_narrators = narrators_data[i:i + min(batch_size, total_narrators - i)]
        
        print(f"\nProcessing narrators batch {i//batch_size + 1} ({i+1}-{min(i+batch_size, total_narrators)} of {total_narrators})...")
        
        for narrator_data in batch_narrators:
            narrator_number = narrator_data.get('number', 'Unknown')
            narrator_name = narrator_data.get('narrator', 'Unknown')
            print(f"Processing narrator #{narrator_number}: {narrator_name}")
            
            # Get narrator information directly from narrator data
            print("Calling API...")
            narrator_info = get_narrator_info(narrator_data)
            if not narrator_info:
                print(f"No valid response for narrator {narrator_number}")
                continue
                
            print("Raw response received, cleaning...")
            
            # Clean and parse the response
            cleaned_data = clean_json_response(narrator_info)
            if not cleaned_data:
                print("Failed to parse response")
                # Save the raw response for inspection
                debug_file = f"debug_response_narrator_{narrator_number}.txt"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(narrator_info)
                print(f"Raw response saved to {debug_file} for debugging")
                continue
                
            # Extract and save narrators from response
            if "narrators" in cleaned_data and cleaned_data["narrators"]:
                api_narrator = cleaned_data["narrators"][0]  # Get the first (and should be only) narrator
                
                # Add original data to enriched narrator info
                api_narrator["original_number"] = narrator_number
                api_narrator["original_narrator"] = narrator_name
                api_narrator["original_page_start"] = narrator_data.get('start_page')
                api_narrator["original_page_end"] = narrator_data.get('end_page')
                api_narrator["narrator_id"] = str(len(all_narrators) + 1)
                
                # Add new narrator
                all_narrators.append(api_narrator)
                
                # Save after each successful narrator
                save_narrators(all_narrators, output_file)
                
                print(f"Added and saved narrator {narrator_number}")
            else:
                print("No valid narrator information found in the response")
            
            # Add short delay between API calls for the same batch
            time.sleep(1)
            
        # Add longer delay between batches
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
    narrators = process_narrators_file()
    print(f"\nScript completed successfully")
