import json
from typing import List, Dict, Any
import re
import os
from pathlib import Path

def clean_text(text: str) -> str:
    """Clean the text by removing unnecessary characters and normalizing whitespace."""
    # Remove special characters and normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def count_tokens(text: str) -> int:
    """Count the number of tokens in the text (simple word count for now)."""
    return len(text.split())

def create_chunks(data: Dict[str, Any], book_transliteration: str) -> List[Dict[str, Any]]:
    """Create chunks from the JSON data according to the specified structure."""
    chunks = []
    
    # Process headings and pages
    headings = data.get('headings', [])
    pages = data.get('pages', [])
    
    # Create a mapping of page numbers to their content
    page_content = {}
    for page in pages:
        vol = page.get('vol')
        page_num = page.get('page')
        if vol and page_num:
            key = f"{vol}_{page_num}"
            page_content[key] = page.get('text', '')
    
    # Process each heading and create chunks
    for heading in headings:
        title = heading.get('title', '')
        vol = heading.get('page', {}).get('vol')
        page_num = heading.get('page', {}).get('page')
        
        if vol and page_num:
            key = f"{vol}_{page_num}"
            text = page_content.get(key, '')
            
            chunk = {
                "book_transliteration": book_transliteration,
                "book_slug": "N/A",
                "text": clean_text(text),
                "vol": vol,
                "page": page_num,
                "title": title,
                "tokens": count_tokens(text)
            }
            chunks.append(chunk)
    
    return chunks

def process_json_file(input_file: str, output_file: str) -> bool:
    """Process the input JSON file and write the chunks to the output file."""
    try:
        # Read the input JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract book transliteration from the JSON data
        book_transliteration = data.get('transliteration', '')
        if not book_transliteration:
            print(f"Warning: Book transliteration not found in {input_file}")
            return False
        
        # Create chunks
        chunks = create_chunks(data, book_transliteration)
        
        # Write the output JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
            
        return True
        
    except Exception as e:
        print(f"Error processing file {input_file}: {str(e)}")
        return False

def process_all_json_files(input_dir: str, output_dir: str):
    """Process all JSON files in the input directory and save results to output directory."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all JSON files in the input directory
    json_files = list(Path(input_dir).glob('*.json'))
    total_files = len(json_files)
    
    if total_files == 0:
        print(f"No JSON files found in {input_dir}")
        return
    
    print(f"Found {total_files} JSON files to process")
    print("-" * 50)
    
    # Process each file
    successful = 0
    failed = 0
    
    for i, json_file in enumerate(json_files, 1):
        print(f"\nProcessing file {i}/{total_files}: {json_file.name}")
        
        # Create output filename
        output_filename = f"{json_file.stem}--chunked.json"
        output_path = os.path.join(output_dir, output_filename)
        
        # Process the file
        if process_json_file(str(json_file), output_path):
            successful += 1
            print(f"✓ Successfully processed {json_file.name}")
            print(f"  Output saved to: {output_path}")
        else:
            failed += 1
            print(f"✗ Failed to process {json_file.name}")
        
        print("-" * 50)
    
    # Print summary
    print("\nProcessing Summary:")
    print(f"Total files processed: {total_files}")
    print(f"Successfully processed: {successful}")
    print(f"Failed to process: {failed}")

if __name__ == "__main__":
    # Define input and output directories
    input_dir = "tafsir_books"
    output_dir = "chunked_output"
    
    process_all_json_files(input_dir, output_dir)