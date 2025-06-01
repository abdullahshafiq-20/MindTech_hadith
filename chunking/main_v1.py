import json
from typing import List, Dict, Any, Tuple
import re
import os
from pathlib import Path
from bs4 import BeautifulSoup
import difflib
from transformers import AutoTokenizer
from tqdm import tqdm
import logging

# Set up logging
logging.basicConfig(level=logging.WARNING)  # Reduced logging level
logger = logging.getLogger(__name__)

# Initialize the tokenizer without special tokens
try:
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    # Disable special tokens
    tokenizer.add_special_tokens = False
except Exception as e:
    logger.error(f"Failed to initialize tokenizer: {str(e)}")
    raise

def clean_text(text: str) -> str:
    """Clean the text by removing HTML tags and normalizing whitespace."""
    # Remove HTML tags using BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text()
    
    # Remove any remaining HTML-like patterns
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove data-type="title" content
    text = re.sub(r'\[.*?\]', '', text)  # Remove content in square brackets
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def remove_title_from_text(text: str, title: str) -> str:
    """Remove the title from the text if it appears at the beginning."""
    if not title:  # If title is None or empty
        return text
        
    # Clean both text and title
    clean_title = clean_text(title)
    
    # If the text starts with the title, remove it
    if text.startswith(clean_title):
        text = text[len(clean_title):].strip()
    
    return text

def count_tokens(text: str) -> int:
    """Count the number of tokens using the tokenizer."""
    try:
        return len(tokenizer.encode(text, add_special_tokens=False))
    except Exception as e:
        return 0

def create_overlapping_chunks(text: str, max_tokens: int = 1024, overlap: int = 100) -> List[Tuple[str, int, int]]:
    """
    Create overlapping chunks from text based on token length.
    Ensures no chunk exceeds max_tokens while trying to maintain semantic boundaries.
    Returns list of tuples containing (chunk_text, start_token, end_token)
    """
    try:
        # First encode the entire text to get total tokens (without special tokens)
        all_tokens = tokenizer.encode(text, add_special_tokens=False)
        total_tokens = len(all_tokens)
        
        # If text is shorter than max_tokens, return as single chunk
        if total_tokens <= max_tokens:
            return [(text, 0, total_tokens)]
        
        # Print overlapping case message
        print(f"OVERLAPPING CASE: Text has {total_tokens} tokens, creating overlapping chunks...")
        
        chunks = []
        start_idx = 0
        
        while start_idx < total_tokens:
            # Calculate end index for this chunk
            end_idx = min(start_idx + max_tokens, total_tokens)
            
            # Get the chunk tokens
            chunk_tokens = all_tokens[start_idx:end_idx]
            
            # Decode the chunk without special tokens
            chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            
            # Try to find a better break point if we're not at the end
            if end_idx < total_tokens:
                # Look for sentence endings or paragraph breaks in the last 100 tokens
                lookback = min(100, len(chunk_tokens))
                
                for i in range(lookback, 0, -1):
                    # Check for common sentence endings in Arabic
                    if any(chunk_text[-i:].strip().endswith(end) for end in ['۔', '!', '?', '.', '،', '\n']):
                        # Adjust the chunk to end at this point
                        chunk_text = chunk_text[:-i].strip()
                        # Recalculate end_idx based on the new chunk text
                        new_tokens = tokenizer.encode(chunk_text, add_special_tokens=False)
                        end_idx = start_idx + len(new_tokens)
                        break
            
            # Add the chunk
            chunks.append((chunk_text, start_idx, end_idx))
            
            # Move start index for next chunk, accounting for overlap
            start_idx = end_idx - overlap
            
            # Safety check to prevent infinite loops
            if start_idx >= total_tokens - overlap:
                break
        
        print(f"Created {len(chunks)} overlapping chunks")
        return chunks
        
    except Exception as e:
        return [(text, 0, 0)]

def verify_text_content(original_text: str, chunked_text: str, title: str) -> Dict[str, Any]:
    """
    Verify that the chunked text preserves the essential content from the original text.
    Returns a dictionary with verification results.
    """
    # Clean both texts
    clean_original = clean_text(original_text)
    clean_chunked = clean_text(chunked_text)
    
    # Remove title from both texts for comparison
    clean_original = remove_title_from_text(clean_original, title)
    clean_chunked = remove_title_from_text(clean_chunked, title)
    
    # Calculate similarity ratio
    similarity = difflib.SequenceMatcher(None, clean_original, clean_chunked).ratio()
    
    # Get differences
    diff = list(difflib.unified_diff(
        clean_original.splitlines(),
        clean_chunked.splitlines(),
        lineterm=''
    ))
    
    # Check for significant content loss
    original_words = set(clean_original.split())
    chunked_words = set(clean_chunked.split())
    missing_words = original_words - chunked_words
    extra_words = chunked_words - original_words
    
    verification_result = {
        "similarity_ratio": similarity,
        "has_differences": len(diff) > 0,
        "missing_words": list(missing_words),
        "extra_words": list(extra_words),
        "diff_count": len(diff),
        "is_valid": similarity > 0.95 and len(missing_words) < 10  # Thresholds can be adjusted
    }
    
    return verification_result

