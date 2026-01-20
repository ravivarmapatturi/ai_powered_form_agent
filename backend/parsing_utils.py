import os
from langchain_community.document_loaders import PyPDFLoader,PyMuPDFLoader,PDFMinerLoader,Docx2txtLoader,UnstructuredHTMLLoader
from langchain_core.documents import Document
import pypdfium2 as pdfium
from openai import OpenAI
# from markitdown import MarkItDown
# from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")





import base64
from openai import OpenAI

client = OpenAI(api_key=api_key)

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
                        "image_url": f"data:image/png;base64,{image_b64}"
                    }
                ]
            }
        ],
    )

    return resp.output_text



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
        langchain_docs=PARSING_PDF("pdfium",file_path)
    elif file_path.lower().endswith(".docx"):
        loader=Docx2txtLoader(file_path)
        langchain_docs = loader.load()
    elif file_path.lower().endswith(".html"):
        loader=UnstructuredHTMLLoader(file_path)
        langchain_docs = loader.load()
    #jpg,png,tiff 
    elif file_path.lower().endswith((".jpg", ".jpeg", ".png", ".tiff", ".tif")):
        extracted_text = parsing_image(file_path)  # returns text/JSON string

        langchain_docs = [
            Document(
                page_content=extracted_text,
                metadata={"source": file_path, "file_type": "image"}
            )
        ]
    else:
        raise ValueError("Unsupported file format. Currently only PDF, DOCX, and HTML formats are supported.")
    
    return langchain_docs

