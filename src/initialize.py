
import time
import os
from dotenv import load_dotenv
from pipeline.db_setup import setup_postgres, setup_chromadb
from pipeline.data_processing import DataProcessor

load_dotenv()

def wait_for_services(max_retries: int = 30, retry_delay: int = 2):
    import psycopg2
    import chromadb
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "postgres_db"),
                database=os.getenv("DB_NAME", "ragdb"),
                user=os.getenv("DB_USER", "raguser"),
                password=os.getenv("DB_PASSWORD", "ragpass")
            )
            conn.close()
            break
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise
    
    for attempt in range(max_retries):
        try:
            client = chromadb.HttpClient(
                host=os.getenv("CHROMA_HOST", "chromadb"),
                port=int(os.getenv("CHROMA_PORT", "8000"))
            )
            client.list_collections()
            break
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise
def initialize_rag_system():
    
    try:
        wait_for_services()
        
        setup_postgres()
        setup_chromadb()
        
        processor = DataProcessor()
        
        try:
            processor.initialize_connections()
            
            pdf_directory = "/app/data/pdfs"
            if os.path.exists(pdf_directory):
                processor.process_all_documents(pdf_directory)
            else:
                pdf_directory = "./data/pdfs"
                if os.path.exists(pdf_directory):
                    processor.process_all_documents(pdf_directory)
        
        except Exception:
            pass
        finally:
            processor.close_connections()
    except Exception:
        pass
if __name__ == "__main__":
    initialize_rag_system()
