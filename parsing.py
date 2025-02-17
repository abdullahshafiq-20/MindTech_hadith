import argparse
import json
import os
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
        
        print(f"Successfully extracted {total_pages} pages")
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
        
    except Exception as e:
        print(f"Error saving book to JSON: {str(e)}")
        raise

def get_sample_book():
    """
    Returns a hardcoded sample book for testing or development.
    
    This sample represents a very small Arabic book with just a few pages.
    In a real application, you'd replace this with actual extraction from a PDF.
    """
    # Sample Arabic text (small snippets for demonstration)
    sample_text = [
        # First page - book title and introduction
        "كتاب الأدب العربي\n\nمقدمة في تاريخ الأدب العربي وتطوره عبر العصور",
        
        # Second page - chapter title and content
        "الفصل الأول: العصر الجاهلي\n\nيعتبر العصر الجاهلي من أهم العصور في الأدب العربي حيث ظهرت فيه المعلقات والقصائد الشهيرة...",
        
        # Third page - more content
        "استمرار الفصل الأول\n\nمن أبرز شعراء العصر الجاهلي: امرؤ القيس، وزهير بن أبي سلمى، وعنترة بن شداد...",
        
        # Fourth page - new chapter
        "الفصل الثاني: العصر الإسلامي\n\nمع ظهور الإسلام، تأثر الأدب العربي بالقيم الإسلامية وظهرت أغراض جديدة في الشعر..."
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
    print(f"Total words: {book['metadata'].get('word_count', 'Unknown')}")
    
    # Save book to JSON
    save_book_to_json(book, args.output)

if __name__ == "__main__":
    main()