def create_chunks(data: Dict[str, Any], book_transliteration: str) -> List[Dict[str, Any]]:
    """Create chunks from the JSON data according to the specified structure."""
    chunks = []
    verification_results = []
    
    try:
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
        
        # Process pages with headings
        processed_pages = set()
        for heading in headings:
            title = heading.get('title')
            vol = heading.get('page', {}).get('vol')
            page_num = heading.get('page', {}).get('page')
            
            if vol and page_num:
                key = f"{vol}_{page_num}"
                processed_pages.add(key)
                original_text = page_content.get(key, '')
                
                # Clean the text and remove the title if it appears
                cleaned_text = clean_text(original_text)
                cleaned_text = remove_title_from_text(cleaned_text, title)
                
                # Create overlapping chunks
                text_chunks = create_overlapping_chunks(cleaned_text, max_tokens=1024, overlap=100)
                
                # Create chunks with metadata
                for chunk_text, start_token, end_token in text_chunks:
                    chunk = {
                        "book_transliteration": book_transliteration,
                        "book_slug": "N/A",
                        "text": chunk_text,
                        "vol": vol,
                        "page": page_num,
                        "title": title,
                        "tokens": end_token - start_token
                    }
                    chunks.append(chunk)
                
                # Verify the text content
                verification = verify_text_content(original_text, cleaned_text, title)
                verification_results.append({
                    "vol": vol,
                    "page": page_num,
                    "title": title,
                    "verification": verification
                })
        
        # Process remaining pages without headings
        remaining_pages = [p for p in pages if f"{p.get('vol')}_{p.get('page')}" not in processed_pages]
        
        for page in remaining_pages:
            vol = page.get('vol')
            page_num = page.get('page')
            if vol and page_num:
                original_text = page.get('text', '')
                cleaned_text = clean_text(original_text)
                
                # Create chunks for current page
                text_chunks = create_overlapping_chunks(cleaned_text, max_tokens=1024, overlap=100)
                
                # Create chunks with metadata
                for chunk_text, start_token, end_token in text_chunks:
                    chunk = {
                        "book_transliteration": book_transliteration,
                        "book_slug": "N/A",
                        "text": chunk_text,
                        "vol": vol,
                        "page": page_num,
                        "title": None,
                        "tokens": end_token - start_token
                    }
                    chunks.append(chunk)
                
                # Verify the text content
                verification = verify_text_content(original_text, cleaned_text, None)
                verification_results.append({
                    "vol": vol,
                    "page": page_num,
                    "title": None,
                    "verification": verification
                })
        
        return chunks, verification_results
        
    except Exception as e:
        logger.error(f"Error in create_chunks: {str(e)}")
        raise

def process_json_file(input_file: str, output_dir: str) -> bool:
    """Process the input JSON file and write the chunks to the output file."""
    try:
        print(f"Processing file: {os.path.basename(input_file)}")
        
        # Read the input JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract book transliteration from the JSON data
        book_transliteration = data.get('transliteration', '')
        if not book_transliteration:
            return False
        
        # Create chunks and get verification results
        chunks, verification_results = create_chunks(data, book_transliteration)
        
        # Create output filenames
        input_filename = Path(input_file).stem
        chunked_output_file = os.path.join(output_dir, 'chunks', f"{input_filename}--chunked.json")
        verification_output_file = os.path.join(output_dir, 'verification', f"{input_filename}--verification.json")
        
        # Create subdirectories if they don't exist
        os.makedirs(os.path.dirname(chunked_output_file), exist_ok=True)
        os.makedirs(os.path.dirname(verification_output_file), exist_ok=True)
        
        # Write the chunked output JSON file
        with open(chunked_output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        # Write verification results to a separate file
        with open(verification_output_file, 'w', encoding='utf-8') as f:
            json.dump(verification_results, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        print(f"Error processing file {input_file}: {str(e)}")
        return False

def process_all_json_files(input_dir: str, output_dir: str):
    """Process all JSON files in the input directory and save results to output directory."""
    try:
        # Create main output directory and subdirectories
        os.makedirs(os.path.join(output_dir, 'chunks'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'verification'), exist_ok=True)
        
        # Get all JSON files in the input directory
        json_files = list(Path(input_dir).glob('*.json'))
        total_files = len(json_files)
        
        if total_files == 0:
            print(f"No JSON files found in {input_dir}")
            return
        
        # Process each file with progress bar
        successful = 0
        failed = 0
        
        for json_file in tqdm(json_files, desc="Processing files"):
            if process_json_file(str(json_file), output_dir):
                successful += 1
            else:
                failed += 1
        
        print(f"\nProcessing completed: {successful}/{total_files} files successful")
        
    except Exception as e:
        print(f"Error in processing: {str(e)}")

if __name__ == "__main__":
    # Define input and output directories
    input_dir = "tafsir_books"
    output_dir = "chunked_output"
    
    process_all_json_files(input_dir, output_dir)