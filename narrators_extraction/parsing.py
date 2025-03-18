import argparse
import json
import os
import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import fitz  # PyMuPDF
from tqdm import tqdm

def extract_text_from_page(page):
    """Extract text from a PDF page with special handling for Arabic text."""
    # Get text blocks which preserve better formatting than raw text extraction
    blocks = page.get_text("blocks")
    
    page_text = []
    for block in blocks:
        if block[6] == 0:  # Text blocks have type 0
            text = block[4].strip()
            if text:  # Only add non-empty text blocks
                page_text.append(text)
    
    return "\n".join(page_text)

def process_page_range(pdf_path, start_page, end_page):
    """Process a range of pages from the PDF."""
    results = []
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(start_page, min(end_page, len(doc))):
            page = doc[page_num]
            text = extract_text_from_page(page)
            
            results.append({
                'page_number': page_num + 1,  # 1-based page numbering for output
                'text': text
            })
        
        doc.close()
    except Exception as e:
        print(f"Error processing pages {start_page}-{end_page}: {str(e)}")
    
    return results

def extract_narrators_from_book(book):
    """
    Extract narrators from a book by analyzing the full text across all pages.
    Handles narratives that might be split across multiple pages.
    Ensures consecutive numbering of narrators.
    
    Args:
        book: Book dictionary with pages
        
    Returns:
        list: List of narrator dictionaries
    """
    # First, concatenate all the pages with page markers
    full_text = ""
    page_markers = {}
    
    for page in book['pages']:
        # Mark the position where this page begins in the full text
        page_markers[len(full_text)] = page['page_number']
        full_text += page['text'] + "\n"
    
    expected_number = 1
    found_narrators = {}
    
    # Improved pattern for Arabic narrator format:
    # This pattern matches "{number} - {narrator_name}"
    pattern = r'(\d+)\s*-\s*(\*?)\s*([^\n]+)'
    
    matches = re.finditer(pattern, full_text)
    last_valid_number = 0
    
    for match in matches:
        narrator_num_str = match.group(1).strip()
        has_asterisk = bool(match.group(2))
        narrator_text = match.group(3).strip()
        
        # Skip if the text after the hyphen starts with another number (like "40 - 42")
        if re.match(r'^\d+', narrator_text):
            print(f"Skipping number-number pattern: {narrator_num_str} - {narrator_text}")
            continue
        
        try:
            narrator_num = int(narrator_num_str)
            
            # Strict sequence checking
            # Only accept if it's the expected next number or within a small tolerance
            if narrator_num != expected_number:
                # If far from expected sequence, skip it as likely not a real narrator
                if abs(narrator_num - expected_number) > 2 and narrator_num != 1:  # Allow reset to 1
                    print(f"Skipping out-of-sequence number: {narrator_num_str} - {narrator_text}")
                    continue
                    
                # If it's a duplicate or going backwards significantly, skip
                if narrator_num <= last_valid_number and narrator_num != 1:  # Allow reset to 1
                    print(f"Skipping duplicate or backwards number: {narrator_num_str} - {narrator_text}")
                    continue
                
                print(f"Warning: Expected narrator number {expected_number}, but found {narrator_num}")
            
            # Clean up the narrator text - remove trailing punctuation and special chars
            narrator_text = re.sub(r'[،.؟:!]$', '', narrator_text).strip()
            
            # Skip if this narrator number already exists
            if narrator_num in found_narrators:
                print(f"Warning: Duplicate narrator number found: {narrator_num}")
                continue
            
            # Update last valid number and expected number
            last_valid_number = narrator_num
            expected_number = narrator_num + 1
            
            # Find the starting page for this narrator
            start_position = match.start()
            start_page = None
            for pos, page_num in sorted(page_markers.items()):
                if pos <= start_position:
                    start_page = page_num
                else:
                    break
            
            # To find the end position of this narrator's content, look for the start of the next narrator
            # or use a reasonable amount of text if this is the last narrator
            next_narrator_pattern = r'(?:\n|\A)(\d+)\s*-\s*(?:\n\*|\*)?'
            next_narrator_matches = list(re.finditer(next_narrator_pattern, full_text))
            
            # Find the next narrator after the current one
            end_position = None
            for i, next_match in enumerate(next_narrator_matches):
                if next_match.start() > match.start():
                    end_position = next_match.start()
                    break
            
            # If no next narrator found, use the end of the text
            if end_position is None:
                end_position = len(full_text)
                
            # Extract the full content for this narrator
            full_content = full_text[match.start():end_position].strip()
                
            # Find ending page (where the narrator text ends)
            end_page = start_page
            for pos, page_num in sorted(page_markers.items()):
                if pos <= end_position:
                    end_page = page_num
                else:
                    break
            
            # Create pages list if narrative spans multiple pages
            span_pages = list(range(start_page, end_page + 1))
            
            # Extract first line as narrator name
            narrator_name = narrator_text.split('\n')[0].strip()
            
            # Store the narrator entry
            found_narrators[narrator_num] = {
                'number': narrator_num_str,
                'narrator': narrator_name,       # Just the name line
                'full_text': full_content,       # Full content including header
                'narrator_content': narrator_text, # Just the narrator text content
                'start_page': start_page,
                'end_page': end_page,
                'span_pages': span_pages
            }
            
            # Update expected number for the next narrator
            expected_number = narrator_num + 1
            
        except ValueError:
            print(f"Warning: Invalid narrator number format: {narrator_num_str}")
    
    # Convert the found_narrators dict to a sorted list
    narrators = [found_narrators[num] for num in sorted(found_narrators.keys())]
    
    # Check for gaps in narrators
    if narrators:
        all_numbers = [int(n['number']) for n in narrators]
        max_num = max(all_numbers)
        missing = [i for i in range(1, max_num + 1) if i not in all_numbers]
        if missing:
            print(f"Warning: Missing narrator numbers: {missing}")
    
    return narrators

