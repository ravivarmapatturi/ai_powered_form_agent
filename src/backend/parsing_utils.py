import os
from langchain_community.document_loaders import PyPDFLoader,PyMuPDFLoader,PDFMinerLoader,Docx2txtLoader,UnstructuredHTMLLoader
from langchain_core.documents import Document
import pypdfium2 as pdfium
from openai import OpenAI
# from markitdown import MarkItDown
# from docling.document_converter import DocumentConverter
import fitz  # PyMuPDF
from pathlib import Path
import json
import shutil

from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")





import base64
from openai import OpenAI

client = OpenAI(api_key=api_key)

def pdf_to_images(pdf_path: str, output_dir: str = "tmp_pdf_images", dpi: int = 200) -> list[str]:
    """
    Convert PDF pages into PNG images.
    Returns list of image file paths.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    image_paths = []

    for i in range(len(doc)):
        page = doc.load_page(i)

        # Render page to pixmap
        zoom = dpi / 72  # 72 is default DPI
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        out_path = os.path.join(output_dir, f"{Path(pdf_path).stem}_page_{i+1}.png")
        pix.save(out_path)
        image_paths.append(out_path)

    doc.close()
    return image_paths


def guess_mime(image_path: str) -> str:
    ext = image_path.lower().split(".")[-1]
    if ext in ["jpg", "jpeg"]:
        return "image/jpeg"
    if ext in ["png"]:
        return "image/png"
    if ext in ["tif", "tiff"]:
        return "image/tiff"
    return "image/png"

def parsing_image(image_path: str):
    # Read image and convert to base64
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = """
You are an Intelligent Form Agent.
Extract key fields and values from this form image.

Rules:
- Use ONLY what is visible in the image
- Do not guess
- If not found, write "Not Found"
Return ONLY valid JSON (no markdown).

JSON keys:
document_type, one_line_summary, key_fields, important_entities, missing_or_unclear_fields, red_flags, short_summary

