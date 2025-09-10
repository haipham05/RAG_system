#!/usr/bin/env python3
"""
Simple data ingestion script for the RAG system.
This script processes PDFs and stores them in both PostgreSQL and Milvus.
"""

import os
import sys
import logging
import psycopg2
from pymilvus import Collection, connections
from extract_chunk import extract, chunk
from rdb_storer import rdb_storer
from vectordb_storer import vectordb_storer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main ingestion function"""
    
    # Get PDF directory from environment or use default
    pdf_dir = os.getenv('PDF_DIR', '/app/data/pdfs')
    
    if not os.path.exists(pdf_dir):
        logger.error(f"PDF directory {pdf_dir} does not exist")
        sys.exit(1)
    
    # Find all PDF files
    pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_dir}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    try:
        # Connect to PostgreSQL
        pg_conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            database='ragdb',
            user='raguser',
            password='ragpass'
        )
        logger.info("Connected to PostgreSQL")
        
        # Connect to Milvus
        connections.connect("default", host=os.getenv('MILVUS_HOST', 'milvus'), port="19530")
        milvus_collection = Collection("chunks")
        logger.info("Connected to Milvus")
        
        # Process PDFs and store in PostgreSQL
        chunk_ids, chunk_texts = rdb_storer(pg_conn, pdf_files)
        
        if chunk_ids and chunk_texts:
            # Store embeddings in Milvus
            vectordb_storer(milvus_collection, chunk_ids, chunk_texts, 'all-MiniLM-L6-v2')
            logger.info("Data ingestion completed successfully!")
        else:
            logger.error("No chunks were processed")
            
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        sys.exit(1)
    finally:
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == "__main__":
    main()