def extract_pdf_to_book(pdf_path, pages_per_process=10, max_workers=None):
    """
    Extract text from a PDF file and return it as a book structure.
    
    Args:
        pdf_path: Path to the PDF file
        pages_per_process: Number of pages to process per worker
        max_workers: Maximum number of worker processes (None for auto)
        
    Returns:
        dict: A dictionary containing the book structure with all extracted text
    """
    try:
        # Open the PDF to get total page count
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        doc.close()
        
        print(f"Processing PDF with {total_pages} pages")
        
        # Prepare page ranges for parallel processing
        ranges = []
        for i in range(0, total_pages, pages_per_process):
            ranges.append((i, min(i + pages_per_process, total_pages)))
        
        # Process page ranges in parallel
        all_pages = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(process_page_range, pdf_path, start, end)
                for start, end in ranges
            ]
            
            # Show progress bar
            for future in tqdm(futures, total=len(futures), desc="Extracting text"):
                result = future.result()
                all_pages.extend(result)
        
        # Sort pages by page number
        all_pages.sort(key=lambda x: x['page_number'])
        
        # Create book structure
        book = {
            'source': os.path.basename(pdf_path),
            'total_pages': total_pages,
            'pages': all_pages,
            'metadata': {
                'direction': 'rtl',  # Arabic text is right-to-left
                'language': 'ar',
                'is_book': True
            }
        }
        
        # Extract narrators from the complete book
        narrators = extract_narrators_from_book(book)
        book['narrators'] = narrators
        
        print(f"Successfully extracted {total_pages} pages and {len(narrators)} narrators")
        return book
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        raise

