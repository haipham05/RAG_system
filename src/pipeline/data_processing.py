
import psycopg2
import chromadb
import os
import uuid
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from dotenv import load_dotenv
from .data_ingest import process_all_pdfs

load_dotenv()
class DataProcessor:
    
    def __init__(self):
        self.model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.model = None
        self.pg_conn = None
        self.chroma_client = None
        self.chroma_collection = None
    
    def initialize_connections(self):
        self.model = SentenceTransformer(self.model_name)
        
        self.pg_conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "ragdb"),
            user=os.getenv("DB_USER", "raguser"),
            password=os.getenv("DB_PASSWORD", "ragpass")
        )
        self.pg_conn.autocommit = True
        
        self.chroma_client = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", "8000"))
        )
        self.chroma_collection = self.chroma_client.get_collection("document_chunks")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
    
    def store_document_metadata(self, filename: str, file_path: str, total_chunks: int) -> int:
        cursor = self.pg_conn.cursor()
        
        cursor.execute("""
            INSERT INTO documents (filename, file_path, total_chunks)
            VALUES (%s, %s, %s)
            ON CONFLICT (filename) 
            DO UPDATE SET 
                file_path = EXCLUDED.file_path,
                total_chunks = EXCLUDED.total_chunks,
                processed_at = CURRENT_TIMESTAMP
            RETURNING id
        """, (filename, file_path, total_chunks))
        
        doc_id = cursor.fetchone()[0]
        cursor.close()
        return doc_id
    
    def store_chunk_in_postgres(self, chunk_id: str, filename: str, section_title: str, 
                               chunk_text: str, chunk_index: int):
        cursor = self.pg_conn.cursor()
        
        cursor.execute("""
            INSERT INTO chunks (id, paper_filename, section_title, chunk_text, chunk_index)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) 
            DO UPDATE SET 
                paper_filename = EXCLUDED.paper_filename,
                section_title = EXCLUDED.section_title,
                chunk_text = EXCLUDED.chunk_text,
                chunk_index = EXCLUDED.chunk_index
        """, (chunk_id, filename, section_title, chunk_text, chunk_index))
        
        cursor.close()
    
    def store_chunk_in_chromadb(self, chunk_id: str, embedding: List[float], metadata: Dict):
        self.chroma_collection.upsert(
            ids=[chunk_id],
            embeddings=[embedding],
            metadatas=[metadata]
        )
    
    def clear_existing_data(self, filename: str = None):
        cursor = self.pg_conn.cursor()
        
        if filename:
            cursor.execute("DELETE FROM chunks WHERE paper_filename = %s", (filename,))
            cursor.execute("DELETE FROM documents WHERE filename = %s", (filename,))
            
            try:
                results = self.chroma_collection.get(where={"filename": filename})
                if results['ids']:
                    self.chroma_collection.delete(ids=results['ids'])
            except Exception:
                pass
        else:
            cursor.execute("DELETE FROM chunks")
            cursor.execute("DELETE FROM documents")
            
            try:
                try:
                    self.chroma_client.delete_collection("document_chunks")
                except Exception:
                    pass  # Collection might not exist
                
                self.chroma_collection = self.chroma_client.create_collection(
                    name="document_chunks",
                    metadata={"description": "Document chunks for RAG system"}
                )
            except Exception:
                pass
        
        cursor.close()
    
    def process_document_chunks(self, filename: str, chunks: List[Dict[str, str]], 
                               file_path: str = None):
        if not chunks:
            return
        
        self.store_document_metadata(filename, file_path or filename, len(chunks))
        
        texts = [chunk["text"] for chunk in chunks]
        
        embeddings = self.generate_embeddings(texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = str(uuid.uuid4())
            
            self.store_chunk_in_postgres(
                chunk_id=chunk_id,
                filename=filename,
                section_title=chunk.get("section_title", "Content"),
                chunk_text=chunk["text"],
                chunk_index=chunk["chunk_index"]
            )
            
            metadata = {
                "filename": filename,
                "section_title": chunk.get("section_title", "Content"),
                "chunk_index": chunk["chunk_index"],
                "page_num": chunk.get("page_num", 0)
            }
            
            self.store_chunk_in_chromadb(chunk_id, embedding, metadata)
    
    def process_all_documents(self, pdf_directory: str, clear_existing: bool = True):
        if clear_existing:
            self.clear_existing_data()
        
        all_documents = process_all_pdfs(pdf_directory)
        
        if not all_documents:
            return
        
        for filename, chunks in all_documents.items():
            try:
                file_path = os.path.join(pdf_directory, filename)
                self.process_document_chunks(filename, chunks, file_path)
            except Exception:
                continue
    
    def close_connections(self):
        if self.pg_conn:
            self.pg_conn.close()
def main():
    processor = DataProcessor()
    
    try:
        processor.initialize_connections()
        
        pdf_directory = "/app/data/pdfs"
        if os.path.exists(pdf_directory):
            processor.process_all_documents(pdf_directory)
        
    except Exception:
        pass
    finally:
        processor.close_connections()
if __name__ == "__main__":
    main()
