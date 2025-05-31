# Text Chunking and Verification Tool

This tool processes JSON files containing text content, headings, and page information, and creates chunked versions of the content with verification results.

## Directory Structure

```
project/
├── tafsir_books/              # Input directory containing JSON files
├── chunked_output/            # Output directory
│   ├── chunks/               # Contains chunked JSON files
│   └── verification/         # Contains verification results
├── chunking/
│   └── main.py              # Main processing script
└── requirements.txt          # Python dependencies
```

## Input JSON Structure

The input JSON files should have the following structure:

```json
{
  "headings": [
    {
      "title": "المقدمة",
      "level": 1,
      "page": {
        "vol": "1",
        "page": 1
      },
      "pageIndex": 1
    }
  ],
  "pages": [
    {
      "text": "Content text here...",
      "vol": "1",
      "page": 1
    }
  ],
  "sourcePdf": [
    {
      "volume": "1",
      "url": "https://example.com/pdf/vol1.pdf"
    }
  ],
  "sourcePublicationDetails": {
    "investigator": "Author Name",
    "publisherLocation": "Location",
    "publisher": "Publisher Name"
  },
  "transliteration": "Book Title in English"
}
```

## Output Structure

### Chunked JSON Files
Located in `chunked_output/chunks/`, each file follows this structure:

```json
[
  {
    "book_transliteration": "Book Title",
    "book_slug": "N/A",
    "text": "Cleaned text content",
    "vol": "1",
    "page": 1,
    "title": "Title if available",
    "tokens": 150
  }
]
```

### Verification Files
Located in `chunked_output/verification/`, each file contains verification results:

```json
[
  {
    "vol": "1",
    "page": 1,
    "title": "Title if available",
    "verification": {
      "similarity_ratio": 0.98,
      "has_differences": false,
      "missing_words": [],
      "extra_words": [],
      "diff_count": 0,
      "is_valid": true
    }
  }
]
```

## Cases Handled

The script handles the following cases:

1. **Pages with Headings and Titles**
   - Extracts title from heading
   - Removes title from text content if present
   - Creates chunk with title information

2. **Pages with Headings but No Titles**
   - Processes the page with null title
   - Preserves all text content

3. **Pages with Only Text and Page Numbers**
   - Creates chunks without title information
   - Sets title field to null
   - Preserves all text content

4. **HTML Content Cleaning**
   - Removes HTML tags
   - Removes data-type="title" content
   - Normalizes whitespace
   - Preserves essential text content

5. **Verification Checks**
   - Compares original and cleaned text
   - Calculates similarity ratio
   - Identifies missing or extra words
   - Validates content preservation

## Requirements

```txt
beautifulsoup4==4.12.2
```

## Usage

1. Place input JSON files in the `tafsir_books` directory
2. Run the script:
   ```bash
   python chunking/main.py
   ```
3. Check the output in `chunked_output` directory:
   - Chunked files in `chunks/` subdirectory
   - Verification results in `verification/` subdirectory

## Output Summary

The script provides a summary for each processed file:
- Total number of chunks
- Number of valid chunks
- Number of invalid chunks
- Pages with titles
- Pages without titles
- Output file locations

## Verification Criteria

A chunk is considered valid if:
- Similarity ratio > 0.95
- Number of missing words < 10
- No significant content loss

## Error Handling

The script handles various error cases:
- Missing transliteration
- Invalid JSON structure
- File reading/writing errors
- HTML parsing errors

## Notes

- The script preserves the original text structure while removing HTML tags
- Titles are extracted from headings when available
- Pages without headings are processed with null titles
- Verification results help ensure content integrity 
