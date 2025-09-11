import os
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
import fitz  # PyMuPDF

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

def extract(pdf_path: list[str]) -> list[str]:
    """
    Extract text from a PDF file.
    """
    extracted_text = []
    for path in pdf_path:
        doc = fitz.open(path)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        extracted_text.append(text)
    return extracted_text

def chunk(text: list[str]) -> list[dict]:
    """
    Chunk the text into chunks of CHUNK_SIZE with CHUNK_OVERLAP.
    """
    section_pattern = r'\n(?=Abstract|Introduction|Conclusion|References|\d+(?:\.\d+)*\s+[A-Z][a-zA-Z\s]+)'
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    final_chunks = []
    for single_text in text:
        sections = re.split(section_pattern, single_text)
        
        for section in sections:
            if not section.strip():
                continue

            lines = section.strip().split('\n')
            title = lines[0].strip()
            content = ' '.join(lines[1:]).strip()

            if content:
                sub_chunks = text_splitter.split_text(content)
                for sub_chunk in sub_chunks:
                    final_chunks.append({
                        'title': title,
                        'content': sub_chunk
                    })
    return final_chunks



