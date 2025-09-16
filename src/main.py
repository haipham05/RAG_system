from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import chromadb
import psycopg2
import google.generativeai as genai
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

pg_conn = None
chroma_client = None
chroma_collection = None
model = None
gemini_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pg_conn, chroma_client, chroma_collection, model, gemini_model
    
    pg_conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres_db"),
        database=os.getenv("DB_NAME", "ragdb"),
        user=os.getenv("DB_USER", "raguser"),
        password=os.getenv("DB_PASSWORD", "ragpass")
    )
    
    chroma_client = chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST", "chromadb"),
        port=int(os.getenv("CHROMA_PORT", "8000"))
    )
    
    try:
        chroma_collection = chroma_client.get_collection("document_chunks")
    except Exception:
        chroma_collection = chroma_client.create_collection(
            name="document_chunks",
            metadata={"description": "Document chunks for RAG system"}
        )
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    
    yield

app = FastAPI(title="Simple RAG API", version="1.0.0", lifespan=lifespan)

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    question_embedding = model.encode([request.question])
    results = chroma_collection.query(
        query_embeddings=question_embedding.tolist(),
        n_results=request.top_k
    )
    
    chunk_ids = results['ids'][0] if results['ids'] else []
    sources = []
    context_texts = []
    
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
                context_texts.append(result[2])
    
    if context_texts:
        context = "\n\n".join(context_texts)
        prompt = f"""Based on the following context, please answer the question. If the context doesn't contain enough information to answer the question, say so.

Context:
{context}

Question: {request.question}

Answer:"""
        
        response = gemini_model.generate_content(prompt)
        answer = response.text
    else:
        answer = "I couldn't find any relevant information to answer your question."
    
    return QueryResponse(answer=answer, sources=sources)
