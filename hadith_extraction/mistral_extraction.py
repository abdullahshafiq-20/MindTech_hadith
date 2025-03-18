import json
import os
import time
import argparse
import google.generativeai as genai
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set the API key for Google Generative AI


# List of API keys to rotate
GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY_1", ""),
    os.getenv("GEMINI_API_KEY_2", "")
]

class GeminiHadithExtractor:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_key_index = 0
        self.api_call_count = 0
        self._configure_api()
    
    def _configure_api(self):
        """Configure the Gemini API with the current API key"""
        current_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=current_key)
        print(f"Using API key index: {self.current_key_index}")
        
        # Initialize the model
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite', generation_config={
            "temperature": 0.3,  # Lower temperature for more focused responses
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 8192,
        })
    
    def _rotate_api_key(self):
        """Rotate to the next API key if needed"""
        self.api_call_count += 1
        if self.api_call_count >= 10:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self.api_call_count = 0
            self._configure_api()
    
    def _clean_markdown(self, markdown: str) -> str:
        """Clean markdown by removing standalone stars and other irrelevant content"""
        # Remove leading stars
        cleaned = markdown.lstrip('*').strip()
        
        # If it's just stars or very short, return empty
        if len(cleaned) < 100 or cleaned.replace('*', '').strip() == '':
            return ''
        
        return cleaned
    
    def call_gemini(self, prompt: str) -> Optional[str]:
        """Make a call to the Gemini API and handle rotation"""
        try:
            # Rotate API key if needed
            self._rotate_api_key()
            
            # Make the API call
            response = self.model.generate_content(prompt)
            
            # Return the text response
            if response:
                content = response.text
                # Debug logging
                print(f"Raw API Response preview: {content[:100]}...")
                return content
            else:
                print("Empty response from Gemini API")
                return None
                
        except Exception as e:
            print(f"Gemini API Error: {str(e)}")
            return None
    
    def extract_hadith_batch(self, markdown_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of markdown entries (2 at a time) to extract hadiths"""
        results = []
        
        # Process in pairs
        for i in range(0, len(markdown_entries), 2):
            batch = markdown_entries[i:i+2]
            batch_result = self._process_markdown_pair(batch)
            if batch_result:
                results.extend(batch_result)
            
            # Small delay to avoid rate limiting
            time.sleep(1)
            
        return results
    
    def _process_markdown_pair(self, markdown_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a pair of markdown entries"""
        # Clean and validate the markdown content
        valid_entries = []
        for entry in markdown_entries:
            cleaned_markdown = self._clean_markdown(entry.get("markdown", ""))
            if cleaned_markdown:
                valid_entries.append({
                    "index": entry.get("index"),
                    "markdown": cleaned_markdown
                })
        
        if not valid_entries:
            return []
        
        # Prepare the prompt with valid entries
        prompt = self._build_prompt(valid_entries)
        
        # Call the API
        response = self.call_gemini(prompt)
        if not response:
            return []
        
        # Parse the response to extract hadiths
        return self._parse_response(response, valid_entries)
    
    def _build_prompt(self, entries: List[Dict[str, Any]]) -> str:
        """Build the prompt for Gemini API"""
        prompt_text = """
        You are a hadith extraction expert. A hadith is a recorded saying, action, or tacit approval of Prophet Muhammad (peace be upon him). 

        Important Hadith Components:
        1. Chain of narration (isnad) - begins with terms like "عن", "حدثنا", "أخبرنا"
        2. Main text (matn) - the actual content
        3. Attribution - references to hadith collections or scholars

        Analyze the following Arabic text and identify any hadiths present. Look for:
        - Direct quotes from the Prophet Muhammad (ﷺ)
        - Narrations with chains of transmitters
        - References to actions or sayings of the Prophet
        - Citations from known hadith collections

        For each hadith found, provide:
        1. The complete hadith text in Arabic (both isnad and matn if present)
        2. The context surrounding the hadith
        3. A brief explanation in English
        4. Whether the hadith appears complete
        5. If incomplete, your best completion from known collections
        6. Whether the hadith includes a chain of narration
        7. The location where the hadith appears

        Important:
        - If NO hadith is found, return ONLY: []
        - Do not provide explanations for non-hadith text
        - Only include verified hadith content
        
        Respond in this exact JSON format:
        [
            {
                "hadith": "The complete Arabic text of the hadith",
                "context": "The specific discussion context where this hadith appears",
                "explanation": "Brief English explanation of the hadith's meaning",
                "is_complete": true/false,
                "completion": "Your completion if incomplete, null if complete",
                "is_narrated": true/false,
                "span": "Page/section reference where found"
            }
        ]

        Here is the text to analyze:
        """
        # Add the content from valid entries
        for i, entry in enumerate(entries):
            prompt_text += f"\n--- TEXT {i+1} (Index: {entry['index']}) ---\n{entry['markdown']}\n"
        
        return prompt_text

    def _parse_response(self, response: str, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse the API response and convert it to the desired output format"""
        try:
            # Find the JSON part in the response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                parsed_data = json.loads(json_str)
                
                # Add source information to each entry
                for item in parsed_data:
                    # Try to match with the original entry
                    for entry in entries:
                        if item.get("span") and str(entry.get("index")) in item.get("span"):
                            item["source_index"] = entry.get("index")
                            break
                
                return parsed_data
            else:
                print("Could not find JSON data in the response")
                return []
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from response: {e}")
            print(f"Response was: {response}")
            return []
        except Exception as e:
            print(f"Unexpected error while parsing response: {e}")
            return []

    def _update_results_file(self, results: List[Dict[str, Any]], output_path: str, 
                            total_pages: int, valid_pages: int):
        """Update the results JSON file with new entries"""
        try:
            # Create initial structure if file doesn't exist
            if not os.path.exists(output_path):
                initial_data = {
                    "total_pages_processed": total_pages,
                    "valid_entries_processed": valid_pages,
                    "hadiths_extracted": 0,
                    "results": []
                }
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, ensure_ascii=False, indent=2)

            # Read existing data
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Update with new results
            data["results"].extend(results)
            data["hadiths_extracted"] = len(data["results"])

            # Write updated data
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"Updated results file with {len(results)} new entries")
            
        except Exception as e:
            print(f"Error updating results file: {e}")

def process_json_file(file_path: str, output_path: str): 
    """Process a JSON file containing markdown entries"""
    extractor = GeminiHadithExtractor(GEMINI_API_KEYS)
    
    # Load the input file
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract pages from the JSON structure
    if isinstance(data, dict) and "pages" in data:
        markdown_entries = data["pages"]
    else:
        print(f"Unexpected JSON format in {file_path}. Expected 'pages' key.")
        return

    # Filter out entries with only image references
    valid_entries = []
    for entry in markdown_entries:
        markdown_content = entry.get("markdown", "")
        if not all(line.startswith("![") for line in markdown_content.split("\n") if line.strip()):
            valid_entries.append(entry)

    total_pages = len(markdown_entries)
    valid_pages = len(valid_entries)

    # Process in smaller batches and update results file incrementally
    batch_size = 2
    for i in range(0, len(valid_entries), batch_size):
        batch = valid_entries[i:i+batch_size]
        batch_results = extractor.extract_hadith_batch(batch)
        
        if batch_results:
            extractor._update_results_file(
                batch_results, 
                output_path,
                total_pages,
                valid_pages
            )
        
        # Small delay between batches
        time.sleep(1)

    print(f"Completed processing {valid_pages} valid entries out of {total_pages} total pages")

if __name__ == "__main__":
    # Get the current directory where the script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define input and output paths relative to current directory
    input_file_path = os.path.join(current_dir, "ocr_output.json")
    output_file_path = os.path.join(current_dir, "data", "new_hadith_extraction_results.json")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file_path)
    os.makedirs(output_dir, exist_ok=True)
    
    # Verify input file exists
    if not os.path.exists(input_file_path):
        print(f"Error: Input file not found at {input_file_path}")
        exit(1)
    
    print(f"Processing input file: {input_file_path}")
    print(f"Output will be saved to: {output_file_path}")
    
    process_json_file(input_file_path, output_file_path)