from mistralai import Mistral
import os
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["MISTRAL_API_KEY"]

client = Mistral(api_key=api_key)

def serialize_dimensions(dimensions):
    """Helper function to serialize OCRPageDimensions"""
    return {
        "dpi": dimensions.dpi,
        "height": dimensions.height,
        "width": dimensions.width
    }

uploaded_pdf = client.files.upload(
    file={
        "file_name": "book.pdf",
        "content": open("book.pdf", "rb"),
    },
    purpose="ocr"
)  
client.files.retrieve(file_id=uploaded_pdf.id)
signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
print(signed_url.url)

ocr_response = client.ocr.process(
    model="mistral-ocr-latest",
    document={
        "type": "document_url",
        "document_url": signed_url.url,
    }
)

def replace_images_in_markdown(markdown_str: str, images_dict: dict) -> str:
    for img_name, base64_str in images_dict.items():
        markdown_str = markdown_str.replace(f"![{img_name}]({img_name})", f"![{img_name}]({base64_str})")
    return markdown_str

def get_combined_markdown(ocr_response) -> str:
    markdowns: list[str] = []
    for page in ocr_response.pages:
        image_data = {}
        for img in page.images:
            image_data[img.id] = img.image_base64
        markdowns.append(replace_images_in_markdown(page.markdown, image_data))
    return "\n\n".join(markdowns)

# Convert OCRResponse to dictionary
ocr_dict = {
    "pages": [
        {
            "index": page.index,
            "markdown": page.markdown,
            "dimensions": serialize_dimensions(page.dimensions),
            "images": [
                {
                    "id": img.id,
                    "image_base64": img.image_base64
                } for img in page.images
            ] if hasattr(page, 'images') else []
        } for page in ocr_response.pages
    ]
}

# Save OCR response to JSON file
json_output = "ocr_output.json"
with open(json_output, 'w', encoding='utf-8') as f:
    json.dump(ocr_dict, f, indent=4, ensure_ascii=False)

# Save markdown output
markdown_output = "ocr_output.md"
with open(markdown_output, 'w', encoding='utf-8') as f:
    f.write(get_combined_markdown(ocr_response))

print(f"OCR results saved to {json_output}")
print(f"Markdown output saved to {markdown_output}")