key_fields must be a list of objects with: field, value
important_entities must include: people, organizations, dates, amounts, ids
"""

    resp = client.responses.create(
        model="gpt-4o-mini",  # vision supported
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:{guess_mime(image_path)};base64,{image_b64}"
                    }
                ]
            }
        ],
    )

    text = resp.output_text

    try:
        return json.loads(text)
    except Exception:
        return {"raw_output": text}


def cleanup_tmp_images(tmp_dir="tmp_pdf_images"):
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
        
def is_text_poor(docs: list[Document], min_chars: int = 200) -> bool:
    total = sum(len(d.page_content.strip()) for d in docs if d.page_content)
    return total < min_chars

def parse_scanned_pdf_with_vision(pdf_path: str) -> dict:
    image_paths=[]
    try:
        """
        Convert PDF pages to images and run vision extraction per page.
        Returns merged JSON dict.
        """
        image_paths = pdf_to_images(pdf_path)

        all_pages = []
        for idx, img_path in enumerate(image_paths, start=1):
            parsed = parsing_image(img_path)

            # parsed might be dict or {"raw_output": "..."}
            all_pages.append({
                "page": idx,
                "result": parsed
            })

        merged = {
            "document_type": "Scanned PDF Form",
            "source": pdf_path,
            "pages": all_pages
        }

        return merged
    finally:
        # Cleanup temp images
        cleanup_tmp_images()
        

def json_to_retrieval_text(parsed: dict) -> str:
    """
    Convert structured extracted JSON into searchable text for vector DB.
    """
    if not isinstance(parsed, dict):
        return str(parsed)

    lines = []
    lines.append(f"Document Type: {parsed.get('document_type', 'Unknown')}")
    if "one_line_summary" in parsed:
        lines.append(f"One Line Summary: {parsed.get('one_line_summary')}")

    # If scanned PDF multi-page format
    if "pages" in parsed and isinstance(parsed["pages"], list):
        for page_obj in parsed["pages"]:
            page_no = page_obj.get("page", "NA")
            result = page_obj.get("result", {})
            lines.append(f"\n--- Page {page_no} ---")

            if isinstance(result, dict):
                lines.append(result.get("short_summary", ""))

                key_fields = result.get("key_fields", [])
                if isinstance(key_fields, list):
                    for kv in key_fields:
                        field = kv.get("field", "")
                        value = kv.get("value", "")
                        if field:
                            lines.append(f"{field}: {value}")

                missing = result.get("missing_or_unclear_fields", [])
                if missing:
                    lines.append(f"Missing/Unclear: {missing}")
            else:
                lines.append(str(result))

    return "\n".join([l for l in lines if l])

def PARSING_PDF(parsing_strategy,pdf_path):
    if parsing_strategy=="PyPDFLoader":
        loader = PyPDFLoader(pdf_path)

        langchain_docs = loader.load()
    
    elif parsing_strategy=="PyMuPDFLoader":
        loader = PyMuPDFLoader(pdf_path)

        langchain_docs = loader.load()
        
    elif parsing_strategy=="PDFMinerLoader":
        loader = PDFMinerLoader(pdf_path)
        langchain_docs = loader.load()
        
    elif parsing_strategy=="pdfium":
        # Load the PDF
        pdf = pdfium.PdfDocument(pdf_path)
        
        # List to hold LangChain documents
        langchain_docs = []
        
        # Extract metadata using get_metadata_dict()
        metadata = pdf.get_metadata_dict()
        source_metadata = {
            "source": pdf_path,
            "title": metadata.get("Title", "Unknown"),
            "author": metadata.get("Author", "Unknown"),
            "subject": metadata.get("Subject", "Unknown"),
        }
        
        # Extract data page by page
        for page_number in range(len(pdf)):
            page = pdf[page_number]
            
            # Extract text
            text = page.get_textpage().get_text_range()
            
            # Create metadata for the current page
            page_metadata = {
                "page_number": page_number + 1,
                **source_metadata,  # Add general metadata
            }
            
            # Create a LangChain Document for the current page
            document = Document(
                page_content=text,
                metadata=page_metadata
            )
            langchain_docs.append(document)
        
        return langchain_docs

    
    # elif parsing_strategy=="markitdown":
        
    #     client = OpenAI()
    #     markitdown = MarkItDown(llm_client=client, llm_model="gpt-4")
        
    #     # Convert the Markdown file
    #     result = markitdown.convert(pdf_path)
        
    #     # Access the attributes of the result object
    #     title = result.title or "Unknown"
    #     text_content = result.text_content or ""
        
    #     # Metadata
    #     metadata = {
    #         "source": pdf_path,
    #         "title": title,
    #     }
        
    #     # Create a LangChain Document
    #     langchain_docs = [
    #         Document(
    #             page_content=text_content,
    #             metadata=metadata
    #         )
    #     ]
        
    #     return langchain_docs
    
    
    elif parsing_strategy=="docling":
        
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        
        
        return result.document
    
def load_and_split_documents(file_path:str)->list[Document]:
    if file_path.lower().endswith(".pdf"):
        # 1) Try text-based extraction first (fast)
        langchain_docs = PARSING_PDF("pdfium", file_path)

        # 2) If scanned/empty → Vision extraction
        if is_text_poor(langchain_docs):
            parsed_json = parse_scanned_pdf_with_vision(file_path)
            retrieval_text = json_to_retrieval_text(parsed_json)

            langchain_docs = [
                Document(
                    page_content=retrieval_text,
                    metadata={"source": file_path, "file_type": "pdf_scanned"}
                )
            ]

    elif file_path.lower().endswith(".docx"):
        loader=Docx2txtLoader(file_path)
        langchain_docs = loader.load()
    elif file_path.lower().endswith(".html"):
        loader=UnstructuredHTMLLoader(file_path)
        langchain_docs = loader.load()
    #jpg,png,tiff 
    elif file_path.lower().endswith((".jpg", ".jpeg", ".png", ".tiff", ".tif")):
        parsed = parsing_image(file_path)
        retrieval_text = json_to_retrieval_text({
            "document_type": "Image Form",
            "pages": [{"page": 1, "result": parsed}]
        })

        langchain_docs = [
            Document(
                page_content=retrieval_text,
                metadata={"source": file_path, "file_type": "image"}
            )
        ]

    else:
        raise ValueError("Unsupported file format. Currently only PDF, DOCX, and HTML formats are supported.")
    
    return langchain_docs

