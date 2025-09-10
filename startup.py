#!/usr/bin/env python3
"""
Startup script that processes PDFs and starts the RAG API.
This runs automatically when the container starts.
"""

import os
import time
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_services():
    """Wait for PostgreSQL and Milvus to be ready"""
    logger.info("Waiting for services to be ready...")
    
    # Wait for PostgreSQL
    import psycopg2
    for i in range(30):
        try:
            conn = psycopg2.connect(
                host="postgres",
                database="ragdb", 
                user="raguser",
                password="ragpass"
            )
            conn.close()
            logger.info("PostgreSQL is ready!")
            break
        except:
            logger.info(f"Waiting for PostgreSQL... ({i+1}/30)")
            time.sleep(2)
    else:
        logger.error("PostgreSQL not ready after 60 seconds")
        sys.exit(1)
    
    # Wait for Milvus
    from pymilvus import connections
    for i in range(30):
        try:
            connections.connect("default", host="milvus", port="19530")
            logger.info("Milvus is ready!")
            break
        except:
            logger.info(f"Waiting for Milvus... ({i+1}/30)")
            time.sleep(2)
    else:
        logger.error("Milvus not ready after 60 seconds")
        sys.exit(1)

def setup_milvus():
    """Setup Milvus collection"""
    logger.info("Setting up Milvus collection...")
    try:
        from processors.setup_milvus import setup_milvus_collection
        setup_milvus_collection()
        logger.info("Milvus collection setup complete!")
    except Exception as e:
        logger.error(f"Error setting up Milvus: {e}")
        sys.exit(1)

def process_pdfs():
    """Process PDFs in the data folder"""
    pdf_dir = "/app/data/pdfs"
    
    if not os.path.exists(pdf_dir):
        logger.warning(f"PDF directory {pdf_dir} does not exist")
        return
    
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        logger.warning("No PDF files found in data/pdfs/")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    try:
        # Import and run data processing
        from processors.ingest_data import main as ingest_main
        ingest_main()
        logger.info("PDF processing completed successfully!")
    except Exception as e:
        logger.error(f"Error processing PDFs: {e}")
        sys.exit(1)

def start_api():
    """Start the FastAPI server"""
    logger.info("Starting RAG API server...")
    try:
        import uvicorn
        from api.main import app
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(f"Error starting API: {e}")
        sys.exit(1)

def main():
    """Main startup sequence"""
    logger.info("Starting RAG system...")
    
    # Step 1: Wait for services
    wait_for_services()
    
    # Step 2: Setup Milvus
    setup_milvus()
    
    # Step 3: Process PDFs
    process_pdfs()
    
    # Step 4: Start API
    logger.info("RAG system is ready! Starting API server...")
    start_api()

if __name__ == "__main__":
    main()
