import fitz
import os
from typing import List, Dict, Tuple
from dotenv import load_dotenv
import re

load_dotenv()

class PDFProcessor:
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = chunk_overlap or int(os.getenv("CHUNK_OVERLAP", "200"))
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, str]]:
        doc = fitz.open(pdf_path)
        pages_text = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            text = self._clean_text(text)
            
            if text.strip():
                pages_text.append({
                    "page_num": page_num + 1,
                    "text": text,
                    "section_title": self._extract_section_title(text)
                })
        
        doc.close()
        return pages_text
    
    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 10:
                cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines)
    
    def _extract_section_title(self, text: str) -> str:
        lines = text.split('\n')
        for line in lines[:3]:
            line = line.strip()
            if len(line) > 5 and len(line) < 100:
                if any(keyword in line.lower() for keyword in 
                       ['abstract', 'introduction', 'conclusion', 'method', 'result', 'discussion']):
                    return line
        return "Content"
    
    def chunk_text(self, pages_text: List[Dict[str, str]]) -> List[Dict[str, str]]:
        chunks = []
        chunk_index = 0
        
        for page_data in pages_text:
            text = page_data["text"]
            page_num = page_data["page_num"]
            section_title = page_data["section_title"]
            
            sentences = self._split_into_sentences(text)
            current_chunk = ""
            current_chunk_sentences = []
            
            for sentence in sentences:
                test_chunk = current_chunk + " " + sentence if current_chunk else sentence
                
                if len(test_chunk) <= self.chunk_size:
                    current_chunk = test_chunk
                    current_chunk_sentences.append(sentence)
                else:
                    if current_chunk:
                        chunks.append({
                            "text": current_chunk.strip(),
                            "chunk_index": chunk_index,
                            "page_num": page_num,
                            "section_title": section_title
                        })
                        chunk_index += 1
                    
                    if self.chunk_overlap > 0 and len(current_chunk_sentences) > 1:
                        overlap_text = " ".join(current_chunk_sentences[-2:])
                        if len(overlap_text) <= self.chunk_overlap:
                            current_chunk = overlap_text + " " + sentence
                            current_chunk_sentences = current_chunk_sentences[-2:] + [sentence]
                        else:
                            current_chunk = sentence
                            current_chunk_sentences = [sentence]
                    else:
                        current_chunk = sentence
                        current_chunk_sentences = [sentence]
            
            if current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "chunk_index": chunk_index,
                    "page_num": page_num,
                    "section_title": section_title
                })
                chunk_index += 1
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def process_pdf(self, pdf_path: str) -> Tuple[str, List[Dict[str, str]]]:
        filename = os.path.basename(pdf_path)
        pages_text = self.extract_text_from_pdf(pdf_path)
        chunks = self.chunk_text(pages_text)
        
        for chunk in chunks:
            chunk["filename"] = filename
        
        return filename, chunks

def process_all_pdfs(pdf_directory: str) -> Dict[str, List[Dict[str, str]]]:
    processor = PDFProcessor()
    all_documents = {}
    
    pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        return all_documents
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_directory, pdf_file)
        try:
            filename, chunks = processor.process_pdf(pdf_path)
            all_documents[filename] = chunks
        except Exception:
            continue
    
    return all_documents

if __name__ == "__main__":
    pdf_dir = "/app/data/pdfs"
    if os.path.exists(pdf_dir):
        documents = process_all_pdfs(pdf_dir)
        for filename, chunks in documents.items():
            print(f"{filename}: {len(chunks)} chunks")
    else:
        print(f"PDF directory {pdf_dir} not found")