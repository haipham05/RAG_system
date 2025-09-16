# RAG System

A minimal Retrieval-Augmented Generation (RAG) system with 3 containers:
1. **rag_app**: FastAPI query endpoint
2. **postgres_db**: PostgreSQL for raw text storage  
3. **chromadb**: ChromaDB for vector embeddings

## Quick Start

### 1. Configure Environment

```bash
cp env.example .env
```

Add your Gemini API key to `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 2. Add PDFs

Place PDF files in `data/pdfs/` directory.

### 3. Start System

```bash
docker-compose up --build
```

The system automatically:
- Initializes databases
- Processes PDFs  
- Starts API on port 8080

## Usage

### Query Documents

```bash
curl -X POST "http://localhost:8080/query" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "What is the main contribution?",
       "top_k": 5
     }'
```

### Response Format

```json
{
  "answer": "Based on the context...",
  "sources": [
    {
      "filename": "paper.pdf",
      "title": "Section Title",
      "content": "Relevant text..."
    }
  ]
}
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│   PostgreSQL    │    │    ChromaDB     │
│   (Port 8080)   │    │  Raw Text Store │    │  Vector Store   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Configuration

Environment variables in `.env`:

```env
# Required
GEMINI_API_KEY=your_api_key_here

# Optional (defaults provided)
DB_HOST=postgres_db
DB_USER=raguser
DB_PASSWORD=ragpass
DB_NAME=ragdb
CHROMA_HOST=chromadb
CHROMA_PORT=8000
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## API Reference

**POST /query**
- `question` (string): Your question
- `top_k` (int, optional): Number of chunks to retrieve (default: 5)

## Development

### Reprocess Documents
```bash
docker-compose exec rag_app python src/initialize.py
```

### View Logs
```bash
docker-compose logs -f rag_app
```

## Troubleshooting

1. **No API key**: Set `GEMINI_API_KEY` in `.env`
2. **No documents**: Add PDFs to `data/pdfs/`
3. **Connection errors**: Check containers with `docker-compose ps`
4. **Memory issues**: Reduce `CHUNK_SIZE` in `.env`

## Get Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create new API key
3. Add to `.env` file