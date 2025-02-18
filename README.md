# PDF Text Extraction Tool

This project provides a Python script to extract text from Arabic PDF files and save the extracted content in a structured JSON format. It includes functionality for parallel processing of pages to improve performance.

## Requirements

- Python 3.x
- Required libraries:
  - `PyMuPDF` (install via `pip install PyMuPDF`)
  - `tqdm` (install via `pip install tqdm`)

## Usage

### Running the Script

To run the script, use the following command in your terminal:

```bash
python parsing.py [options]
```

### Options

- `-o`, `--output`: Specify the path to save the output JSON file.
- `-p`, `--pages-per-process`: Set the number of pages to process per worker (default is 10).
- `-w`, `--workers`: Set the maximum number of worker processes (default is None, which uses the number of available CPU cores).
- `--use-sample`: Use a hardcoded sample book instead of processing a PDF file.

### Example Command

To extract text from a PDF file named `004.pdf` and save the output to `output.json`, run:

```bash
python parsing.py -o output/output.json
```

To use the hardcoded sample book instead, run:

```bash
python parsing.py --use-sample
```

### Input

The script expects a PDF file named `004.pdf` to be present in the same directory as the script. You can replace this file with your own Arabic PDF file.

### Output

The output will be a JSON file containing the extracted text structured as follows:

```json
{
  "source": "004.pdf",
  "total_pages": 10,
  "pages": [
    {
      "page_number": 1,
      "text": "Extracted text from page 1"
    },
    {
      "page_number": 2,
      "text": "Extracted text from page 2"
    }
    // ...
  ],
  "metadata": {
    "direction": "rtl",
    "language": "ar",
    "is_book": true,
    "author": "Author Name",
    "title": "Book Title",
    "word_count": 1234
  }
}
```

### Notes

- Ensure that the PDF file is accessible and not password-protected.
- The script handles Arabic text and formats it appropriately for right-to-left reading.

## License

This project is licensed under the MIT License.
