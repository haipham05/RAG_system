
import psycopg2
import chromadb
import os
from dotenv import load_dotenv

load_dotenv()

def setup_postgres():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "ragdb"),
            user=os.getenv("DB_USER", "raguser"),
            password=os.getenv("DB_PASSWORD", "ragpass")
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id VARCHAR(255) PRIMARY KEY,
                paper_filename VARCHAR(500) NOT NULL,
                section_title VARCHAR(500),
                chunk_text TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(500) UNIQUE NOT NULL,
                file_path VARCHAR(1000) NOT NULL,
                total_chunks INTEGER NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.close()
        conn.close()
        
    except Exception as e:
        raise
def setup_chromadb():
    try:
        client = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", "8000"))
        )
        
        try:
            collection = client.create_collection(
                name="document_chunks",
                metadata={"description": "Document chunks for RAG system"}
            )
        except Exception as e:
            if "already exists" in str(e).lower() or "UniqueConstraintError" in str(e):
                try:
                    collection = client.get_collection("document_chunks")
                except Exception as get_error:
            else:
                raise e
        
    except Exception as e:
        raise
def main():
    
    try:
        setup_postgres()
        setup_chromadb()
        
    except Exception as e:
        raise
if __name__ == "__main__":
    main()
