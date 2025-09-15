from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from sentence_transformers import SentenceTransformer
from pymilvus import Collection, connections
import psycopg2
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Simple RAG API", version="1.0.0")

# Global variables for connections
pg_conn = None
milvus_collection = None
model = None

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]

@app.on_event("startup")
async def startup_event():
    """Initialize connections and load model on startup"""
    global pg_conn, milvus_collection, model
    
    try:
        # Connect to PostgreSQL
        pg_conn = psycopg2.connect(
            host="postgres",
            database="ragdb",
            user="raguser",
            password="ragpass"
        )
        logger.info("Connected to PostgreSQL")
        
        # Connect to Milvus
        connections.connect("default", host="milvus", port="19530")
        milvus_collection = Collection("chunks")
        milvus_collection.load()
        logger.info("Connected to Milvus")
        
        # Load embedding model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Loaded embedding model")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.get("/")
async def root():
    return {"message": "Simple RAG API is running!"}

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents using RAG"""
    try:
        # Generate embedding for the question
        question_embedding = model.encode([request.question])
        
        # Search in Milvus
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = milvus_collection.search(
            data=question_embedding,
            anns_field="embedding",
            param=search_params,
            limit=request.top_k,
            output_fields=["chunk_id"]
        )
        
        # Get chunk IDs from search results
        chunk_ids = []
        for hit in results[0]:
            chunk_ids.append(hit.entity.get('chunk_id'))
        
        # Retrieve full chunks from PostgreSQL
        sources = []
        with pg_conn.cursor() as cur:
            for chunk_id in chunk_ids:
                cur.execute(
                    "SELECT paper_filename, section_title, chunk_text FROM chunks WHERE id = %s",
                    (chunk_id,)
                )
                result = cur.fetchone()
                if result:
                    sources.append({
                        "filename": result[0],
                        "title": result[1],
                        "content": result[2]
                    })
        
        # Simple answer (in a real system, you'd use an LLM here)
        answer = f"Found {len(sources)} relevant documents for: {request.question}"
        
        return QueryResponse(answer=answer, sources=sources)
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