def save_book_to_json(book, output_path):
    """
    Save book dictionary to JSON file.
    
    Args:
        book: Dictionary containing book structure
        output_path: Path to save the JSON output
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(book, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully saved book with {book['total_pages']} pages to {output_path}")
        print(f"Total narrators extracted: {len(book.get('narrators', []))}")
        
    except Exception as e:
        print(f"Error saving book to JSON: {str(e)}")
        raise

def save_narrators_to_json(narrators, output_path):
    """
    Save just the narrators dictionary to a JSON file.
    
    Args:
        narrators: List of narrator dictionaries
        output_path: Path to save the JSON output
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(narrators, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully saved {len(narrators)} narrators to {output_path}")
        
    except Exception as e:
        print(f"Error saving narrators to JSON: {str(e)}")
        raise

def get_sample_book():
    """
    Returns a hardcoded sample book for testing or development.
    
    This sample represents a very small Arabic book with just a few pages.
    In a real application, you'd replace this with actual extraction from a PDF.
    """
    # Sample Arabic text with narrators split across pages
    sample_text = [
        # First page - book title and introduction
        "كتاب الأدب العربي\n\nمقدمة في تاريخ الأدب العربي وتطوره عبر العصور",
        
        # Second page - chapter title and start of first narrator
        "الفصل الأول: العصر الجاهلي\n\n1 - المَجْنُوْنُ قَيْسُ بنُ المُلَوِّحِ العَامِرِي\nيعتبر العصر الجاهلي من أهم العصور في الأدب العربي",
        
        # Third page - continuation of first narrator and start of second
        "حيث ظهرت فيه المعلقات والقصائد الشهيرة...\n\n2 - امرؤ القيس بن حجر الكندي\nمن أبرز شعراء",
        
        # Fourth page - continuation of second narrator and start of third
        "العصر الجاهلي: امرؤ القيس، وزهير بن أبي سلمى، وعنترة بن شداد...\n\n3 - حسان بن ثابت الأنصاري\nمع ظهور الإسلام"
    ]
    
    # Construct sample book structure
    sample_book = {
        'source': 'sample_arabic_book.pdf',
        'total_pages': len(sample_text),
        'pages': [
            {
                'page_number': i + 1,
                'text': text
            } for i, text in enumerate(sample_text)
        ],
        'metadata': {
            'direction': 'rtl',
            'language': 'ar',
            'is_book': True,
            'author': 'مؤلف تجريبي',
            'title': 'كتاب الأدب العربي',
            'word_count': sum(len(text.split()) for text in sample_text)
        }
    }
    
    # Extract narrators from the sample book
    narrators = extract_narrators_from_book(sample_book)
    sample_book['narrators'] = narrators
    
    return sample_book

def main():
    """Process a specific PDF file in the same directory as this script."""
    # Hardcoded PDF filename
    pdf_filename = "004.pdf"
    
    # Get the PDF path relative to the script location
    script_dir = Path(__file__).parent
    pdf_path = script_dir / pdf_filename
    
    if not pdf_path.exists():
        print(f"Error: {pdf_filename} not found in the script directory")
        return
    
    parser = argparse.ArgumentParser(description='Extract text from Arabic PDF and save as JSON or use sample book.')
    parser.add_argument('-o', '--output', help='Path to save the output JSON file')
    parser.add_argument('-p', '--pages-per-process', type=int, default=10,
                        help='Number of pages to process per worker')
    parser.add_argument('-w', '--workers', type=int, default=None,
                        help='Maximum number of worker processes')
    parser.add_argument('--use-sample', action='store_true',
                        help='Use hardcoded sample book instead of processing a PDF')
    
    args = parser.parse_args()
    
    # Use sample book or extract from PDF
    if args.use_sample:
        print("Using hardcoded sample book")
        book = get_sample_book()
    else:
        # Extract PDF to book variable
        print(f"Processing {pdf_filename}")
        book = extract_pdf_to_book(
            str(pdf_path),
            pages_per_process=args.pages_per_process,
            max_workers=args.workers
        )
    
    # Generate output path if not provided
    if not args.output:
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{book['metadata'].get('title', 'output').replace(' ', '_')}.json"
        args.output = str(output_file)
    
    # Access and work with the book variable here if needed
    print(f"Book title: {book['metadata'].get('title', 'Unknown')}")
    print(f"Total pages: {book['total_pages']}")
    print(f"Total narrators: {len(book.get('narrators', []))}")
    print(f"Total words: {book['metadata'].get('word_count', 'Unknown')}")
    
    # Save book to JSON
    save_book_to_json(book, args.output)
    
    # Generate narrators output path and save narrators separately
    narrators_output = str(Path(args.output).with_name(
        f"{Path(args.output).stem}_narrators.json"
    ))
    save_narrators_to_json(book.get('narrators', []), narrators_output)

if __name__ == "__main__":
    main()