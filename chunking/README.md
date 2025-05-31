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

## Output Structure and code output

```
Verification Summary for bahir-burhan.json:
Total chunks: 1639
Valid chunks: 1634
Invalid chunks: 5
Pages with titles: 82
Pages without titles: 1557
Chunked output saved to: chunked_output\chunks\bahir-burhan--chunked.json
Verification results saved to: chunked_output\verification\bahir-burhan--verification.json
✓ Successfully processed bahir-burhan.json
--------------------------------------------------

Processing file 2/20: cujab-fi-bayan-asbab.json

Verification Summary for cujab-fi-bayan-asbab.json:
Total chunks: 1302
Valid chunks: 1302
Invalid chunks: 0
Pages with titles: 41
Pages without titles: 1261
Chunked output saved to: chunked_output\chunks\cujab-fi-bayan-asbab--chunked.json
Verification results saved to: chunked_output\verification\cujab-fi-bayan-asbab--verification.json
✓ Successfully processed cujab-fi-bayan-asbab.json
--------------------------------------------------

Processing file 3/20: daqaiq-tafsir.json

Verification Summary for daqaiq-tafsir.json:
Total chunks: 322
Valid chunks: 322
Invalid chunks: 0
Pages with titles: 100
Pages without titles: 222
Chunked output saved to: chunked_output\chunks\daqaiq-tafsir--chunked.json
Verification results saved to: chunked_output\verification\daqaiq-tafsir--verification.json
✓ Successfully processed daqaiq-tafsir.json
--------------------------------------------------

Processing file 4/20: durr-masun.json

Verification Summary for durr-masun.json:
Total chunks: 10884
Valid chunks: 10881
Invalid chunks: 3
Pages with titles: 4712
Pages without titles: 6172
Chunked output saved to: chunked_output\chunks\durr-masun--chunked.json
Verification results saved to: chunked_output\verification\durr-masun--verification.json
✓ Successfully processed durr-masun.json
--------------------------------------------------

Processing file 5/20: fadail-quran-8.json

Verification Summary for fadail-quran-8.json:
Total chunks: 305
Valid chunks: 303
Invalid chunks: 2
Pages with titles: 37
Pages without titles: 268
Chunked output saved to: chunked_output\chunks\fadail-quran-8--chunked.json
Verification results saved to: chunked_output\verification\fadail-quran-8--verification.json
✓ Successfully processed fadail-quran-8.json
--------------------------------------------------

Processing file 6/20: hashiya-cala-tafsir-baydawi-1.json

Verification Summary for hashiya-cala-tafsir-baydawi-1.json:
Total chunks: 3155
Valid chunks: 3153
Invalid chunks: 2
Pages with titles: 115
Pages without titles: 3040
Chunked output saved to: chunked_output\chunks\hashiya-cala-tafsir-baydawi-1--chunked.json
Verification results saved to: chunked_output\verification\hashiya-cala-tafsir-baydawi-1--verification.json
✓ Successfully processed hashiya-cala-tafsir-baydawi-1.json
--------------------------------------------------

Processing file 7/20: hidaya-1.json

Verification Summary for hidaya-1.json:
Total chunks: 8475
Valid chunks: 8446
Invalid chunks: 29
Pages with titles: 2287
Pages without titles: 6188
Chunked output saved to: chunked_output\chunks\hidaya-1--chunked.json
Verification results saved to: chunked_output\verification\hidaya-1--verification.json
✓ Successfully processed hidaya-1.json
--------------------------------------------------

Processing file 8/20: hikayat-munazara.json

Verification Summary for hikayat-munazara.json:
Total chunks: 45
Valid chunks: 45
Invalid chunks: 0
Pages with titles: 2
Pages without titles: 43
Chunked output saved to: chunked_output\chunks\hikayat-munazara--chunked.json
Verification results saved to: chunked_output\verification\hikayat-munazara--verification.json
✓ Successfully processed hikayat-munazara.json
--------------------------------------------------

Processing file 9/20: icjaz-quran.json

Verification Summary for icjaz-quran.json:
Total chunks: 401
Valid chunks: 397
Invalid chunks: 4
Pages with titles: 40
Pages without titles: 361
Chunked output saved to: chunked_output\chunks\icjaz-quran--chunked.json
Verification results saved to: chunked_output\verification\icjaz-quran--verification.json
✓ Successfully processed icjaz-quran.json
--------------------------------------------------

Processing file 10/20: ithaf-dhawi-albab.json

Verification Summary for ithaf-dhawi-albab.json:
Total chunks: 98
Valid chunks: 98
Invalid chunks: 0
Pages with titles: 17
Pages without titles: 81
Chunked output saved to: chunked_output\chunks\ithaf-dhawi-albab--chunked.json
Verification results saved to: chunked_output\verification\ithaf-dhawi-albab--verification.json
✓ Successfully processed ithaf-dhawi-albab.json
--------------------------------------------------

Processing file 11/20: juz-fi-tafsir-baqiyat.json

Verification Summary for juz-fi-tafsir-baqiyat.json:
Total chunks: 34
Valid chunks: 34
Invalid chunks: 0
Pages with titles: 10
Pages without titles: 24
Chunked output saved to: chunked_output\chunks\juz-fi-tafsir-baqiyat--chunked.json
Verification results saved to: chunked_output\verification\juz-fi-tafsir-baqiyat--verification.json
✓ Successfully processed juz-fi-tafsir-baqiyat.json
--------------------------------------------------

Processing file 12/20: lughat-fi-quran.json

Verification Summary for lughat-fi-quran.json:
Total chunks: 81
Valid chunks: 81
Invalid chunks: 0
Pages with titles: 74
Pages without titles: 7
Chunked output saved to: chunked_output\chunks\lughat-fi-quran--chunked.json
Verification results saved to: chunked_output\verification\lughat-fi-quran--verification.json
✓ Successfully processed lughat-fi-quran.json
--------------------------------------------------

Processing file 13/20: nawahid-abkar.json

Verification Summary for nawahid-abkar.json:
Total chunks: 1469
Valid chunks: 1464
Invalid chunks: 5
Pages with titles: 393
Pages without titles: 1076
Chunked output saved to: chunked_output\chunks\nawahid-abkar--chunked.json
Verification results saved to: chunked_output\verification\nawahid-abkar--verification.json
✓ Successfully processed nawahid-abkar.json
--------------------------------------------------

Processing file 14/20: nawasikh-quran.json

Verification Summary for nawahid-abkar.json:
Total chunks: 1469
Valid chunks: 1464
Invalid chunks: 5
Pages with titles: 393
Pages without titles: 1076
Chunked output saved to: chunked_output\chunks\nawahid-abkar--chunked.json
Verification results saved to: chunked_output\verification\nawahid-abkar--verification.json
✓ Successfully processed nawahid-abkar.json
--------------------------------------------------

Processing file 14/20: nawasikh-quran.json

Valid chunks: 1464
Invalid chunks: 5
Pages with titles: 393
Pages without titles: 1076
Chunked output saved to: chunked_output\chunks\nawahid-abkar--chunked.json
Verification results saved to: chunked_output\verification\nawahid-abkar--verification.json
✓ Successfully processed nawahid-abkar.json
--------------------------------------------------

Processing file 14/20: nawasikh-quran.json

Pages without titles: 1076
Chunked output saved to: chunked_output\chunks\nawahid-abkar--chunked.json
Verification results saved to: chunked_output\verification\nawahid-abkar--verification.json
✓ Successfully processed nawahid-abkar.json
--------------------------------------------------

Processing file 14/20: nawasikh-quran.json

✓ Successfully processed nawahid-abkar.json
--------------------------------------------------

Processing file 14/20: nawasikh-quran.json

Processing file 14/20: nawasikh-quran.json


Verification Summary for nawasikh-quran.json:
Total chunks: 417
Valid chunks: 412
Invalid chunks: 5
Pages with titles: 365
Pages without titles: 52
Chunked output saved to: chunked_output\chunks\nawasikh-quran--chunked.json
Verification results saved to: chunked_output\verification\nawasikh-quran--verification.json
✓ Successfully processed nawasikh-quran.json
--------------------------------------------------

Processing file 15/20: nazm-durar-1.json

Verification Summary for nazm-durar-1.json:
Total chunks: 11854
Valid chunks: 11854
Invalid chunks: 0
Pages with titles: 1445
Pages without titles: 10409
Chunked output saved to: chunked_output\chunks\nazm-durar-1--chunked.json
Verification results saved to: chunked_output\verification\nazm-durar-1--verification.json
✓ Successfully processed nazm-durar-1.json
--------------------------------------------------

Processing file 16/20: tafsir-13.json

Verification Summary for tafsir-13.json:
Total chunks: 8530
Valid chunks: 8530
Invalid chunks: 0
Pages with titles: 6257
Pages without titles: 2273
Chunked output saved to: chunked_output\chunks\tafsir-13--chunked.json
Verification results saved to: chunked_output\verification\tafsir-13--verification.json
✓ Successfully processed tafsir-13.json
--------------------------------------------------

Processing file 17/20: tafsir-19.json

Verification Summary for tafsir-19.json:
Verification Summary for tafsir-27.json:
Total chunks: 2387
Valid chunks: 2387
Invalid chunks: 0
Pages with titles: 683
Pages without titles: 1704
Chunked output saved to: chunked_output\chunks\tafsir-27--chunked.json
Verification results saved to: chunked_output\verification\tafsir-27--verification.json
✓ Successfully processed tafsir-27.json
--------------------------------------------------

Processing file 19/20: tafsir-abi-al-suud.json

Verification Summary for tafsir-abi-al-suud.json:
Total chunks: 8755
Valid chunks: 8755
Invalid chunks: 0
Pages with titles: 6244
Pages without titles: 2511
Chunked output saved to: chunked_output\chunks\tafsir-abi-al-suud--chunked.json
Verification results saved to: chunked_output\verification\tafsir-abi-al-suud--verification.json
✓ Successfully processed tafsir-abi-al-suud.json
--------------------------------------------------

Processing file 20/20: tafsir-quran.json

Verification Summary for tafsir-quran.json:
Total chunks: 436
Valid chunks: 436
Invalid chunks: 0
Pages with titles: 14
Processing file 20/20: tafsir-quran.json

Verification Summary for tafsir-quran.json:
Total chunks: 436
Valid chunks: 436
Invalid chunks: 0
Processing file 20/20: tafsir-quran.json

Verification Summary for tafsir-quran.json:
Total chunks: 436
Valid chunks: 436
Processing file 20/20: tafsir-quran.json

Verification Summary for tafsir-quran.json:
Total chunks: 436
Processing file 20/20: tafsir-quran.json

Processing file 20/20: tafsir-quran.json

Verification Summary for tafsir-quran.json:
Total chunks: 436
Valid chunks: 436
Invalid chunks: 0
Pages with titles: 14
Pages without titles: 422
Chunked output saved to: chunked_output\chunks\tafsir-quran--chunked.json
Verification results saved to: chunked_output\verification\tafsir-quran--verification.json
✓ Successfully processed tafsir-quran.json
--------------------------------------------------

Processing Summary:
Total files processed: 20
Successfully processed: 20
Failed to process: 0

Output Directory Structure:
  chunked_output/
  ├── chunks/
  │   └── [chunked JSON files]
  └── verification/
      └── [verification JSON files]

```

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