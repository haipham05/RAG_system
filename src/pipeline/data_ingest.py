import fitz
import os
from typing import List, Dict, Tuple
from dotenv import load_dotenv
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

class PDFProcessor:
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None, max_section_size: int = None):
        self.chunk_size = chunk_size or int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = chunk_overlap or int(os.getenv("CHUNK_OVERLAP", "200"))
        self.max_section_size = max_section_size or int(os.getenv("MAX_SECTION_SIZE", "3000"))
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
    
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
        numbered_pattern = r'\b(\d+\s+[A-Z][a-zA-Z\s]+?)(?=\s+[a-z]|\s+[A-Z][a-z]|\s+[A-Z]{2,}|\s+[0-9]|\s+[^\w\s]|$)'
        numbered_matches = re.findall(numbered_pattern, text)
        if numbered_matches:
            for match in numbered_matches:
                if len(match.strip()) > 5 and len(match.strip()) < 100:
                    return match.strip()
        
        subsection_pattern = r'\b(\d+\.\d+\s+[A-Z][a-zA-Z\s]+?)(?=\s+[a-z]|\s+[A-Z][a-z]|\s+[A-Z]{2,}|\s+[0-9]|\s+[^\w\s]|$)'
        subsection_matches = re.findall(subsection_pattern, text)
        if subsection_matches:
            for match in subsection_matches:
                if len(match.strip()) > 5 and len(match.strip()) < 100:
                    return match.strip()
        
        section_keywords = [
            'abstract', 'introduction', 'related work', 'background', 
            'methodology', 'method', 'approach', 'model', 'architecture',
            'experiments', 'results', 'evaluation', 'analysis',
            'discussion', 'conclusion', 'future work', 'limitations',
            'acknowledgments', 'references', 'appendix', 'scope',
            'scaling', 'prediction', 'capabilities', 'training',
            'attention', 'transformer', 'encoder', 'decoder'
        ]
        
        text_lower = text.lower()
        for keyword in section_keywords:
            if keyword in text_lower:
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if keyword in line.lower() and len(line) > 5 and len(line) < 100:
                        return line
        
        return "Content"
    
    def chunk_text(self, pages_text: List[Dict[str, str]]) -> List[Dict[str, str]]:
        chunks = []
        chunk_index = 0
        
        sections = self._group_pages_by_section(pages_text)
        
        for section_title, section_pages in sections.items():
            if len(" ".join([page["text"] for page in section_pages])) > self.max_section_size:
                section_text = " ".join([page["text"] for page in section_pages])
                section_chunks = self.text_splitter.split_text(section_text)
                
                for i, chunk_text in enumerate(section_chunks):
                    chunk_page_num = self._find_page_for_chunk(chunk_text, section_pages)
                    
                    chunks.append({
                        "text": chunk_text.strip(),
                        "chunk_index": chunk_index,
                        "page_num": chunk_page_num,
                        "section_title": f"{section_title} (Part {i+1})"
                    })
                    chunk_index += 1
            else:
                for page_data in section_pages:
                    chunks.append({
                        "text": page_data["text"].strip(),
                        "chunk_index": chunk_index,
                        "page_num": page_data["page_num"],
                        "section_title": section_title
                    })
                    chunk_index += 1
        
        return chunks
    
    def _group_pages_by_section(self, pages_text: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        sections = {}
        current_section = "Abstract"
    
        all_text = " ".join([page["text"] for page in pages_text])
        detected_sections = self._detect_all_sections(all_text)
        
        for page_data in pages_text:
            page_text = page_data["text"]
            page_num = page_data["page_num"]
            
            page_section = self._find_section_for_page(page_text, detected_sections, current_section)
            
            if page_section != "Content":
                current_section = page_section
            
            if page_section not in sections:
                sections[page_section] = []
            sections[page_section].append(page_data)
        
        return sections
    
    def _detect_all_sections(self, text: str) -> List[str]:
        sections = []
        
        numbered_pattern = r'\b(\d+\s+[A-Z][a-zA-Z\s]+?)(?=\s+[a-z]|\s+[A-Z][a-z]|\s+[A-Z]{2,}|\s+[0-9]|\s+[^\w\s]|$)'
        numbered_matches = re.findall(numbered_pattern, text)
        for match in numbered_matches:
            if len(match.strip()) > 5 and len(match.strip()) < 100:
                sections.append(match.strip())
        
        subsection_pattern = r'\b(\d+\.\d+\s+[A-Z][a-zA-Z\s]+?)(?=\s+[a-z]|\s+[A-Z][a-z]|\s+[A-Z]{2,}|\s+[0-9]|\s+[^\w\s]|$)'
        subsection_matches = re.findall(subsection_pattern, text)
        for match in subsection_matches:
            if len(match.strip()) > 5 and len(match.strip()) < 100:
                sections.append(match.strip())
        
        sections = list(set(sections))
        sections.sort()
        
        return sections
    
    def _find_section_for_text(self, text: str, detected_sections: List[str]) -> str:
        lines = text.split('\n')
        
        for line in lines[:5]:
            line = line.strip()
            if line in detected_sections:
                return line
        
        for section in detected_sections:
            if section.lower() in text.lower():
                return section
        
        return "Content"
    
    def _find_page_for_chunk(self, chunk_text: str, section_pages: List[Dict[str, str]]) -> int:
        best_page = section_pages[0]["page_num"] if section_pages else 1
        max_overlap = 0
        
        for page_data in section_pages:
            page_text = page_data["text"]
            chunk_words = set(chunk_text.lower().split())
            page_words = set(page_text.lower().split())
            overlap = len(chunk_words.intersection(page_words))
            
            if overlap > max_overlap:
                max_overlap = overlap
                best_page = page_data["page_num"]
        
        return best_page
    
    def _find_section_for_page(self, page_text: str, detected_sections: List[str], current_section: str) -> str:
        for line in page_text.split('\n'):
            line = line.strip()
            if line in detected_sections:
                return line
        
        for section in detected_sections:
            if section.lower() in page_text.lower():
                return section
        
        return current_section
    
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