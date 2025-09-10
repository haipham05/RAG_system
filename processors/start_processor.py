#!/usr/bin/env python3
"""
Data processor startup script.
Sets up Milvus collection and then waits for data processing tasks.
"""

import time
import logging
from setup_milvus import setup_milvus_collection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main processor function"""
    try:
        # Setup Milvus collection
        logger.info("Setting up Milvus collection...")
        setup_milvus_collection()
        logger.info("Milvus collection setup complete!")
        
        # Keep the container running
        logger.info("Data processor is ready. Waiting for data processing tasks...")
        logger.info("You can run data ingestion with: docker-compose exec data_processor python ingest_data.py")
        
        while True:
            time.sleep(60)  # Sleep for 1 minute
            
    except Exception as e:
        logger.error(f"Error in data processor: {e}")
        raise

if __name__ == "__main__":
    main()
